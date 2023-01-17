import copy

import json

import os

import re

from matplotlib import colors as mcolors
from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import transforms

from matplotlib.backend_bases import MouseButton

from matplotlib.backends.backend_pdf import PdfPages

from matplotlib.patches import Rectangle

from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import LogFormatter
from matplotlib.ticker import LogFormatterExponent
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.ticker import LogLocator
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import NullLocator
from matplotlib.ticker import ScalarFormatter

import numpy

if __name__ == "__main__":
    import dirsetup

from datum import column
from datum import frame

from textio import dirmaster
from textio import header

from cypy.vectorpy import strtype

filedir = os.path.dirname(__file__)

filepath = os.path.join(filedir,"pphys.json")

with open(filepath,"r") as jsonfile:
    library = json.load(jsonfile)

def pop(kwargs,key,default=None):

    try:
        return kwargs.pop(key)
    except KeyError:
        return default

class LasCurve(column):
    """The major difference between Column and LasCurve is the depth attribute
    of LasCurve."""

    def __init__(self,**kwargs):
        """Initialization of LasCurve."""

        super().__init__(
            vals = pop(kwargs,"vals"),
            head = pop(kwargs,"head"),
            unit = pop(kwargs,"unit"),
            info = pop(kwargs,"info"),
            size = pop(kwargs,"size"),
            dtype = pop(kwargs,"dtype"))

        depth = kwargs.pop("depth")

        if not isinstance(depth,column):
            depth = column(
                vals = depth,
                head = "DEPT",
                unit = pop(kwargs,"dunit","m"),
                info = "")

        self.depth = depth

        if self.depth.size != self.vals.size:
            raise f"depth.size and vals.size does not match!"

        self.setattrs(**kwargs)

    def setattrs(self,**kwargs):

        for key,value in kwargs.items():
            setattr(self,key,value)

    @property
    def height(self):

        depth = self.depth

        total = depth.max()-depth.min()

        node_head = numpy.roll(depth,1)
        node_foot = numpy.roll(depth,-1)

        thickness = (node_foot-node_head)/2

        thickness[ 0] = (depth[ 1].vals[0]-depth[ 0].vals[0])/2
        thickness[-1] = (depth[-1].vals[0]-depth[-2].vals[0])/2

        null = numpy.sum(thickness[self.isnone])

        return {'total': total, 'null': null, 'valid': total-null,}
    
class LasFile(dirmaster):

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

class LasBatch(dirmaster):

    def __init__(self,filepaths=None,**kwargs):

        super().__init__(
            homedir = pop(kwargs,"homedir"),
            filedir = pop(kwargs,"filedir"))

        self.files = []

        self.loadall(filepaths,**kwargs)

    def loadall(self,filepaths,**kwargs):

        if filepaths is None:
            return

        if isinstance(filepaths,list):
            filepaths = tuple(filepaths)

        if not isinstance(filepaths,tuple):
            filepaths = (filepaths,)

        for filepath in filepaths:
            self.load(filepath,**kwargs)

    def load(self,filepath,**kwargs):

        if filepath is None:
            return

        lasfile = loadlas(filepath,**kwargs)

        self.files.append(lasfile)

        print(f"Loaded {lasfile.filepath}")

        # logging.info(f"Loaded {lasfile.filepath}")

    def __getitem__(self,index):

        return self.files[index]

    def wells(self,idframes=None):

        if idframes is None:
            idframes = range(len(self.files))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            dataframe = self.files[index]

            print("\n\tWELL #{}".format(dataframe.well.get_row(mnemonic="WELL")["value"]))

            # iterator = zip(dataframe.well["mnemonic"],dataframe.well["units"],dataframe.well["value"],dataframe.well.descriptions)

            iterator = zip(*dataframe.well.get_columns())

            for mnem,unit,value,descr in iterator:
                print(f"{descr} ({mnem}):\t\t{value} [{unit}]")

    def curves(self,idframes=None,mnemonic_space=33,tab_space=8):

        if idframes is None:
            idframes = range(len(self.files))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            dataframe = self.files[index]

            iterator = zip(dataframe.headers,dataframe.units,dataframe.details,dataframe.running)

            # file.write("\n\tLOG NUMBER {}\n".format(idframes))
            print("\n\tLOG NUMBER {}".format(index))

            for header,unit,detail,datacolumn in iterator:

                if numpy.all(numpy.isnan(datacolumn)):
                    minXval = numpy.nan
                    maxXval = numpy.nan
                else:
                    minXval = numpy.nanmin(datacolumn)
                    maxXval = numpy.nanmax(datacolumn)

                tab_num = int(numpy.ceil((mnemonic_space-len(header))/tab_space))
                tab_spc = "\t"*tab_num if tab_num>0 else "\t"

                # file.write("Curve: {}{}Units: {}\tMin: {}\tMax: {}\tDescription: {}\n".format(
                #     curve.mnemonic,tab_spc,curve.unit,minXval,maxXval,curve.descr))
                print("Curve: {}{}Units: {}\tMin: {}\tMax: {}\tDescription: {}".format(
                    header,tab_spc,unit,minXval,maxXval,detail))

    def merge(self,fileIDs,curveNames):

        if isinstance(fileIDs,int):

            try:
                depth = self.files[fileIDs]["MD"]
            except KeyError:
                depth = self.files[fileIDs]["DEPT"]

            xvals1 = self.files[fileIDs][curveNames[0]]

            for curveName in curveNames[1:]:

                xvals2 = self.files[fileIDs][curveName]

                xvals1[numpy.isnan(xvals1)] = xvals2[numpy.isnan(xvals1)]

            return depth,xvals1

        elif numpy.unique(numpy.array(fileIDs)).size==len(fileIDs):

            if isinstance(curveNames,str):
                curveNames = (curveNames,)*len(fileIDs)

            depth = numpy.array([])
            xvals = numpy.array([])

            for (fileID,curveName) in zip(fileIDs,curveNames):

                try:
                    depth_loc = self.files[fileID]["MD"]
                except KeyError:
                    depth_loc = self.files[fileID]["DEPT"]

                xvals_loc = self.files[fileID][curveName]

                depth_loc = depth_loc[~numpy.isnan(xvals_loc)]
                xvals_loc = xvals_loc[~numpy.isnan(xvals_loc)]

                depth_max = 0 if depth.size==0 else depth.max()

                depth = numpy.append(depth,depth_loc[depth_loc>depth_max])
                xvals = numpy.append(xvals,xvals_loc[depth_loc>depth_max])

            return depth,xvals

class BulkModel(header):

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        object.__setattr__(self,"library",library)

    def set_colors(self,**kwargs):

        for key,value in kwargs.items():

            try:
                mcolors.to_rgba(value)
            except ValueError:
                raise ValueError(f"Invalid RGBA argument: '{value}'")

            getattr(self,key)[1] = value

    def view(self):

        pass

    def viewlib(self,axis,nrows=(7,7,8),ncols=3,fontsize=10,sizes=(8,5),dpi=100):

        X,Y = [dpi*size for size in sizes]

        w = X/ncols
        h = Y/(max(nrows)+1)

        names = self.names

        colors = self.colors

        hatches = self.hatches

        k = 0
            
        for idcol in range(ncols):

            for idrow in range(nrows[idcol]):

                y = Y-(idrow*h)-h

                xmin = w*(idcol+0.05)
                xmax = w*(idcol+0.25)

                ymin = y-h*0.3
                ymax = y+h*0.3

                xtext = w*(idcol+0.3)

                axis.text(xtext,y,names[k],fontsize=(fontsize),
                        horizontalalignment='left',
                        verticalalignment='center')

                axis.add_patch(
                    Rectangle((xmin,ymin),xmax-xmin,ymax-ymin,
                    fill=True,hatch=hatches[k],facecolor=colors[k]))

                k += 1

        axis.set_xlim(0,X)
        axis.set_ylim(0,Y)

        axis.set_axis_off()

        return axis

class DepthView(dirmaster):

    def __init__(self,lasfile,**kwargs):

        super().__init__(homedir=pop(kwargs,"homedir"))

        self.depths = {}
        self.axes = {}

        self.curves = {}
        self.modules = []
        self.perfs = []
        self.casings = []

        if lasfile is None:
            self.lasfile = LasFile(**kwargs)
        if isinstance(lasfile,str):
            self.lasfile = loadlas(lasfile,**kwargs)
        elif isinstance(lasfile,LasFile):
            self.lasfile = lasfile

        self.set_depths()

    def set_depths(self,base=10,subs=1,subskip=None,subskip_top=0,subskip_bottom=0):
        """It sets the depth interval for which log data will be shown.
        
        top             : top of interval
        bottom          : bottom of interval
        base            : major grid intervals on the plot
        subs            : minor grid intervals on the plot
        subskip         : number of minors to skip at the top and bottom
        subskip_top     : number of minors to skip at the top
        subskip_bottom  : number of minors to skip at the bottom

        """

        top = self.lasfile.depth.min()
        bottom = self.lasfile.depth.max()

        top = numpy.floor(top/base)*base
        bottom = top+numpy.ceil((bottom-top)/base)*base

        if subskip is not None:
            subskip_bottom,subskip_top = subskip,subskip

        top += subs*subskip_top
        bottom += subs*subskip_bottom

        self.depths['top'] = top
        self.depths['bottom'] = bottom
        self.depths['height'] = bottom-top
        self.depths['limit'] = (bottom,top)
        self.depths['base'] = base
        self.depths['subs'] = subs

        self.depths['ticks'] = MultipleLocator(base).tick_values(top,bottom)

    def set_curve(self,col,curve,row=None,vmin=None,vmax=None,multp=None,**kwargs):
        """It adds LasCurve[head] to the axes[col]."""

        kwargs['color'] = pop(kwargs,"color","black")
        kwargs['style'] = pop(kwargs,"style","solid")
        kwargs['width'] = pop(kwargs,"width",0.75)

        if isinstance(curve,str):
            curve = self.lasfile[curve]
            curve.setattrs(**kwargs)
        elif not isinstance(curve,LasCurve):
            curve = LasCurve(vals=curve,**kwargs)
        else:
            curve.setattrs(**kwargs)
        
        curve.col = col
        curve.row = row

        if vmin is None:
            vmin = curve.min()
        
        if vmax is None:
            vmax = curve.max()

        curve.vmin = vmin
        curve.vmax = vmax

        curve.limit = (vmin,vmax)

        curve.multp = multp

        self.curves[curve.head] = curve

    def set_axes(self,ncols=None,nrows=None,depthloc=None,labelloc="top",depth=6,label=6,width=15,height=70):
        """It sets grid number for different elements in the axes.

        ncols       : number of column axis including depth axis in the figure, integer
        nrows       : number of curves in the axes, integer, nrows*label defines
                      grid number in the height of labels

        depthloc    : location of depth axis, integer
        labelloc    : location of label axis, top, bottom or None

        depth       : grid number in the width of depth xaxis, integer
        label       : grid number in the height of individual label, integer
        width       : grid number in the width of curve individual xaxis, integer
        height      : grid number in the height of curve yaxis, integer

        """

        if ncols is None:
            ncols = self.columns+1

        if nrows is None:
            nrows = self.rows

        self.axes['ncols'] = ncols
        self.axes['nrows'] = nrows

        if depthloc is None:
            depthloc = 0 if ncols<3 else 1

        self.axes['depthloc'] = depthloc
        self.axes['labelloc'] = str(labelloc).lower()

        self.axes['depth'] = depth
        self.axes['label'] = label
        self.axes['width'] = width
        self.axes['height'] = height

        self.axes['size'] = (depth+ncols*width,nrows*label+height)

        if self.axes['labelloc'] == "none":
            self.axes['naxes_percolumn'] = 1
            self.axes['label_indices'] = slice(0)
            self.axes['curve_indices'] = slice(ncols)
        elif self.axes['labelloc'] == "top":
            self.axes['naxes_percolumn'] = 2
            self.axes['label_indices'] = slice(0,ncols*2,2)
            self.axes['curve_indices'] = slice(1,ncols*2,2)
        elif self.axes['labelloc'] == "bottom":
            self.axes['naxes_percolumn'] = 2
            self.axes['label_indices'] = slice(0,ncols*2,2)
            self.axes['curve_indices'] = slice(1,ncols*2,2)
        else:
            raise ValueError(f"{labelloc} has not been defined! options: {{top,bottom}}")

        width_ratio = [width]*self.axes["ncols"]
        width_ratio[depthloc] = depth

        self.axes["width_ratio"] = tuple(width_ratio)

        if self.axes['labelloc'] == 'none':
            height_ratio = [height]
        elif self.axes['labelloc'] == 'top':
            height_ratio = [nrows*label,height]
        elif self.axes['labelloc'] == 'bottom':
            height_ratio = [height,nrows*label]

        self.axes["height_ratio"] = tuple(height_ratio)

        self.axes['xaxis'] = [{} for _ in range(ncols)]

        for index in range(self.axes['ncols']):
            self.set_xaxis(index)

    def set_xaxis(self,col,cycles=2,scale='linear',subs=None,subskip=None,subskip_left=0,subskip_right=0):

        if len(self.axes)==0:
            self.set_axes()

        if subskip is not None:
            subskip_left,subskip_right = subskip,subskip

        if col==self.axes['depthloc']:
            subs = 1
            limit = (0,10)
        elif scale=="linear":
            subs = 1 if subs is None else subs
            limit = (0+subskip_left,cycles*10+subskip_right)
        elif scale=="log":
            subs = range(1,10) if subs is None else subs
            limit = ((1+subskip_left)*10**0,(1+subskip_right)*10**cycles)
        else:
            raise ValueError(f"{scale} has not been defined! options: {{linear,log}}")

        self.axes['xaxis'][col]['subs'] = subs
        self.axes['xaxis'][col]['limit'] = limit
        self.axes['xaxis'][col]['scale'] = scale

    def __getitem__(self,head):

        return self.curves[head]

    def set_module(self,col,module,left=0,right=None,**kwargs):
        """It adds petrophysical module to the defined curve axis."""

        _module = {}

        _module['col'] = col
        _module['module'] = module
        _module['left'] = left
        _module['right'] = right

        for key,value in kwargs.items():
            _module[key] = value

        self.modules.append(_module)

    def set_perf(self,depth,col=None,**kwargs):
        """It adds perforation depth to the depth axis."""

        _perf = {}

        if len(self.axes)==0:
            self.set_axes()

        if col is None:
            col = self.axes['depthloc']

        _perf['col'] = col

        _perf['depth'] = depth

        for key,value in kwargs.items():
            _perf[key] = value

        self.perfs.append(_perf)

    def set_casing(self,depth,col=None,**kwargs):
        """It adds casing depth to the depth axis."""

        _casing = {}

        if len(self.axes)==0:
            self.set_axes()

        if col is None:
            col = self.axes['depthloc']

        _casing['col'] = col

        _casing['depth'] = depth

        for key,value in kwargs.items():
            _casing[key] = value

        self.casings.append(_casing)

    def view(self,top,wspace=0.0,hspace=0.0,height=30,**kwargs):

        if len(self.axes)==0:
            self.set_axes()

        if kwargs.get("figsize") is None:
            kwargs["figsize"] = (self.columns*2.0,6.0)

        self.add_figure(**kwargs)

        self.add_axes()
        self.add_curves()
        self.add_modules()
        self.add_perfs()
        self.add_casings()

        self.gspecs.tight_layout(self.figure)

        self.gspecs.update(wspace=wspace,hspace=hspace)

        for index,axis in enumerate(self.figure.axes):
            if self.axes['labelloc'] == "none":
                axis.set_ylim(top+height,top)
            elif index%2==1:
                axis.set_ylim(top+height,top)

        pyplot.show()

    def set_page(self,**kwargs):
        """It sets the format of page for printing."""

        depths = pop(kwargs,"depths")

        self.page = {}

        self.page['fmt'] = pop(kwargs,"fmt","A4").lower()

        self.page['orientation'] = pop(kwargs,"orientation","portrait").lower()

        size = self.get_pagesize(self.page['orientation'])

        self.page['width'] = size['width']

        self.page['height'] = size['height']

        self.page['size'] = (size['width'],size['height'])

        self.page['dpi'] = pop(kwargs,"dpi",100)

        grids = self.get_pagegrid(self.page['orientation'])

        self.set_axes(label=4,**grids)

        if depths is not None:
            top,bottom = abs(min(depths)),abs(max(depths))
            depths = (bottom,top)
            top,bottom = min(depths),max(depths)
            height_total = bottom-top
        else:
            height_total = self.depths['height']
            top,bottom = self.depths['top'],self.depths['bottom']

        height_pages = self.axes['curve_indices']

        self.page['depth'].number = -(-height_total//height_pages)

        self.page['depth'].limits = []

        while top<bottom:
            self.page['depth'].limits.append(top,top+height_pages)
            top += height_pages

    def save(self,filepath,wspace=0.0,hspace=0.0,**kwargs):
        """It saves the DepthView as a multipage pdf file."""

        if len(self.axes)==0:
            self.set_axes()

        if not hasattr(self,"page"):
            self.set_page(**kwargs)

        filepath = self.get_extended(path=filepath,extension='.pdf')

        filepath = self.get_abspath(path=filepath,homeFlag=True)

        self.add_figure(**kwargs)

        self.add_axes()
        self.add_curves()
        self.add_modules()
        self.add_perfs()
        self.add_casings()

        self.gspecs.tight_layout(self.figure)

        self.gspecs.update(wspace=wspace,hspace=hspace)

        with PdfPages(filepath) as pdf:

            for limit in self.page['depth'].limits:

                for index,axis in enumerate(self.figure.axes):
                    if self.axes['labelloc'] == "none":
                        axis.set_ylim(limit)
                    elif index%2==1:
                        axis.set_ylim(limit)

                pdf.savefig()

    def add_figure(self,**kwargs):

        self.figure = pyplot.figure(**kwargs)

        self.gspecs = gridspec.GridSpec(
            nrows = self.axes['naxes_percolumn'],
            ncols = self.axes['ncols'],
            figure = self.figure,
            width_ratios = self.axes['width_ratio'],
            height_ratios = self.axes['height_ratio'])

    def add_axes(self):

        for index in range(self.axes['ncols']):

            xaxis = self.axes['xaxis'][index]

            yaxis = self.depths

            if self.axes['labelloc'] == "none":
                curve_axis = self.figure.add_subplot(self.gspecs[index])
            elif self.axes['labelloc'] == "top":
                label_axis = self.figure.add_subplot(self.gspecs[0,index])
                curve_axis = self.figure.add_subplot(self.gspecs[1,index])
            elif self.axes['labelloc'] == "bottom":
                label_axis = self.figure.add_subplot(self.gspecs[1,index])
                curve_axis = self.figure.add_subplot(self.gspecs[0,index])

            if self.axes['labelloc'] != "none":
                xlim,ylim = (0,1),(0,self.axes['nrows'])
                self.set_axislabel(label_axis,xlim,ylim)

            if index != self.axes['depthloc']:
                self.set_yaxiscurve(curve_axis,yaxis)
                self.set_xaxiscurve(curve_axis,xaxis)
            else:
                self.set_axisdepth(curve_axis,xaxis,yaxis)

    def add_curves(self):

        label_axes = self.figure.axes[self.axes['label_indices']]
        curve_axes = self.figure.axes[self.axes['curve_indices']]

        for _,curve in self.curves.items():

            label_axis = label_axes[curve.col]
            curve_axis = curve_axes[curve.col]

            xaxis = self.axes['xaxis'][curve.col]

            getattr(self,f"set_{xaxis['scale'][:3]}xaxis")(curve,xaxis)

            curve_axis.plot(curve.xaxis,curve.depth,
                color = curve.color,
                linestyle = curve.style,
                linewidth = curve.width,)

            row = len(curve_axis.lines)

            if curve.row is None:
                curve.row = row

            self.set_labelcurve(label_axis,curve)

    def add_modules(self):

        label_axes = self.figure.axes[self.axes['label_indices']]
        curve_axes = self.figure.axes[self.axes['curve_indices']]

        for module in self.modules:

            label_axis = label_axes[module['col']]
            curve_axis = curve_axes[module['col']]

            xlim = curve_axis.get_xlim()

            lines = curve_axis.lines

            xvals = lines[module['left']].get_xdata()
            yvals = lines[module['left']].get_ydata()

            if module['right'] is None:
                x2 = 0
            elif module['right']>=len(lines):
                x2 = max(xlim)
            else:
                x2 = lines[module['right']].get_xdata()

            curve_axis.fill_betweenx(yvals,xvals,x2=x2,facecolor=module['module']['fillcolor'],hatch=module['module']["hatch"])

            module['row'] = len(lines)

            self.set_labelmodule(label_axis,module)

    def add_perfs(self):
        """It includes perforated depth."""

        curve_axes = self.figure.axes[self.axes['curve_indices']]

        for perf in self.perfs:

            curve_axis = curve_axes[perf['col']]

            depth = numpy.array(perf['depth'],dtype=float)

            yvals = numpy.arange(depth.min(),depth.max()+0.5,1.0)

            xvals = numpy.zeros(yvals.shape)

            curve_axis.plot(xvals[0],yvals[0],
                marker=11,
                color='orange',
                markersize=10,
                markerfacecolor='black')

            curve_axis.plot(xvals[-1],yvals[-1],
                marker=10,
                color='orange',
                markersize=10,
                markerfacecolor='black')

            curve_axis.plot(xvals[1:-1],yvals[1:-1],
                marker=9,
                color='orange',
                markersize=10,
                markerfacecolor='black')

    def add_casings(self):
        """It includes casing set depth."""

        pass

    @staticmethod
    def set_linxaxis(curve,xaxis):

        amin,amax = xaxis["limit"]

        vmin,vmax = curve.limit

        # print(f"{amin=},",f"{amax=}")
        # print(f"given_{vmin=},",f"given_{vmax=}")

        delta_axis = numpy.abs(amax-amin)
        delta_vals = numpy.abs(vmax-vmin)

        # print(f"{delta_vals=}")

        delta_powr = -numpy.floor(numpy.log10(delta_vals))

        # print(f"{delta_powr=}")

        vmin = numpy.floor(vmin*10**delta_powr)/10**delta_powr

        vmax_temp = numpy.ceil(vmax*10**delta_powr)/10**delta_powr

        # print(f"{vmin=},",f"{vmax_temp=}")

        if curve.multp is None:

            multp_temp = (vmax_temp-vmin)/(delta_axis)
            multp_powr = -numpy.floor(numpy.log10(multp_temp))

            # print(f"{multp_temp=},")

            curve.multp = numpy.ceil(multp_temp*10**multp_powr)/10**multp_powr

            # print(f"{curve.multp=},")
        
        axis_vals = amin+(curve.vals-vmin)/curve.multp

        vmax = delta_axis*curve.multp+vmin
        
        # print(f"normalized_{vmin=},",f"normalized_{vmax=}")

        curve.xaxis = axis_vals
        curve.limit = (vmin,vmax)

    @staticmethod
    def set_logxaxis(curve,xaxis):

        vmin,_ = curve.limit

        if curve.multp is None:
            curve.multp = numpy.ceil(numpy.log10(1/vmin))

        axis_vals = curve.vals*10**curve.multp

        vmin = min(xaxis["limit"])/10**curve.multp
        vmax = max(xaxis["limit"])/10**curve.multp

        curve.xaxis = axis_vals
        curve.limit = (vmin,vmax)

    @staticmethod
    def get_pagesize(fmt="A4",orientation="portrait",unit="in"):

        fmt = fmt.lower()

        orientation = orientation.lower()

        unit = unit.lower()[:2]

        _page = {}

        a4,letter = {},{}

        if orientation == "portrait":
            a4["cm"] = [21.0,29.7]
            letter["in"] = [8.5,11.0]
        elif orientation == "landscape":
            a4["cm"] = [29.7,21.0]
            letter["in"] = [11.0,8.5]
        else:
            raise(f'Page orientation={orientation} has not been defined!')

        a4["in"] = [size/2.54 for size in a4['cm']]
        
        letter["cm"] = [size*2.54 for size in letter['in']]

        _page['a4'],_page['letter'] = a4,letter

        return {'width': _page[fmt][unit][0], 'height': _page[fmt][unit][1]}

    @staticmethod
    def get_pagegrid(fmt="A4",orientation="portrait"):

        fmt = fmt.lower()

        orientation = orientation.lower()

        _grid = {}

        if orientation=="portrait":
            a4,letter = [66,86],[66,81]
        elif orientation=="landscape":
            a4,letter = [90,61],[90,62]
        else:
            raise(f'Page orientation={orientation} has not been defined!')

        _grid['a4'],_grid['letter'] = a4,letter

        return {'width': _grid[fmt][0], 'height': _grid[fmt][1]}

    @staticmethod
    def set_axislabel(axis,xlim,ylim):

        axis.set_xlim(xlim)

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.set_ylim(ylim)

        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

    @staticmethod
    def set_axisdepth(axis,xaxis,yaxis):

        axis.set_ylim(yaxis['limit'])
        axis.set_xlim(xaxis['limit'])

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.yaxis.set_minor_locator(MultipleLocator(yaxis['subs']))
        axis.yaxis.set_major_locator(MultipleLocator(yaxis['base']))
        
        axis.tick_params(
            axis="y",which="both",direction="in",right=True,pad=-40)

        pyplot.setp(axis.get_yticklabels(),visible=False)

        xmin,xmax = xaxis['limit']

        for ytick in yaxis['ticks']:

            axis.annotate(f"{ytick:4.0f}",xy=((xmin+xmax)/2,ytick),
                horizontalalignment='center',
                verticalalignment='center',
                backgroundcolor='white',)

    @staticmethod
    def set_yaxiscurve(axis,yaxis):
        """It staticly sets y-axis of the given axis. Required keywords in yaxis:
        
        limit:  defines the ylim
        base:   sets the frequency of major ticks
        subs:   sets the frequency of minor ticks
        """

        axis.set_ylim(yaxis['limit'])

        axis.yaxis.set_minor_locator(MultipleLocator(yaxis['subs']))
        axis.yaxis.set_major_locator(MultipleLocator(yaxis['base']))

        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        axis.tick_params(axis="y",which="minor",left=False)

        axis.grid(axis="y",which='minor',color='k',alpha=0.4)
        axis.grid(axis="y",which='major',color='k',alpha=0.9)

    @staticmethod
    def set_xaxiscurve(axis,xaxis):
        """It staticly sets x-axis of the given axis. Required keywords in xaxis:
        
        limit:  defines the xlim
        scale:  linear or log
        subs:   sets the frequency of minor ticks
        """

        axis.set_xlim(xaxis['limit'])

        axis.set_xscale(xaxis['scale'])

        if xaxis['scale']=="linear":
            axis.xaxis.set_minor_locator(MultipleLocator(xaxis['subs']))
            axis.xaxis.set_major_locator(MultipleLocator(10))
        elif xaxis['scale']=="log":
            axis.xaxis.set_minor_locator(LogLocator(base=10,subs=xaxis['subs'],numticks=12))
            axis.xaxis.set_major_locator(LogLocator(base=10,numticks=12))

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.tick_params(axis="x",which="minor",bottom=False)

        axis.grid(axis="x",which='minor',color='k',alpha=0.4)
        axis.grid(axis="x",which='major',color='k',alpha=0.9)

    @staticmethod
    def set_labelcurve(axis,curve):

        axis.plot((0,1),(curve.row-0.6,curve.row-0.6),
            color=curve.color,linestyle=curve.style,linewidth=curve.width)

        axis.text(0.5,curve.row-0.5,f"{curve.head}",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        axis.text(0.5,curve.row-0.9,f"[{curve.unit}]",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        axis.text(0.02,curve.row-0.5,f"{curve.limit[0]:.5g}",horizontalalignment='left')
        axis.text(0.98,curve.row-0.5,f"{curve.limit[1]:.5g}",horizontalalignment='right')

    @staticmethod
    def set_labelmodule(axis,module):

        rect = Rectangle((0,module['row']),1,1,
            fill=True,facecolor=module['module']['fillcolor'],hatch=module['module']['hatch'])

        axis.add_patch(rect)

        axis.text(0.5,module['row']+0.5,module['module']['detail'],
            horizontalalignment='center',
            verticalalignment='center',
            backgroundcolor='white',
            fontsize='small',)

    @property
    def columns(self):

        columns = []

        for _,curve in self.curves.items():
            columns.append(curve.col)

        return len(set(columns))

    @property
    def rows(self):

        columns = []

        for _,curve in self.curves.items():
            columns.append(curve.col)

        columns_unique = set(columns)

        rows = []

        for column in columns_unique:
            rows.append(columns.count(column))

        nrows = 3 if max(rows)<3 else max(rows)

        return nrows

class BatchView(dirmaster):
    """It creates correlation based on multiple las files from different wells."""

    def __init__(self):

        pass

class WorkFlow():

    def __init__(self,lasfile=None,**kwargs):

        if lasfile is None:
            self.lasfile = LasFile(**kwargs)
        elif isinstance(lasfile,str):
            self.lasfile = loadlas(lasfile,**kwargs)
        elif isinstance(lasfile,LasFile):
            self.lasfile = lasfile

    def set_temps(self,unit="field",Tsurf=None,Tsurfdepth=0,Tgrad=None,Tmax=None,Tmaxdepth=None):
        """
        It will calculate the temperature based on the linear equation
        if it is not measured for every depth.
        
        unit         : unit system to be used for the calculation, field or international
        Tsurf        : temperature at the surface, °F or °C
        Tsurfdepth   : Tsurface depth where we know the temperature, ft or meters
        Tmax         : temperature at maximum depth, °F or °C
        Tmaxdepth    : maximum depth where we know the temperature, ft or meters
        Tgrad        : temperature gradient, °F/ft or °C/m

        """

        if Tmax is not None: #it should mean that Tmaxdepth is not None too

            if Tsurf is None: #it should mean that Tgrad is not None
                Tsurf = Tmax-Tgrad*(Tmaxdepth-Tsurfdepth)
            if Tgrad is None: #it should mean that Tsurf is not None
                Tgrad = (Tmax-Tsurf)/(Tmaxdepth-Tsurfdepth)

        temp = self.temperature(unit=unit,Tsurf=Tsurf,Tgrad=Tgrad)

        Tsurf = temp['Tsurf']
        Tgrad = temp['Tgrad']

        depth = self.lasfile.depth

        if unit == "field":
            cdepth = depth.convert('ft')
        elif unit == "international":
            cdepth = depth.convert('m')

        Temp = Tsurf+Tgrad*(cdepth.vals-Tsurfdepth)

        if unit == "field":
            Tunit = "degF"
        elif unit == "international":
            Tunit = "degC"

        info = f"Linear temperature with {unit} units, {Tsurf=}, {Tsurfdepth=}, {Tgrad=}."

        self.add_curve(vals=Temp,head='TEMP',unit=Tunit,info=info,depth=depth)

        temp['Tsurfdepth'] = Tsurfdepth
        
        self.temp = temp

    def set_perm(self,PHI,method=None):

        PHIE = self[PHI].vals

        PERM = 50*((1-0.13)**2)/(0.13**3)*(PHIE**3)/((1-PHIE)**2)

        depth = self.lasfile.depth

        info = 'Permeability calculated from effective porosity.'

        self.add_curve(vals=PERM,depth=depth,head='PERM',unit='mD',info=info)

    def set_bwv(self,PHI,SW):

        porosity = self[PHI].vals

        saturation = self[SW].vals

        BWV = porosity*saturation

        depth = self.lasfile.depth

        info = 'Bulk water volume.'

        self.add_curve(vals=BWV,depth=depth,head='BWV',unit='-',info=info)

    def __getattr__(self,key):

        return getattr(self.lasfile,key)

    def __setitem__(self,head,curve):

        self.lasfile[head] = curve

    def __getitem__(self,head):

        return self.lasfile[head]

    def __call__(self,**kwargs):
        """It is calling the interpretation method for the specified curve(s)."""

        if len(kwargs) != 1:
            raise "Number of optional arguments must be one specifying method and head dictionary."

        method,heads = kwargs.popitem()

        if not isinstance(heads,dict):
            raise "Heads must be dictionary!"

        curves = {}

        for head,curve in heads.items():
            curves[head] = self[curve]

        if method is None:
            return
        elif method.lower() == "sonic":
            return sonic(**curves)
        elif method.lower() == "spotential":
            return spotential(**curves)
        elif method.lower() == "laterolog":
            return laterolog(**curves)
        elif method.lower() == "induction":
            return induction(**curves)
        elif method.lower() == "gammaray":
            return gammaray(**curves)
        elif method.lower() == "density":
            return density(**curves)
        elif method.lower() == "neutron":
            return neutron(**curves)
        elif method.lower() == "nmr":
            return nmr(**curves)
        elif method.lower() == "density-neutron":
            return denneu(**curves)
        elif method.lower() == "sonic-density":
            return sonden(**curves)
        elif method.lower() == "sonic-neutron":
            return sonneu(**curves)
        elif method.lower() == "mn-plot":
            return mnplot(**curves)
        elif method.lower() == "mid-plot":
            return midplot(**curves)
        elif method.lower() == "rhomaa-umaa":
            return rhoumaa(**curves)
        elif method.lower() == "pickett":
            return pickett(**curves)
        elif method.lower() == "hingle":
            return hingle(**curves)

    @staticmethod
    def temperature(unit="field",Tsurf=None,Tgrad=None):
        """Returns temperature parameters for field and international units.
        
        unit    : Unit unit for temperature parameters, field and international

        Tsurf   : The average temperature of the sea Tsurf is about 20°C (68°F),
                  but it ranges from more than 30°C (86°F) in warm tropical regions
                  to less than 0°C at high latitudes. Input must be [°C] or [°F],
                  respectively.

        Tgrad   : Worldwide average geothermal Tgrads changes from 0.024 to 0.041°C/m
                  (0.013-0.022°F/ft), with extremes outside this range. Input must be
                  [°C/m] or [°F/ft], respectively.

        """

        temp = {}

        temp['unit'] = unit

        if unit == "international":
            Tgrad = 0.024 if Tgrad is None else Tgrad   # degC/m
            Tsurf = 20 if Tsurf is None else Tsurf      # degC
        elif unit == "field":
            Tgrad = 0.013 if Tgrad is None else Tgrad   # degF/ft
            Tsurf = 68 if Tsurf is None else Tsurf      # degF

        temp['Tsurf'] = Tsurf
        temp['Tgrad'] = Tgrad

        return temp

    @staticmethod
    def archie(m=2,a=1,Rw=0.01,n=2):

        archie = {}

        archie["m"] = m
        archie["a"] = a
        archie["Rw"] = Rw
        archie["n"] = n

        return archie

# TOOL INTERPRETATION

class sonic():

    def __init__(self,deltaTcomp,deltaTshear):

        self.dtcomp = dtcomp
        self.dtshear = dtshear

    def porosity(self):

        pass

class spotential():

    def __init__(self,SP=None,TEMP=None):
        """Initialization of output signals."""

        self.SP = SP

        self.TEMP = TEMP

    def config(self,**kwargs):
        """Setting tool configuration."""

        pass

    def get_temp(self,depthpoint):
        """Returns the temperature at the given depth based on interpolation of TEMP curve."""

        indices = numpy.argpartition(numpy.abs(self.depth-depthpoint),2)[:2]

        Dtop,Dbottom = self.depth[indices]
        Ttop,Tbottom = self.TEMP[indices]

        temp = Ttop+(Tbottom-Ttop)*(depthpoint-Dtop)/(Dbottom-Dtop)

        return temp

    def shalevolume(self,spsand=None,spshale=None):

        if spsand is None:
            spsand = self.SP.min()

        if spshale is None:
            spshale = self.SP.max()

        Vsh = (self.SP.vals-spsand)/(spshale-spsand)

        info = 'Shale volume calculated from spontaneous potential.'

        return LasCurve(
            depth = self.SP.depth,
            vals = Vsh,
            head = 'VSH',
            unit = '-',
            info = info)

    def cut(self,percent,spsand=None,spshale=None):

        if spsand is None:
            spsand = self.SP.min()

        if spshale is None:
            spshale = self.SP.max()

        return (percent/100.)*(spshale-spsand)+spsand

    def netthickness(self,percent,**kwargs):

        spcut = self.cut(percent,**kwargs)

        node_top = numpy.roll(self.SP.depth,1)
        node_bottom = numpy.roll(self.SP.depth,-1)

        thickness = (node_bottom-node_top)/2

        thickness[0] = (self.SP.depth[1].vals[0]-self.SP.depth[0].vals[0])/2
        thickness[-1] = (self.SP.depth[-1].vals[0]-self.SP.depth[-2].vals[0])/2

        return numpy.sum(thickness[self.SP.vals<spcut])

    def nettogrossratio(self,percent,**kwargs):

        return self.netthickness(percent,**kwargs)/self.SP.height['total']

    def formwaterres(self,method='bateman_and_konen',**kwargs):

        return getattr(self,f"{method}")(**kwargs)

    def bateman_and_konen(self,SSP,resmf,resmf_temp,depthpoint):

        resmf_75F = self.restemp_conversion(resmf,resmf_temp,75)

        if resmf_75F>0.1:
            resmfe_75F = 0.85*resmf_75F
        else:
            resmfe_75F = (146*resmf_75F-5)/(377*resmf_75F+77)

        K = 60+0.133*self.get_temp(depthpoint)

        reswe_75F = resmfe_75F/10**(-SSP/K)

        if reswe_75F>0.12:
            resw_75F = -(0.58-10**(0.69*reswe_75F-0.24))
        else:
            resw_75F = (77*reswe_75F+5)/(146-377*reswe_75F)

        return self.restemp_conversion(resw_75F,75,self.get_temp(depthpoint))

    def silva_and_bassiouni(self):

        return Rw

    @staticmethod
    def restemp_conversion(res1,T1,T2):

        return res1*(T1+6.77)/(T2+6.77)

    @property
    def depth(self):

        return self.SP.depth

class laterolog():

    def __init__(self,microres):

        self.microres = microres

    def porosity(self):

        pass

class induction():

    def __init__(self):

        pass

    def porosity(self):

        pass

class gammaray():

    def __init__(self,total,potassium=None,thorium=None,uranium=None):

        self.total = total

        if potassium is not None:
            self.potassium = potassium

        if thorium is not None:
            self.thorium = thorium

        if uranium is not None:
            self.uranium = utanium

    def config(self):

        pass

    def shaleindex(values,grmin=None,grmax=None):

        if grmin is None:
            grmin = numpy.nanmin(values)

        if grmax is None:
            grmax = numpy.nanmax(values)

        return (values-grmin)/(grmax-grmin)

    def shalevolume(values,model="linear",factor=None,grmin=None,grmax=None):

        if grmin is None:
            grmin = numpy.nanmin(values)

        if grmax is None:
            grmax = numpy.nanmax(values)

        index = (values-grmin)/(grmax-grmin)

        if model == "linear":
            volume = index
        elif factor is None:
            volume = getattr(gammaray,f"{model}")(index)
        else:
            volume = getattr(gammaray,f"{model}")(index,factor=factor)

        return volume

    def cut(values,percent=40,model="linear",factor=None,grmin=None,grmax=None):

        if model == "linear":
            index = percent/100
        elif factor is None:
            index = getattr(gammaray,f"_{model}")(None,volume=percent/100)
        else:
            index = getattr(gammaray,f"_{model}")(None,volume=percent/100,factor=factor)

        if grmin is None:
            grmin = numpy.nanmin(values)

        if grmax is None:
            grmax = numpy.nanmax(values)

        return index*(grmax-grmin)+grmin

    def netthickness(depth,values,percent,**kwargs):

        grcut = gammaray.get_cut(percent,**kwargs)

        node_top = numpy.roll(depth,1)
        node_bottom = numpy.roll(depth,-1)

        thickness = (node_bottom-node_top)/2

        thickness[0] = (depth[1]-depth[0])/2
        thickness[-1] = (depth[-1]-depth[-2])/2

        return numpy.sum(thickness[values<grcut])

    def netgrossratio(depth,*args,**kwargs):

        height = max(depth)-min(depth)

        return gammaray.netthickness(depth,*args,**kwargs)/height

    def set_axis(self,axis=None):

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        self.axis = axis

    def show(self):

        pyplot.show()

    def larionov_oldrocks(index,volume=None):
        if volume is None:
            return 0.33*(2**(2*index)-1)
        elif index is None:
            return numpy.log2(volume/0.33+1)/2

    def clavier(index,volume=None):
        if volume is None:
            return 1.7-numpy.sqrt(3.38-(0.7+index)**2)
        elif index is None:
            return numpy.sqrt(3.38-(1.7-volume)**2)-0.7

    def bateman(index,volume=None,factor=1.2):
        if volume is None:
            return index**(index+factor)
        elif index is None:
            return #could not calculate inverse yet

    def stieber(index,volume=None,factor=3):
        if volume is None:
            return index/(index+factor*(1-index))
        elif index is None:
            return volume*factor/(1+volume*(factor-1))

    def larionov_tertiary(index,volume=None):
        if volume is None:
            return 0.083*(2**(3.7*index)-1)
        elif index is None:
            return numpy.log2(volume/0.083+1)/3.7

class density():

    def __init__(self,compton,photoe):

        self.compton = compton
        self.photoe = photoe

    def porosity():

        pass

class neutron():

    def __init__(self,NGL=None,VSH=None):
        """Initialization of output signals."""

        self.NGL = NGL
        self.VSH = VSH

    def config(self,observer):
        """Setting tool configuration."""

        self.observer = observer  # gamma capture rate or neutron count

    def phit(self,*args,**kwargs):

        if self.observer.lower() == "gamma":
            func = getattr(self,"_gamma_capture_total")
        elif self.observer.lower() == "neutron":
            func = getattr(self,"_neutron_count_total")

        return func(*args,**kwargs)

    def phie(self,*args,**kwargs):

        if self.observer.lower() == "gamma":
            func = getattr(self,"_gamma_capture_effective")
        elif self.observer.lower() == "neutron":
            func = getattr(self,"_neutron_count_effective")

        return func(*args,**kwargs)

    def _gamma_capture_total(self,phi_clean,phi_shale,ngl_clean=None,ngl_shale=None):
        """The porosity based on gamma detection:
        
        phi_clean    :  porosity in the clean formation
        phi_shale    :  porosity in the adjacent shale

        ngl_clean    :  NGL reading in the clean formation
        ngl_shale    :  NGL reading in the adjacent shale
        
        """

        if ngl_clean is None:
            ngl_clean = self.NGL.min()

        if ngl_shale is None:
            ngl_shale = self.NGL.max()

        normalized = (self.NGL.vals-ngl_clean)/(ngl_shale-ngl_clean)

        normalized[normalized<=0] = 0
        normalized[normalized>=1] = 1

        PHIT = phi_clean+(phi_shale-phi_clean)*normalized

        info = 'Total porosity calculated from neutron-gamma-log.'

        return LasCurve(
            depth = self.NGL.depth,
            vals = PHIT,
            head = 'PHIT',
            unit = '-',
            info = info)

    def _gamma_capture_effective(self,phi_clean,phi_shale,**kwargs):
        """
        shale_volume :  it is required for the calculation of effective porosity,
                        and it can be calculated from etiher GR or SP logs.
        """

        PHIT = self._gamma_capture_total(phi_clean,phi_shale,**kwargs)

        PHIE = PHIT.vals-self.VSH.vals*phi_shale

        info = 'Effective porosity calculated from neutron-gamma-log.'

        return LasCurve(
            depth = self.NGL.depth,
            vals = PHIE,
            head = 'PHIE',
            unit = '-',
            info = info)

    def _neutron_count(self,a,b):
        """The porosity based on the neutron count is given by:
        
        nnl = a-b*log(phi)
        
        curve   :  neutron-neutron-logging curve, the slow neutrons counted

        a       :  empirical constants determined by appropriate calibration
        b       :  empirical constants determined by appropriate calibration

        phi     :  porosity

        """

        porosity = {}

        total = 10**((a-curve.vals)/b)

        return total

class nmr():

    def __init__(self):
        """Tool configuration and output signal initialization."""

        pass

    def porosity():

        pass

# LITHOLOGY MODELING

class denneu():

    def __init__(self,rhof=1.0,phiNf=1.0,NTool="CNL",**kwargs):

        self.rhof = rhof
        self.phiNf = phiNf

        self.NTool = NTool

        self.Dens = {}
        self.Neus = {}

        self.lithos()

    def lithos(self):

        phima = f"phima_{self.NTool}"

        self.Dens["SS1"] = self.SS["type1"]["rhoma"]
        self.Neus["SS1"] = self.SS["type1"][phima]

        self.Dens["SS2"] = self.SS["type2"]["rhoma"]
        self.Neus["SS2"] = self.SS["type2"][phima]

        self.Dens["LS1"] = self.LS["type1"]["rhoma"]
        self.Neus["LS1"] = self.LS["type1"][phima]

        self.Dens["DOL1"] = self.DOL["type1"]["rhoma"]
        self.Neus["DOL1"] = self.DOL["type1"][phima]

        self.Dens["DOL2"] = self.DOL["type2"]["rhoma"]
        self.Neus["DOL2"] = self.DOL["type2"][phima]

        self.Dens["DOL3"] = self.DOL["type3"]["rhoma"]
        self.Neus["DOL3"] = self.DOL["type3"][phima]

        self.Dens["ANH1"] = self.ANH["type1"]["rhoma"]
        self.Neus["ANH1"] = self.ANH["type1"][phima]

        self.Dens["SLT1"] = self.SLT["type1"]["rhoma"]
        self.Neus["SLT1"] = self.SLT["type1"][phima]

    def lithonodes(self,axis):

        DENSS  = [self.Dens["SS2"]] #self.Dens["SS1"],
        NEUSS  = [self.Neus["SS2"]] #self.Neus["SS1"],

        DENLS  = [self.Dens["LS1"]]
        NEULS  = [self.Neus["LS1"]]

        DENDOL = [self.Dens["DOL3"]] #self.Dens["DOL1"],self.Dens["DOL2"],
        NEUDOL = [self.Neus["DOL3"]] #self.Neus["DOL1"],self.Neus["DOL2"],

        DENANH = [self.Dens["ANH1"]]
        NEUANH = [self.Neus["ANH1"]]

        DENSLT = [self.Dens["SLT1"]]
        NEUSLT = [self.Neus["SLT1"]]

        axis.plot(NEUSS,DENSS,label=self.SS["lithology"],
            linestyle="None",
            marker=self.SS["marker"],
            markerfacecolor=self.SS["markercolor"],
            markeredgecolor=self.SS["markercolor"])

        axis.plot(NEULS,DENLS,label=self.LS["lithology"],
            linestyle="None",
            marker=self.LS["marker"],
            markerfacecolor=self.LS["markercolor"],
            markeredgecolor=self.LS["markercolor"])

        axis.plot(NEUDOL,DENDOL,label=self.DOL["lithology"],
            linestyle="None",
            marker=self.DOL["marker"],
            markerfacecolor=self.DOL["markercolor"],
            markeredgecolor=self.DOL["markercolor"])

        axis.plot(NEUANH,DENANH,label=self.ANH["lithology"],
            linestyle="None",
            marker=self.ANH["marker"],
            markerfacecolor=self.ANH["markercolor"],
            markeredgecolor=self.ANH["markercolor"])

        axis.plot(NEUSLT,DENSLT,label=self.SLT["lithology"],
            linestyle="None",
            marker=self.SLT["marker"],
            markerfacecolor=self.SLT["markercolor"],
            markeredgecolor=self.SLT["markercolor"])

        axis.set_xlabel(f"PHI-{self.NTool}, Apparent Limestone Porosity")
        axis.set_ylabel("RHOB Bulk Density, g/cm3")

        axis.legend(loc="upper center",ncol=3,bbox_to_anchor=(0.5,1.15))

        axis.set_xlim((-0.05,0.45))
        axis.set_ylim((3.0,1.9))

        xmajor_ticks = numpy.arange(-0.00,0.45,0.05)
        xminor_ticks = numpy.arange(-0.05,0.45,0.01)

        ymajor_ticks = numpy.arange(1.9,3.01,0.1)
        yminor_ticks = numpy.arange(1.9,3.01,0.02)

        axis.set_xticks(xmajor_ticks,minor=False)
        axis.set_xticks(xminor_ticks,minor=True)

        axis.set_yticks(ymajor_ticks,minor=False)
        axis.set_yticks(yminor_ticks,minor=True)

        axis.grid(which='both')

        axis.grid(which='minor',alpha=0.2)
        axis.grid(which='major',alpha=0.5)

        return axis

    def litholines(self,axis):

        a_SS = +0.00
        a_LS = +0.00
        a_DOL = 0.10

        b_SS = +0.90
        b_LS = +0.80
        b_DOL = +0.57

        c1_SS = 10**((a_LS-a_SS)/b_LS)
        c1_LS = 10**((a_LS-a_LS)/b_LS)
        c1_DOL = 10**((a_LS-a_DOL)/b_LS)

        c2_SS = b_SS/b_LS
        c2_LS = b_LS/b_LS
        c2_DOL = b_DOL/b_LS

        porosity = numpy.linspace(0,0.45,100)

        DENSS = self.Dens["SS2"]-porosity*(self.Dens["SS2"]-self.rhof)
        NEUSS = c1_SS*(porosity)**c2_SS+self.Neus["SS2"]

        DENLS = self.Dens["LS1"]-porosity*(self.Dens["LS1"]-self.rhof)
        NEULS = c1_LS*(porosity)**c2_LS+self.Neus["LS1"]

        DENDOL = self.Dens["DOL3"]-porosity*(self.Dens["DOL3"]-self.rhof)
        NEUDOL = c1_DOL*(porosity)**c2_DOL+self.Neus["DOL3"]

        axis.plot(NEUSS,DENSS,color='black',linewidth=0.3)
        axis.plot(NEULS,DENLS,color='black',linewidth=0.3)
        axis.plot(NEUDOL,DENDOL,color='black',linewidth=0.3)

    def terniary(self):

        pass

    def lithoratio(self):

        pass

class sonden():

    def __init__(self,**kwargs):

        pass

class sonneu():

    def __init__(self,DT_FLUID=189,PHI_NF=1,**kwargs):

        self.DT_FLUID = DT_FLUID
        self.PHI_NF = PHI_NF

    def lithos(self):

        # porLine,
        # sonLine,
        # a_SND=+0.00,
        # a_LMS=+0.00,
        # a_DOL=-0.06,
        # b_SND=+0.90,
        # b_LMS=+0.80,
        # b_DOL=+0.84,
        # p_SND=+0.02,
        # p_LMS=+0.00,
        # p_DOL=-0.01,
        # DT_SND=55.6,
        # DT_LMS=47.5,
        # DT_DOL=43.5,
        # xmin=None,
        # ymin=None,
        # xmax=None,
        # ymax=None,
        # rotate=0

        self.fig_sncp.set_figwidth(5)
        self.fig_sncp.set_figheight(6)

        c1_SND = 10**((a_LMS-a_SND)/b_LMS)
        c1_LMS = 10**((a_LMS-a_LMS)/b_LMS)
        c1_DOL = 10**((a_LMS-a_DOL)/b_LMS)

        c2_SND = b_SND/b_LMS
        c2_LMS = b_LMS/b_LMS
        c2_DOL = b_DOL/b_LMS

        porSND = numpy.linspace(0,0.45,46)
        porLMS = numpy.linspace(0,0.45,46)
        porDOL = numpy.linspace(0,0.45,46)

        sonicSND = porSND*(DT_FLUID-DT_SND)+DT_SND
        sonicLMS = porLMS*(DT_FLUID-DT_LMS)+DT_LMS
        sonicDOL = porDOL*(DT_FLUID-DT_DOL)+DT_DOL

        porLMS_SND = c1_SND*(porSND)**c2_SND-p_SND
        porLMS_LMS = c1_LMS*(porLMS)**c2_LMS-p_LMS
        porLMS_DOL = c1_DOL*(porDOL)**c2_DOL-p_DOL

        xaxis_max = 0.5
        yaxis_max = 110

        for depth in self.depths:

            xaxis = self.get_interval(*depth[1:],idframe=porLine[0],curveID=porLine[1])
            yaxis = self.get_interval(*depth[1:],idframe=sonLine[0],curveID=sonLine[1])

            xaxis_max = max((xaxis_max,xaxis[0].max()))
            yaxis_max = max((yaxis_max,yaxis[0].max()))

            self.axis_sncp.scatter(xaxis,yaxis,s=1,label=depth[0])

        self.axis_sncp.legend(scatterpoints=10)

        self.axis_sncp.plot(porLMS_SND,sonicSND,color='blue',linewidth=0.3)
        self.axis_sncp.plot(porLMS_LMS,sonicLMS,color='blue',linewidth=0.3)
        self.axis_sncp.plot(porLMS_DOL,sonicDOL,color='blue',linewidth=0.3)

        self.axis_sncp.scatter(porLMS_SND[::5],sonicSND[::5],marker=(2,0,45),color="blue")
        self.axis_sncp.scatter(porLMS_LMS[::5],sonicLMS[::5],marker=(2,0,45),color="blue")
        self.axis_sncp.scatter(porLMS_DOL[::5],sonicDOL[::5],marker=(2,0,45),color="blue")

        self.axis_sncp.text(porLMS_SND[27],sonicSND[26],'Sandstone',rotation=rotate)
        self.axis_sncp.text(porLMS_LMS[18],sonicLMS[17],'Calcite (limestone)',rotation=rotate)
        self.axis_sncp.text(porLMS_DOL[19],sonicDOL[18],'Dolomite',rotation=rotate)

        self.axis_sncp.set_xlabel("Apparent Limestone Neutron Porosity")
        self.axis_sncp.set_ylabel("Sonic Transit Time $\\Delta$t [$\\mu$s/ft]")

        xaxis_min = -0.05 if xmin is None else xmin
        yaxis_min = +40.0 if ymin is None else ymin

        xaxis_max = xaxis_max if xmax is None else xmax
        yaxis_max = yaxis_max if ymax is None else ymax

        self.axis_sncp.set_xlim([xaxis_min,xaxis_max])
        self.axis_sncp.set_ylim([yaxis_min,yaxis_max])

        self.axis_sncp.xaxis.set_minor_locator(AutoMinorLocator(10))
        self.axis_sncp.yaxis.set_minor_locator(AutoMinorLocator(10))

        self.axis_sncp.grid(True,which="both",axis='both')

        self.fig_sncp.tight_layout()

    def litholines(self,axis):

        pass

    def ternary(self,axis):

        pass

    def lithoratio(self):

        pass

class mnplot():

    def __init__(self,DTf=189,rhof=1.0,phiNf=1.0,NTool="SNP",**kwargs):

        self.DTf = DTf
        self.rhof = rhof
        self.phiNf = phiNf

        self.NTool = NTool

        self.Ms = {}
        self.Ns = {}

        self.lithos()

    def MValue(self,DT,rhob):

        return (self.DTf-DT)/(rhob-self.rhof)*0.01

    def NValue(self,PhiN,rhob):

        return (self.phiNf-PhiN)/(rhob-self.rhof)

    def lithos(self):

        phima = f"phima_{self.NTool}"

        self.Ms["SS1"] = self.MValue(self.SS["type1"]["DTma"],self.SS["type1"]["rhoma"])
        self.Ns["SS1"] = self.NValue(self.SS["type1"][phima],self.SS["type1"]["rhoma"])

        self.Ms["SS2"] = self.MValue(self.SS["type2"]["DTma"],self.SS["type2"]["rhoma"])
        self.Ns["SS2"] = self.NValue(self.SS["type2"][phima],self.SS["type2"]["rhoma"])

        self.Ms["LS1"] = self.MValue(self.LS["type1"]["DTma"],self.LS["type1"]["rhoma"])
        self.Ns["LS1"] = self.NValue(self.LS["type1"][phima],self.LS["type1"]["rhoma"])

        self.Ms["DOL1"] = self.MValue(self.DOL["type1"]["DTma"],self.DOL["type1"]["rhoma"])
        self.Ns["DOL1"] = self.NValue(self.DOL["type1"][phima],self.DOL["type1"]["rhoma"])

        self.Ms["DOL2"] = self.MValue(self.DOL["type2"]["DTma"],self.DOL["type2"]["rhoma"])
        self.Ns["DOL2"] = self.NValue(self.DOL["type2"][phima],self.DOL["type2"]["rhoma"])

        self.Ms["DOL3"] = self.MValue(self.DOL["type3"]["DTma"],self.DOL["type3"]["rhoma"])
        self.Ns["DOL3"] = self.NValue(self.DOL["type3"][phima],self.DOL["type3"]["rhoma"])

        self.Ms["ANH1"] = self.MValue(self.ANH["type1"]["DTma"],self.ANH["type1"]["rhoma"])
        self.Ns["ANH1"] = self.NValue(self.ANH["type1"][phima],self.ANH["type1"]["rhoma"])

        self.Ms["SLT1"] = self.MValue(self.SLT["type1"]["DTma"],self.SLT["type1"]["rhoma"])
        self.Ns["SLT1"] = self.NValue(self.SLT["type1"][phima],self.SLT["type1"]["rhoma"])

    def lithonodes(self,axis):

        NSS  = [self.Ns["SS1"],self.Ns["SS2"]]
        MSS  = [self.Ms["SS1"],self.Ms["SS2"]]
        NLS  = [self.Ns["LS1"]]
        MLS  = [self.Ms["LS1"]]
        NDOL = [self.Ns["DOL1"],self.Ns["DOL2"],self.Ns["DOL3"]]
        MDOL = [self.Ms["DOL1"],self.Ms["DOL2"],self.Ms["DOL3"]]
        NANH = [self.Ns["ANH1"]]
        MANH = [self.Ms["ANH1"]]
        NSLT = [self.Ns["SLT1"]]
        MSLT = [self.Ms["SLT1"]]

        axis.plot(NSS,MSS,label=self.SS["lithology"],
            linestyle="None",
            marker=self.SS["marker"],
            markerfacecolor=self.SS["markercolor"],
            markeredgecolor=self.SS["markercolor"])

        axis.plot(NLS,MLS,label=self.LS["lithology"],
            linestyle="None",
            marker=self.LS["marker"],
            markerfacecolor=self.LS["markercolor"],
            markeredgecolor=self.LS["markercolor"])

        axis.plot(NDOL,MDOL,label=self.DOL["lithology"],
            linestyle="None",
            marker=self.DOL["marker"],
            markerfacecolor=self.DOL["markercolor"],
            markeredgecolor=self.DOL["markercolor"])

        axis.plot(NANH,MANH,label=self.ANH["lithology"],
            linestyle="None",
            marker=self.ANH["marker"],
            markerfacecolor=self.ANH["markercolor"],
            markeredgecolor=self.ANH["markercolor"])

        axis.plot(NSLT,MSLT,label=self.SLT["lithology"],
            linestyle="None",
            marker=self.SLT["marker"],
            markerfacecolor=self.SLT["markercolor"],
            markeredgecolor=self.SLT["markercolor"])

        axis.set_xlabel("N-values")
        axis.set_ylabel("M-values")

        axis.legend(loc="upper center",ncol=3,bbox_to_anchor=(0.5,1.15))

        axis.set_xlim((0.3,1))
        axis.set_ylim((0.5,1.2))

        xmajor_ticks = numpy.arange(0.3,1.01,0.1)
        xminor_ticks = numpy.arange(0.3,1.01,0.02)

        ymajor_ticks = numpy.arange(0.5,1.21,0.1)
        yminor_ticks = numpy.arange(0.5,1.21,0.02)

        axis.set_xticks(xmajor_ticks,minor=False)
        axis.set_xticks(xminor_ticks,minor=True)

        axis.set_yticks(ymajor_ticks,minor=False)
        axis.set_yticks(yminor_ticks,minor=True)

        axis.grid(which='both')

        axis.grid(which='minor',alpha=0.2)
        axis.grid(which='major',alpha=0.5)

        return axis

    def ternary(self,axis,lith1="SS1",lith2="LS1",lith3="DOL1",num=10):

        p1 = [self.Ns[lith1],self.Ms[lith1]]
        p2 = [self.Ns[lith2],self.Ms[lith2]]
        p3 = [self.Ns[lith3],self.Ms[lith3]]

        nodes = [p1,p2,p3]

        xmin = min((p1[0],p2[0],p3[0]))
        xmax = max((p1[0],p2[0],p3[0]))

        ymin = min((p1[1],p2[1],p3[1]))
        ymax = max((p1[1],p2[1],p3[1]))

        xmin = 0.3+int((xmin-0.3)/0.02)*0.02
        xmax = 1.0-int((1.0-xmax)/0.02)*0.02

        ymin = 0.5+int((ymin-0.5)/0.02)*0.02
        ymax = 1.2-int((1.2-ymax)/0.02)*0.02

        axis.plot([p1[0],p2[0]],[p1[1],p2[1]],'k',linewidth=0.5)
        axis.plot([p2[0],p3[0]],[p2[1],p3[1]],'k',linewidth=0.5)
        axis.plot([p3[0],p1[0]],[p3[1],p1[1]],'k',linewidth=0.5)

        axis.set_xlim([xmin,xmax])
        axis.set_ylim([ymin,ymax])

        xmajor_ticks = numpy.arange(xmin,xmax+1e-5,0.02)

        if xmajor_ticks.size<10:
            axis.set_xticks(xmajor_ticks,minor=False)

        ymajor_ticks = numpy.arange(ymin,ymax+1e-5,0.02)

        if ymajor_ticks.size<10:
            axis.set_yticks(ymajor_ticks,minor=False)

        axis.grid(visible=True)

        index = numpy.arange(1,num)

        xs1 = p1[0]+index*(p2[0]-p1[0])/num
        xs2 = p2[0]+index*(p3[0]-p2[0])/num
        xs3 = p3[0]+index*(p1[0]-p3[0])/num

        ys1 = p1[1]+index*(p2[1]-p1[1])/num
        ys2 = p2[1]+index*(p3[1]-p2[1])/num
        ys3 = p3[1]+index*(p1[1]-p3[1])/num

        axis.plot([p1[0],p2[0]],[p1[1],p2[1]],'k',linewidth=0.5)
        axis.plot([p2[0],p3[0]],[p2[1],p3[1]],'k',linewidth=0.5)
        axis.plot([p3[0],p1[0]],[p3[1],p1[1]],'k',linewidth=0.5)

        for i in index:
            axis.plot([xs1[i-1],xs2[num-1-i]],[ys1[i-1],ys2[num-1-i]],'k',linewidth=0.5)
            axis.plot([xs2[i-1],xs3[num-1-i]],[ys2[i-1],ys3[num-1-i]],'k',linewidth=0.5)
            axis.plot([xs3[i-1],xs1[num-1-i]],[ys3[i-1],ys1[num-1-i]],'k',linewidth=0.5)

        return axis,nodes

    def lithoratio(self,nodes):
        
        pass

class midplot():

    def __init__(self):

        pass

class rhoumaa():

    def __init__(self):

        pass

# SATURATION MODELING

class pickett():

    def __init__(self,PHI=None,RT=None):
        """Initialization of Pickett (porosity vs. resistivity)
        cross-plot that assists in water saturation calculation.

        PHI : las curve for porosity (y-axis).
        RT  : las curve for resistivity (x-axis).

        """

        self.PHI = PHI

        self.RT = RT

    def config(self,slope=None,intercept=None,**kwargs):
        """Configures the cross-plot settings

        slope           : slope of 100% water saturation line, negative of cementation exponent.
        intercept       : intercept of 100% water saturation line, multiplication of
                          tortuosity exponent and formation water resistivity.
        
        **kwargs        : archie parameters, keys are 'm', 'a', 'Rw' and 'n'. 
        """

        archie = {}

        for key,value in kwargs.items():
            archie[key] = value

        self.archie = archie

        if slope is None:
            slope = -1/self.archie['m']

        self.slope = slope

        if intercept is None:
            intercept = numpy.log10(self.archie['a']*self.archie['Rw'])/self.archie['m']

        self.intercept = intercept

    def set_axis(self,axis=None):

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        self.axis = axis

        xaxis = self.resistivity.vals
        yaxis = self.porosity.vals

        self.axis.scatter(xaxis,yaxis,s=2,c="k")

        self.axis.set_xscale('log')
        self.axis.set_yscale('log')

        xlim = numpy.array(self.axis.get_xlim())
        ylim = numpy.array(self.axis.get_ylim())

        self.xlim = numpy.floor(numpy.log10(xlim))+numpy.array([0,1])
        self.ylim = numpy.floor(numpy.log10(ylim))+numpy.array([0,1])

        self.axis.set_xlabel(f"Resistivity [{self.resistivity.unit}]")
        self.axis.set_ylabel(f"Porosity [{self.porosity.unit}]")

        self.axis.set_xlim(10**self.xlim)
        self.axis.set_ylim(10**self.ylim)

        fstring = 'x={:1.3f} y={:1.3f} m={:1.3f} b={:1.3f}'

        self.axis.format_coord = lambda x,y: fstring.format(x,y,-1/self.slope,self.intercept)

        self.lines = []

        self.canvas = self.axis.figure.canvas

    def set_lines(self,*args):
        """arguments must be water saturation percentage in a decreasing order!"""

        saturations = [100]

        [saturations.append(arg) for arg in args]

        base = self.slope*self.xlim+self.intercept

        for line in self.lines:

            line.remove()

        self.lines = []

        linewidth = 1.0

        alpha = 1.0

        X = 10**self.xlim

        n = self.archie['n']

        m = -1/self.slope

        for Sw in saturations:

            Sw = Sw/100

            Y = 10**(base-n/m*numpy.log10(Sw))

            line, = self.axis.plot(X,Y,linewidth=linewidth,color="blue",alpha=alpha)

            linewidth -= 0.1

            alpha -= 0.1

            self.lines.append(line)

        self.canvas.draw()

    def set_mouse(self):

        self.pressed = False
        self.start = False

        self.canvas.mpl_connect('button_press_event',self._mouse_press)
        self.canvas.mpl_connect('motion_notify_event',self._mouse_move)
        self.canvas.mpl_connect('button_release_event',self._mouse_release)

    def _mouse_press(self,event):

        if self.axis.get_navigate_mode()!= None: return
        if not event.inaxes: return
        if event.inaxes != self.axis: return

        if self.start: return

        if event.button is not MouseButton.LEFT: return

        self.pressed = True

    def _mouse_move(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if not self.pressed: return

        self.start = True

        x = numpy.log10(event.xdata)
        y = numpy.log10(event.ydata)

        self.intercept = y-self.slope*x

        self.set_lines()

    def _mouse_release(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if self.pressed:

            self.pressed = False
            self.start = False

            self.set_lines(50,20,10)

            return

    def show(self):

        pyplot.show()

    def saturation(self):

        m = -1/self.slope

        aRw = 10**(m*self.intercept)

        n = self.archie['n']

        Rt = self.RT.vals

        phi = self.PHI.vals

        Sw = (aRw/Rt/phi**m)**(1/n)

        Sw[Sw>1] = 1

        info = 'Water saturation from Pickett Cross-Plot.'

        return LasCurve(
            depth = self.depth,
            vals = Sw,
            head = 'SW',
            unit = '-',
            info = info)

    @property
    def depth(self):

        return self.PHI.depth

class hingle():

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

    def set_axis(self,axis=None):

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        self.axis = axis

    def show(self):

        pyplot.show()

if __name__ == "__main__":

    bm = BulkModel(sandstone=1)

    for key in bm.library.keys():
        print(key)

    # for item in bm.library:
    #     print(item)