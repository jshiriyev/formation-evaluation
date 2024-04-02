class LasFile():

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