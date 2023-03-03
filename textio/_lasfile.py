from .folder._browser import Browser

class LasFile(Browser):

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        self.sections = []

    def add_section(self,key,mnemonic,unit,value,description):

        if key in self.sections:
            raise f"LasFile has the section with the title {key}."

        setattr(self,key,
            header(
                mnemonic=mnemonic,
                unit=unit,
                value=value,
                description=description
                )
            )

        self.sections.append(key)

    def add_ascii(self,*args,**kwargs):

        if "ascii" in self.sections:
            raise f"LasFile has the section with the title 'ascii'."

        self.ascii = frame(*args,**kwargs)

        head,unit,vals,info = [],[],[],[]

        for column in self.ascii.running:
            head.append(column.head)
            unit.append(column.unit)
            vals.append('')
            info.append(column.info)

        self.add_section('curve',head,unit,vals,info)

        self.sections.append("ascii")

    def add_curve(self,**kwargs):

        depth = pop(kwargs,"depth",self.depth)

        curve = LasCurve(depth=depth,**kwargs)

        self[curve.head] = curve

    def __setitem__(self,head,curve):

        if not isinstance(curve,LasCurve):
            raise "curve is not pphys.LasCurve type!"

        if not numpy.all(self.depth==curve.depth):
            raise "Depths does not match!"

        self.ascii._setup(column(
            vals = curve.vals,
            head = head,
            unit = curve.unit,
            info = curve.info,
            size = curve.size,
            dtype = curve.dtype,
            )
        )

        self.curve.extend((head,curve.unit,"",curve.info))

    def __getitem__(self,head):

        return LasCurve(
            vals = self.ascii[head].vals,
            head = self.ascii[head].head,
            unit = self.ascii[head].unit,
            info = self.ascii[head].info,
            depth = self.depth,
            )

    def write(self,filepath):
        """It will write a LasFile to the given filepath."""

        filepath = self.get_abspath(filepath,homeFlag=True)

        fstringH = "{}.{}\t{}: {}"
        fstringA = " ".join(["{}" for _ in range(self.ascii.shape[1])])

        fstringA += "\n"

        vprint = numpy.vectorize(lambda *args: fstringA.format(*args))

        with open(filepath,'w') as outfile:

            for section in self.sections:

                outfile.write(f"#{'='*66}\n")
                outfile.write(f"~{section.capitalize()}\n")

                outfile.write(getattr(self,section).__str__(fstring=fstringH,skip=True))

            outfile.write(f"#{'='*66}\n")
            outfile.write(f"~{'ascii'.capitalize()}\n")

            bodycols = vprint(*self.ascii.running).tolist()

            outfile.write("".join(bodycols))

    def nanplot(self,axis=None,highlight=None,rotation=90):
        """Highlight needs to be added for highlighting certain intervals or maybe zooming.
        Also numbers on the axis needs to be formatted, I do not need to see the prcision more than 1 for depth."""

        show = True if axis is None else False

        if axis is None:
            axis = pyplot.figure().add_subplot()

        yvals = []
        zvals = []

        depth = self.ascii.running[0].vals

        for index,datacolumn in enumerate(self.ascii.running):

            isnan = numpy.isnan(datacolumn.vals)

            L_shift = numpy.ones(datacolumn.size,dtype=bool)
            R_shift = numpy.ones(datacolumn.size,dtype=bool)

            L_shift[:-1] = isnan[1:]
            R_shift[1:] = isnan[:-1]

            lower = numpy.where(numpy.logical_and(~isnan,R_shift))[0]
            upper = numpy.where(numpy.logical_and(~isnan,L_shift))[0]

            zval = numpy.concatenate((lower,upper),dtype=int).reshape((2,-1)).T.flatten()

            yval = numpy.full(zval.size,index,dtype=float)
            
            yval[::2] = numpy.nan

            yvals.append(yval)
            zvals.append(zval)

        qvals = numpy.unique(numpy.concatenate(zvals))

        for (yval,zval) in zip(yvals,zvals):
            axis.step(numpy.where(qvals==zval.reshape((-1,1)))[1],yval)

        axis.set_xlim((-1,qvals.size))
        axis.set_ylim((-1,self.ascii.shape[1]))

        axis.set_xticks(numpy.arange(qvals.size))
        axis.set_xticklabels(depth[qvals],rotation=rotation)

        axis.set_yticks(numpy.arange(self.ascii.shape[1]))
        axis.set_yticklabels(self.ascii.heads)

        axis.grid(True,which="both",axis='x')

        if show:
            pyplot.show()

    def trim(self,*args,strt=None,stop=None,curve=None):
        """It trims the data based on the strt and stop depth."""

        if len(args)==0:
            pass
        elif len(args)==1:
            strt, = args
        elif len(args)==2:
            strt,stop = args
        elif len(args)==3:
            strt,stop,curve = args
        else:
            raise("Too many arguments!")

        self.well['STRT'].value
        self.well['STOP'].value

        if strt is None and stop is None:
            return
        elif strt is None and stop is not None:
            conds = self.depth<=stop
        elif strt is not None and stop is None:
            conds = self.depth>=strt
        else:
            conds = numpy.logical_and(self.depth>=strt,self.depth<=stop)

        if curve is not None:
            return self[curve][conds]

        self.ascii = self.ascii[conds]

        self.well.fields[2][self.well.mnemonic.index('STRT')] = str(self.depth[0].vals[0])
        self.well.fields[2][self.well.mnemonic.index('STOP')] = str(self.depth[-1].vals[0])

    def resample(self,depth):
        """Resamples the frame data based on given depth:

        depth :   The depth values where new curve data will be calculated;
        """

        depth_current = self.ascii.running[0].vals

        if not LasFile.isvalid(depth):
            raise ValueError("There are none values in depth.")

        if not LasFile.issorted(depth):
            depth = numpy.sort(depth)

        outers_above = depth<depth_current.min()
        outers_below = depth>depth_current.max()

        inners = numpy.logical_and(~outers_above,~outers_below)

        depth_inners = depth[inners]

        lowers = numpy.empty(depth_inners.shape,dtype=int)
        uppers = numpy.empty(depth_inners.shape,dtype=int)

        lower,upper = 0,0

        for index,depth in enumerate(depth_inners):

            while depth>depth_current[lower]:
                lower += 1

            while depth>depth_current[upper]:
                upper += 1

            lowers[index] = lower-1
            uppers[index] = upper

        delta_depth = depth_inners-depth_current[lowers]

        delta_depth_current = depth_current[uppers]-depth_current[lowers]

        grads = delta_depth/delta_depth_current

        for index,_column in enumerate(self.ascii.running):

            if index==0:
                self.ascii.running[index].vals = depth
                continue

            delta_values = _column.vals[uppers]-_column.vals[lowers]

            self.ascii.running[index].vals = numpy.empty(depth.shape,dtype=float)

            self.ascii.running[index].vals[outers_above] = numpy.nan
            self.ascii.running[index].vals[inners] = _column.vals[lowers]+grads*(delta_values)
            self.ascii.running[index].vals[outers_below] = numpy.nan

    @staticmethod
    def resample_curve(depth,curve):
        """Resamples the curve.vals based on given depth, and returns curve:

        depth       :   The depth where new curve values will be calculated;
        curve       :   The curve object to be resampled

        """

        if not LasFile.isvalid(depth):
            raise ValueError("There are none values in depth.")

        if not LasFile.issorted(depth):
            depth = numpy.sort(depth)

        outers_above = depth<curve.depth.min()
        outers_below = depth>curve.depth.max()

        inners = numpy.logical_and(~outers_above,~outers_below)

        depth_inners = depth[inners]

        lowers = numpy.empty(depth_inners.shape,dtype=int)
        uppers = numpy.empty(depth_inners.shape,dtype=int)

        lower,upper = 0,0

        for index,depth in enumerate(depth_inners):

            while depth>curve.depth[lower]:
                lower += 1

            while depth>curve.depth[upper]:
                upper += 1

            lowers[index] = lower-1
            uppers[index] = upper

        delta_depth = depth_inners-curve.depth[lowers]

        delta_depth_current = curve.depth[uppers]-curve.depth[lowers]

        delta_values_current = curve.vals[uppers]-curve.vals[lowers]

        grads = delta_depth/delta_depth_current

        values = numpy.empty(depth.shape,dtype=float)

        values[outers_above] = numpy.nan
        values[inners] = curve.vals[lowers]+grads*(delta_values_current)
        values[outers_below] = numpy.nan

        curve.depth = depth

        curve.vals = values

        return curve

    @property
    def height(self):

        top = self.depth.min()
        bottom = self.depth.max()

        total = bottom-top

        return {
            'total' :   total,
            'top'   :   top,
            'bottom':   bottom,
            'limit' :   (bottom,top)}

    @property
    def depth(self):

        return self.ascii.running[0]

    @property
    def isdepthvalid(self):
        
        return LasFile.isvalid(self.depth.vals)

    @staticmethod
    def isvalid(vals):

        return numpy.all(~numpy.isnan(vals))

    @property
    def isdepthpositive(self):

        return LasFile.ispositive(self.depth.vals)

    @staticmethod
    def ispositive(vals):

        return numpy.all(vals>=0)

    @property
    def isdepthsorted(self):

        return LasFile.issorted(self.depth.vals)

    @staticmethod
    def issorted(vals):

        return numpy.all(vals[:-1]<vals[1:])

def loadlas(*args,**kwargs):
    """
    Returns an instance of pphys.LasFile. If a filepath is specified, the instance
    represents the file.
    
    Arguments:
        filepath {str} -- path to the given LAS file

    Keyword Arguments:
        homedir {str} -- path to the home (output) directory
        filedir {str} -- path to the file (input) directory
    
    Returns:
        pphys.LasFile -- an instance of pphys.LasFile filled with LAS file text.

    """

    if len(args)==1:
        filepath = args[0]
    elif len(args)>1:
        raise "The function does not take more than one positional argument."

    # It creates an empty pphys.LasFile instance.
    nullfile = LasFile(filepath=filepath,**kwargs)

    # It reads LAS file and returns pphys.LasFile instance.
    fullfile = LasWorm(nullfile).lasfile

    return fullfile

class LasWorm():
    """Reads a las file with all sections."""

    def __init__(self,lasfile):

        self.lasfile = lasfile

        with open(self.lasfile.filepath,"r",encoding="latin1") as lasmaster:
            dataframe = self.text(lasmaster)

        self.lasfile.ascii = dataframe

    def seeksection(self,lasmaster,section=None):

        lasmaster.seek(0)

        self._seeksection(lasmaster,section)

    def _seeksection(self,lasmaster,section=None):

        if section is None:
            section = "~"

        while True:

            line = next(lasmaster).strip()

            if line.startswith(section):
                break

    def version(self,lasmaster):
        """It returns the version of file."""

        pattern = r"\s*VERS\s*\.\s+([^:]*)\s*:"

        program = re.compile(pattern)

        lasmaster.seek(0)

        self._seeksection(lasmaster,section="~V")

        while True:

            line = next(lasmaster).strip()

            if line.startswith("~"):
                break
            
            version = program.match(line)

            if version is not None:
                break

        return version.groups()[0].strip()

    def program(self,version="2.0"):
        """It returns the program that compiles the regular expression to retrieve parameter data."""

        """
        Mnemonic:

        LAS Version 2.0
        This mnemonic can be of any length but must not contain any internal spaces, dots, or colons.

        LAS Version 3.0
        Any length >0, but must not contain periods, colons, embedded spaces, tabs, {}, [], |
        (bar) characters, leading or trailing spaces are ignored. It ends at (but does not include)
        the first period encountered on the line.
        
        """

        if version in ["1.2","1.20"]:
            mnemonic = r"[^:\.\s]+"
        elif version in ["2.0","2.00"]:
            mnemonic = r"[^:\.\s]+"
        elif version in ["3.0","3.00"]:
            mnemonic = r"[^:\.\s\{\}\|\[\]]+"

        """
        Unit:
        
        LAS Version 2.0
        The units if used, must be located directly after the dot. There must be not spaces
        between the units and the dot. The units can be of any length but must not contain any
        colons or internal spaces.

        LAS Version 3.0
        Any length, but must not contain colons, embedded spaces, tabs, {} or | characters. If present,
        it must begin at the next character after the first period on the line. The Unitends at
        (but does not include) the first space or first colon after the first period on the line.
        
        """

        if version in ["1.2","1.20"]:
            unit = r"[^:\s]*"
        elif version in ["2.0","2.00"]:
            unit = r"[^:\s]*"
        elif version in ["3.0","3.00"]:
            unit = r"[^:\s\{\}\|]*"

        """
        Value:
        
        LAS Version 2.0
        This value can be of any length and can contain spaces or dots as appropriate, but must not contain any colons.
        It must be preceded by at least one space to demarcate it from the units and must be to the left of the colon.

        LAS Version 3.0
        Any length, but must not contain colons, {} or | characters. If the Unit field is present,
        at least one space must exist between the unit and the first character of the Value field.
        The Value field ends at (but does not include) the last colon on the line.
        
        """

        if version in ["1.2","1.20"]:
            value = r"[^:]*"
        elif version in ["2.0","2.00"]:
            value = r"[^:]*"
        elif version in ["3.0","3.00"]:
            value = r"[^:\{\}\|]*"
        
        """
        Description:

        LAS Version 2.0
        It is always located to the right of the colon. Its length is limited by the total
        line length limit of 256 characters which includes a carriage return and a line feed.
        
        LAS Version 3.0
        Any length, Begins as the first character after the last colon on the line, and ends at the
        last { (left brace), or the last | (bar), or the end of the line, whichever is encountered
        first.

        """

        description = r".*"

        pattern = f"\\s*({mnemonic})\\s*\\.({unit})\\s+({value})\\s*:\\s*({description})"

        program = re.compile(pattern)

        return program

    def headers(self,lasmaster):

        version = self.version(lasmaster)
        program = self.program(version)

        lasmaster.seek(0)

        while True:

            line = next(lasmaster).strip()

            if line.startswith("~A"):
                types = self._types(lasmaster)
                break

            if line.startswith("~O"):
                continue

            if line.startswith("~"):

                sectioncode = line[:2]
                sectionhead = line[1:].split()[0].lower()
                sectionbody = self._header(lasmaster,program)

                self.lasfile.sections.append(sectionhead)

                setattr(self.lasfile,sectionhead,sectionbody)

                lasmaster.seek(0)

                self._seeksection(lasmaster,section=sectioncode)

        return types

    def _header(self,lasmaster,program):

        mnemonic,unit,value,description = [],[],[],[]

        mnemonic_parantheses_pattern = r'\([^)]*\)\s*\.'

        while True:

            line = next(lasmaster).strip()

            if len(line)<1:
                continue
            
            if line.startswith("#"):
                continue

            if line.startswith("~"):
                break

            line = re.sub(r'[^\x00-\x7F]+','',line)

            mpp = re.search(mnemonic_parantheses_pattern,line)

            if mpp is not None:
                line = re.sub(mnemonic_parantheses_pattern,' .',line) # removing the content in between paranthesis for mnemonics

            mnemonic_,unit_,value_,description_ = program.match(line).groups()

            if mpp is not None:
                mnemonic_ = f"{mnemonic_} {mpp.group()[:-1]}"

            mnemonic.append(mnemonic_.strip())

            unit.append(unit_.strip())

            value.append(value_.strip())

            description.append(description_.strip())

        return header(
            mnemonic = mnemonic,
            unit = unit,
            value = value,
            description = description,)

    def types(self,lasmaster):

        lasmaster.seek(0)

        return self._types(lasmaster)

    def _types(self,lasmaster):

        while True:

            line = next(lasmaster).strip()

            if len(line)<1:
                continue
            
            if line.startswith("#"):
                continue

            break

        row = re.sub(r"\s+"," ",line).split(" ")

        return strtype(row)

    def text(self,lasmaster):

        types = self.headers(lasmaster)

        value_null = float(self.lasfile.well['NULL'].value)

        dtypes = [numpy.dtype(type_) for type_ in types]

        floatFlags = [True if type_ is float else False for type_ in types]

        lasmaster.seek(0)

        self._seeksection(lasmaster,section="~A")

        if all(floatFlags):
            cols = numpy.loadtxt(lasmaster,comments="#",unpack=True,encoding="latin1")
        else:
            cols = numpy.loadtxt(lasmaster,comments="#",unpack=True,encoding="latin1",dtype='str')

        iterator = zip(cols,self.lasfile.curve.mnemonic,self.lasfile.curve.unit,self.lasfile.curve.description,dtypes)

        running = []

        for vals,head,unit,info,dtype in iterator:

            if dtype.type is numpy.dtype('float').type:
                vals[vals==value_null] = numpy.nan

            datacolumn = column(vals,head=head,unit=unit,info=info,dtype=dtype)

            running.append(datacolumn)

        dataframe = frame(*running)

        if not LasFile.isvalid(dataframe.running[0].vals):
            raise Warning("There are none depth values.")

        if not LasFile.ispositive(dataframe.running[0].vals):
            raise Warning("There are negative depth values.")

        if not LasFile.issorted(dataframe.running[0].vals):
            dataframe = dataframe.sort((dataframe.running[0].head,))

        return dataframe