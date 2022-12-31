import copy

import json

import os

import re

from matplotlib import colors as mcolors
from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import transforms

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

from PIL import ImageTk, Image

if __name__ == "__main__":
    import dirsetup

from datum import column
from datum import frame

from textio import dirmaster
from textio import header

from wlogs import *

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

class lascurve(column):

    def __init__(self,**kwargs):

        self.depths = kwargs.pop("depths")

        super().__init__(
            vals = pop(kwargs,"vals"),
            head = pop(kwargs,"head"),
            unit = pop(kwargs,"unit"),
            info = pop(kwargs,"info"),
            size = pop(kwargs,"size"),
            dtype = pop(kwargs,"dtype"))

        if kwargs.get("color") is None:
            kwargs["color"] = "black"

        if kwargs.get("style") is None:
            kwargs["style"] = "solid"

        if kwargs.get("width") is None:
            kwargs["width"] = 0.75

        self.set_style(**kwargs)

    def set_style(self,**kwargs):

        for key,value in kwargs.items():
            setattr(self,key,value)

    @property
    def height(self):

        depths = self.depths

        total = depths.max()-depths.min()

        node_head = numpy.roll(depths,1)
        node_foot = numpy.roll(depths,-1)

        thickness = (node_foot-node_head)/2

        thickness[ 0] = (depths[ 1]-depths[ 0])/2
        thickness[-1] = (depths[-1]-depths[-2])/2

        null = numpy.sum(thickness[self.isnone()])

        return {'total': total, 'null': null, 'valid': total-null,}
    
class lasfile(dirmaster):

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        self.sections = []

    def add_section(self,key,mnemonic,unit,value,description):

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

        self.ascii = frame(*args,**kwargs)

        self.sections.append("ascii")

    def __getitem__(self,key):

        return lascurve(
            vals = self.ascii[key].vals,
            head = self.ascii[key].head,
            unit = self.ascii[key].unit,
            info = self.ascii[key].info,
            depths = self.depths,
            )

    def write(self,filepath):

        import lasio

        """
        filepath:       It will write a lasio.LASFile to the given filepath

        kwargs:         These are mnemonics, data, units, descriptions, values
        """

        lasmaster = lasio.LASFile()

        lasmaster.well.DATE = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        depthExistFlag = False

        for mnemonic in mnemonics:
            if mnemonic=="MD" or mnemonic=="DEPT" or mnemonic=="DEPTH":
                depthExistFlag = True
                break

        if not depthExistFlag:
            curve = lasio.CurveItem(
                mnemonic="DEPT",
                unit="",
                value="",
                descr="Depth index",
                data=numpy.arange(data[0].size))
            lasmaster.append_curve_item(curve)            

        for index,(mnemonic,datum) in enumerate(zip(mnemonics,data)):

            if units is not None:
                unit = units[index]
            else:
                unit = ""

            if descriptions is not None:
                description = descriptions[index]
            else:
                description = ""

            if values is not None:
                value = values[index]
            else:
                value = ""

            curve = lasio.CurveItem(mnemonic=mnemonic,data=datum,unit=unit,descr=description,value=value)

            lasmaster.append_curve_item(curve)

        with open(filepath, mode='w') as filePathToWrite:
            lasmaster.write(filePathToWrite)

    def nanplot(self,axis):

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
        axis.set_xticklabels(depth[qvals],rotation=90)

        axis.set_yticks(numpy.arange(self.ascii.shape[1]))
        axis.set_yticklabels(self.ascii.heads)

        axis.grid(True,which="both",axis='x')

        return axis

    def trim(self,*args,strt=None,stop=None,curve=None):
        """It trims the data based on the strt and stop depths"""

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
            conds = self.depths<=stop
        elif strt is not None and stop is None:
            conds = self.depths>=strt
        else:
            conds = numpy.logical_and(self.depths>=strt,self.depths<=stop)

        if curve is not None:
            return self[curve][conds]

        self.ascii = self.ascii[conds]

        self.well.fields[2][self.well.mnemonic.index('STRT')] = str(self.depths[0])
        self.well.fields[2][self.well.mnemonic.index('STOP')] = str(self.depths[-1])

    def resample(self,depths):
        """Resamples the frame data based on given depths:

        depths :   The depth values where new curve data will be calculated;
        """

        depths_current = self.ascii.running[0].vals

        if not lasfile.isvalid(depths):
            raise ValueError("There are none values in depths.")

        if not lasfile.issorted(depths):
            depths = numpy.sort(depths)

        outers_above = depths<depths_current.min()
        outers_below = depths>depths_current.max()

        inners = numpy.logical_and(~outers_above,~outers_below)

        depths_inners = depths[inners]

        lowers = numpy.empty(depths_inners.shape,dtype=int)
        uppers = numpy.empty(depths_inners.shape,dtype=int)

        lower,upper = 0,0

        for index,depth in enumerate(depths_inners):

            while depth>depths_current[lower]:
                lower += 1

            while depth>depths_current[upper]:
                upper += 1

            lowers[index] = lower-1
            uppers[index] = upper

        delta_depths = depths_inners-depths_current[lowers]

        delta_depths_current = depths_current[uppers]-depths_current[lowers]

        grads = delta_depths/delta_depths_current

        for index,_column in enumerate(self.ascii.running):

            if index==0:
                self.ascii.running[index].vals = depths
                continue

            delta_values = _column.vals[uppers]-_column.vals[lowers]

            self.ascii.running[index].vals = numpy.empty(depths.shape,dtype=float)

            self.ascii.running[index].vals[outers_above] = numpy.nan
            self.ascii.running[index].vals[inners] = _column.vals[lowers]+grads*(delta_values)
            self.ascii.running[index].vals[outers_below] = numpy.nan

    @staticmethod
    def resample_curve(depths,curve):
        """Resamples the curve.vals based on given depths, and returns curve:

        depths      :   The depths where new curve values will be calculated;
        curve       :   The curve object to be resampled

        """

        if not lasfile.isvalid(depths):
            raise ValueError("There are none values in depths.")

        if not lasfile.issorted(depths):
            depths = numpy.sort(depths)

        outers_above = depths<curve.depths.min()
        outers_below = depths>curve.depths.max()

        inners = numpy.logical_and(~outers_above,~outers_below)

        depths_inners = depths[inners]

        lowers = numpy.empty(depths_inners.shape,dtype=int)
        uppers = numpy.empty(depths_inners.shape,dtype=int)

        lower,upper = 0,0

        for index,depth in enumerate(depths_inners):

            while depth>curve.depths[lower]:
                lower += 1

            while depth>curve.depths[upper]:
                upper += 1

            lowers[index] = lower-1
            uppers[index] = upper

        delta_depths = depths_inners-curve.depths[lowers]

        delta_depths_current = curve.depths[uppers]-curve.depths[lowers]
        delta_values_current = curve.vals[uppers]-curve.vals[lowers]

        grads = delta_depths/delta_depths_current

        values = numpy.empty(depths.shape,dtype=float)

        values[outers_above] = numpy.nan
        values[inners] = curve.vals[lowers]+grads*(delta_values_current)
        values[outers_below] = numpy.nan

        curve.depths = depths

        curve.vals = values

        return curve

    @property
    def height(self):

        depths = self.depths

        total = depths.max()-depths.min()

        return {'total': total,}

    @property
    def depths(self):

        return self.ascii.running[0].vals

    @property
    def isdepthvalid(self):
        
        return lasfile.isvalid(self.depths)

    @staticmethod
    def isvalid(vals):

        return numpy.all(~numpy.isnan(vals))

    @property
    def isdepthpositive(self):

        return lasfile.ispositive(self.depths)

    @staticmethod
    def ispositive(vals):

        return numpy.all(vals>=0)

    @property
    def isdepthsorted(self):

        return lasfile.issorted(self.depths)

    @staticmethod
    def issorted(vals):

        return numpy.all(vals[:-1]<vals[1:])

def loadlas(filepath,**kwargs):
    """
    Returns an instance of pphys.lasfile for the given filepath.
    
    Arguments:
        filepath {str} -- path to the given LAS file

    Keyword Arguments:
        homedir {str} -- path to the home (output) directory
        filedir {str} -- path to the file (input) directory
    
    Returns:
        pphys.lasfile -- an instance of pphys.lasfile filled with LAS file text.

    """

    # It creates an empty pphys.lasfile instance.
    nullfile = lasfile(filepath=filepath,**kwargs)

    # It reads LAS file and returns pphys.lasfile instance.
    fullfile = lasworm(nullfile).lasfile

    return fullfile

class lasworm():
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

        section = header(mnemonic=mnemonic,unit=unit,value=value,description=description)

        return section

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

        if not lasfile.isvalid(dataframe.running[0].vals):
            raise Warning("There are none depth values.")

        if not lasfile.ispositive(dataframe.running[0].vals):
            raise Warning("There are negative depth values.")

        if not lasfile.issorted(dataframe.running[0].vals):
            dataframe = dataframe.sort((dataframe.running[0].head,))

        return dataframe

class lasbatch(dirmaster):

    def __init__(self,filepaths=None,**kwargs):

        super().__init__(
            homedir = pop(kwargs,"homedir"),
            filedir = pop(kwargs,"filedir"))

        self.frames = []

        self.load(filepaths,**kwargs)

    def load(self,filepaths,**kwargs):

        if filepaths is None:
            return

        if not isinstance(filepaths,list) and not isinstance(filepaths,tuple):
            filepaths = (filepaths,)

        for filepath in filepaths:

            dataframe = loadlas(filepath,**kwargs)

            self.frames.append(dataframe)

            logging.info(f"Loaded {filepath} as expected.")

    def wells(self,idframes=None):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            dataframe = self.frames[index]

            print("\n\tWELL #{}".format(dataframe.well.get_row(mnemonic="WELL")["value"]))

            # iterator = zip(dataframe.well["mnemonic"],dataframe.well["units"],dataframe.well["value"],dataframe.well.descriptions)

            iterator = zip(*dataframe.well.get_columns())

            for mnem,unit,value,descr in iterator:
                print(f"{descr} ({mnem}):\t\t{value} [{unit}]")

    def curves(self,idframes=None,mnemonic_space=33,tab_space=8):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            dataframe = self.frames[index]

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
                depth = self.frames[fileIDs]["MD"]
            except KeyError:
                depth = self.frames[fileIDs]["DEPT"]

            xvals1 = self.frames[fileIDs][curveNames[0]]

            for curveName in curveNames[1:]:

                xvals2 = self.frames[fileIDs][curveName]

                xvals1[numpy.isnan(xvals1)] = xvals2[numpy.isnan(xvals1)]

            return depth,xvals1

        elif numpy.unique(numpy.array(fileIDs)).size==len(fileIDs):

            if isinstance(curveNames,str):
                curveNames = (curveNames,)*len(fileIDs)

            depth = numpy.array([])
            xvals = numpy.array([])

            for (fileID,curveName) in zip(fileIDs,curveNames):

                try:
                    depth_loc = self.frames[fileID]["MD"]
                except KeyError:
                    depth_loc = self.frames[fileID]["DEPT"]

                xvals_loc = self.frames[fileID][curveName]

                depth_loc = depth_loc[~numpy.isnan(xvals_loc)]
                xvals_loc = xvals_loc[~numpy.isnan(xvals_loc)]

                depth_max = 0 if depth.size==0 else depth.max()

                depth = numpy.append(depth,depth_loc[depth_loc>depth_max])
                xvals = numpy.append(xvals,xvals_loc[depth_loc>depth_max])

            return depth,xvals

class bulkmodel(header):

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

class depthview(dirmaster):

    def __init__(self,filepath,**kwargs):

        super().__init__(**kwargs)

        self.depths = {}
        self.axes = {}
        self.grids = {}

        self.curves = {}
        self.modules = []
        self.perfs = []
        self.casings = []

        self.lasfile = loadlas(filepath,**kwargs)

        self.set_depths()
        self.set_axes()
        self.set_grids()

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

        top = self.lasfile.depths.min()
        bottom = self.lasfile.depths.max()

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
    
    def set_axes(self,ncols=4,depth=1,legends='top'):
        """It sets the number of axes and maximum number of lines in the axes.

        ncols       : number of column axis including depth axis in the figure, integer
        depth       : index of depth axis, integer
        legends     : location of labels, top, bottom or None

        """

        self.axes['ncols'] = ncols
        self.axes['depth'] = depth

        self.axes['legends'] = legends.lower()

        if self.axes['legends'] is None:
            self.axes['nrows'] = 1
            self.axes['labels'] = slice(0)
            self.axes['curves'] = slice(ncols)
        elif self.axes['legends']=="top":
            self.axes['nrows'] = 2
            self.axes['labels'] = slice(0,ncols*2,2)
            self.axes['curves'] = slice(1,ncols*2,2)
        elif self.axes['legends']=="bottom":
            self.axes['nrows'] = 2
            self.axes['labels'] = slice(0,ncols*2,2)
            self.axes['curves'] = slice(1,ncols*2,2)
        else:
            raise ValueError(f"{legends} has not been defined! options: {{top,bottom}}")

        self.axes['xaxis'] = [{} for _ in range(ncols)]

        for index in range(self.axes['ncols']):
            self.set_xaxis(index)

    def set_xaxis(self,col,cycles=2,scale='linear',subs=None,subskip=None,subskip_left=0,subskip_right=0):

        if subskip is not None:
            subskip_left,subskip_right = subskip,subskip

        if col==self.axes['depth']:
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

    def set_grids(self,width=66,height=66,depth=6,label=6,nlabel=3,width_ratio=None,height_ratio=None):
        """It sets grid number for different elements in the axes.

        width        : grid number in the total width, integer
        height       : grid number in the total heigth, integer

        depth        : grid number in the width of depth xaxis, integer
        label        : grid number in the height of individual label, integer

        nlabel       : maximum number of curves in the axes, integer, nlabel*label defines
                       grid number in the height of labels

        width_ratio  : width ratio of column axes, tuple of integers

        height_ratio : height ratio of label and curve axes, tuple of integers

        """

        self.grids['width'] = width
        
        self.grids['height'] = height

        self.grids['size'] = (width,height)

        self.grids['depth'] = depth
        self.grids['label'] = label

        self.grids['nlabel'] = nlabel

        class ratio(): pass

        if width_ratio is None:

            if self.axes['ncols']<2:
                width_ratio = [width]

            elif self.axes['ncols']>1:
                naxis = self.axes['ncols']-1
                curve = (width-depth)//naxis
                extra = (width-depth)%naxis

                width_ratio = [curve+1 if i<extra else curve for i in range(naxis)]
                width_ratio = width_ratio[::-1]
                width_ratio.insert(self.axes['depth'],depth)

        ratio.width = tuple(width_ratio)

        if height_ratio is None:

            if self.axes['legends'] is None:
                height_ratio = [height]
            elif self.axes['legends'] == 'top':
                height_ratio = [nlabel*label,height-nlabel*label]
            elif self.axes['legends'] == 'bottom':
                height_ratio = [height-nlabel*label,nlabel*label]

        ratio.height = tuple(height_ratio)

        self.grids['ratio'] = ratio

    def set_curve(self,col,curve,multp=None,vmin=None,vmax=None,**kwargs):
        """It adds lascurve[head] to the axes[col]."""

        if isinstance(curve,str):
            curve = self.lasfile[curve]
            curve.set_style(**kwargs)
        elif not isinstance(curve,lascurve):
            curve = lascurve(curve,**kwargs)
        else:
            curve.set_style(**kwargs)
        
        curve.col = col

        if vmin is None:
            vmin = curve.min()
        
        if vmax is None:
            vmax = curve.max()

        curve.vmin = vmin
        curve.vmax = vmax

        curve.limit = (vmin,vmax)

        curve.multp = multp

        xaxis = self.axes['xaxis'][col]

        getattr(self,f"set_{xaxis['scale'][:3]}xaxis")(curve,xaxis)

        self.curves[curve.head] = curve

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
        """It adds perforation depths to the depth axis."""

        _perf = {}

        if col is None:
            col = self.axes['depth']

        _perf['col'] = col

        _perf['depth'] = depth

        for key,value in kwargs.items():
            _perf[key] = value

        self.perfs.append(_perf)

    def set_casing(self,depth,col=None,**kwargs):
        """It adds casing depths to the depth axis."""

        _casing = {}

        if col is None:
            col = self.axes['depth']

        _casing['col'] = col

        _casing['depth'] = depth

        for key,value in kwargs.items():
            _casing[key] = value

        self.casings.append(_casing)

    def view(self,top,wspace=0.0,hspace=0.0,height=30,**kwargs):

        if kwargs.get("figsize") is None:
            kwargs["figsize"] = (6.5,6)

        self.add_figure(**kwargs)

        self.add_axes()
        self.add_curves()
        self.add_modules()
        self.add_perfs()
        self.add_casings()

        self.gspecs.tight_layout(self.figure)

        self.gspecs.update(wspace=wspace,hspace=hspace)

        for index,axis in enumerate(self.figure.axes):
            if self.axes['legends'] is None:
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

        self.set_grids(label=4,**grids)

        if depths is not None:
            top,bottom = abs(min(depths)),abs(max(depths))
            depths = (bottom,top)
            top,bottom = min(depths),max(depths)
            height_total = bottom-top
        else:
            height_total = self.depths['height']
            top,bottom = self.depths['top'],self.depths['bottom']

        height_pages = self.grids['curves']

        self.page['depth'].number = -(-height_total//height_pages)

        self.page['depth'].limits = []

        while top<bottom:
            self.page['depth'].limits.append(top,top+height_pages)
            top += height_pages

    def save(self,filepath,wspace=0.0,hspace=0.0,**kwargs):
        """It saves the depthview as a multipage pdf file."""

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
                    if self.axes['legends'] is None:
                        axis.set_ylim(limit)
                    elif index%2==1:
                        axis.set_ylim(limit)

                pdf.savefig()

    def add_figure(self,**kwargs):

        self.figure = pyplot.figure(**kwargs)

        self.gspecs = gridspec.GridSpec(
            nrows = self.axes['nrows'],
            ncols = self.axes['ncols'],
            figure = self.figure,
            width_ratios = self.grids['ratio'].width,
            height_ratios = self.grids['ratio'].height)

    def add_axes(self):

        for index in range(self.axes['ncols']):

            xaxis = self.axes['xaxis'][index]

            yaxis = self.depths

            if self.axes['legends'] is None:
                curve_axis = self.figure.add_subplot(self.gspecs[index])
            elif self.axes['legends'] == "top":
                label_axis = self.figure.add_subplot(self.gspecs[0,index])
                curve_axis = self.figure.add_subplot(self.gspecs[1,index])
            elif self.axes['legends'] == "bottom":
                label_axis = self.figure.add_subplot(self.gspecs[1,index])
                curve_axis = self.figure.add_subplot(self.gspecs[0,index])

            if self.axes['legends'] is not None:
                xlim,ylim = (0,1),(0,self.grids['nlabel'])
                self.set_axislabel(label_axis,xlim,ylim)

            if index != self.axes['depth']:
                self.set_yaxiscurve(curve_axis,yaxis)
                self.set_xaxiscurve(curve_axis,xaxis)
            else:
                self.set_axisdepth(curve_axis,xaxis,yaxis)

    def add_curves(self):

        label_axes = self.figure.axes[self.axes['labels']]
        curve_axes = self.figure.axes[self.axes['curves']]

        for _,curve in self.curves.items():

            label_axis = label_axes[curve.col]
            curve_axis = curve_axes[curve.col]

            curve_axis.plot(curve.xaxis,curve.depths,
                color = curve.color,
                linestyle = curve.style,
                linewidth = curve.width,)

            row = len(curve_axis.lines)

            if not hasattr(curve,"row"):
                curve.row = row

            self.set_labelcurve(label_axis,curve)

    def add_modules(self):

        for module in self.modules:

            curve_axis = self.figure.axes[module['index']*2+1]
            label_axis = self.figure.axes[module['index']*2]

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

            curve_axis.fill_betweenx(yvals,xvals,x2=x2,facecolor=module["fillcolor"],hatch=module["hatch"])

            module['row'] = len(lines)

            self.set_labelmodule(label_axis,module)

    def add_perfs(self):

        curve_axes = self.figure.axes[self.axes['curves']]

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
        """It includes casing set depths"""

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
            fill=True,facecolor=module["fillcolor"],hatch=module["hatch"])

        axis.add_patch(rect)

        axis.text(0.5,module['row']+0.5,module["head"],
            horizontalalignment='center',
            verticalalignment='center',
            backgroundcolor='white',
            fontsize='small',)

class batchview():
    """It creates correlation based on multiple las files from different wells."""

    def __init__(self):

        pass

if __name__ == "__main__":

    bm = bulkmodel(sandstone=1)

    for key in bm.library.keys():
        print(key)

    # for item in bm.library:
    #     print(item)