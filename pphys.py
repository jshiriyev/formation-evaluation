import copy

import io

import re

import tkinter

from matplotlib import colors as mcolors
from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import transforms

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

from datum import frame
from datum import column

from textio import header
from textio import dirmaster

from cypy.vectorpy import strtype

class lasfile(dirmaster):

    def __init__(self,**kwargs):

        homedir = kwargs.get("homedir")
        filedir = kwargs.get("filedir")

        filepath = kwargs.get("filepath")

        if homedir is not None:
            kwargs.pop("homedir")

        if filedir is not None:
            kwargs.pop("filedir")

        if filepath is not None:
            kwargs.pop("filepath")

        super().__init__(homedir=homedir,filedir=filedir,filepath=filepath)

        self.sections = []

    def _version(self,mnemonic,unit,value,description):

        self.sections.append("version")

        self.version = header(mnemonic=mnemonic,unit=unit,value=value,description=description)

    def _well(self,mnemonic,unit,value,description):

        self.sections.append("well")

        self.well = header(mnemonic=mnemonic,unit=unit,value=value,description=description)

    def _parameter(self,mnemonic,unit,value,description):

        self.sections.append("parameter")

        self.parameter = header(mnemonic=mnemonic,unit=unit,value=value,description=description)

    def _curve(self,mnemonic,unit,value,description):

        self.sections.append("curve")

        self.curve = header(mnemonic=mnemonic,unit=unit,value=value,description=description)

    def _ascii(self,*args,**kwargs):

        self.sections.append("ascii")

        self.ascii = frame(*args,**kwargs)

    def write(self,filepath,mnemonics,data,units=None,descriptions=None,values=None):

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

    def issorted(self):

        depths_ = self.ascii.running[0].vals

        return lasfile._issorted(depths_)

    @staticmethod
    def _issorted(depths):

        if numpy.all(depths[:-1]<depths[1:]):
            return True
        else:
            return False

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

    def depths(self,top,bottom,curve=None):

        depth = self.ascii.running[0].vals

        conds = numpy.logical_and(depth>=top,depth<=bottom)

        if curve is None:
            dataframe = copy.deepcopy(self.ascii)
            return dataframe[conds]

        else:
            datacolumn = copy.deepcopy(self.ascii[curve])
            return datacolumn[conds]

    def resample(self,depths1,curve=None):
        """Resamples the frame data based on given depths1."""

        """
        depths1 :   The depth values where new curve data will be calculated;
        curve   :   The head of curve to resample; If None, all curves in the file will be resampled;

        """

        depths0 = self.ascii.running[0].vals

        if curve is not None:
            values0 = self.ascii[curve].vals

            datacolumn = copy.deepcopy(self.ascii[curve])
            datacolumn.vals = lasfile._resample(depths1,depths0,values0)
            
            return datacolumn

        if not lasfile._issorted(depths1):
            raise ValueError("Input depths are not sorted.")

        outers_above = depths1<depths0.min()
        outers_below = depths1>depths0.max()

        inners = numpy.logical_and(~outers_above,~outers_below)

        depths1_inners_ = depths1[inners]

        lowers = numpy.empty(depths1_inners_.shape,dtype=int)
        uppers = numpy.empty(depths1_inners_.shape,dtype=int)

        lower = 0
        upper = 0

        for index,depth in enumerate(depths1_inners_):

            while depth>depths0[lower]:
                lower += 1

            while depth>depths0[upper]:
                upper += 1

            lowers[index] = lower-1
            uppers[index] = upper

        delta_depths1 = depths1_inners_-depths0[lowers]
        delta_depths0 = depths0[uppers]-depths0[lowers]

        grads = delta_depths1/delta_depths0

        dataframe = copy.deepcopy(self.ascii)

        for index,datacolumn in enumerate(self.ascii.running):

            if index==0:
                dataframe[datacolumn.head].vals = depths1
                continue

            delta_values = datacolumn.vals[uppers]-datacolumn.vals[lowers]

            dataframe[datacolumn.head].vals = numpy.empty(depths1.shape,dtype=float)

            dataframe[datacolumn.head].vals[outers_above] = numpy.nan
            dataframe[datacolumn.head].vals[inners] = datacolumn.vals[lowers]+grads*(delta_values)
            dataframe[datacolumn.head].vals[outers_below] = numpy.nan

        return dataframe

    @staticmethod
    def _resample(depths1,depths0,values0):

        """
        depths1 :   The depths where new curve values will be calculated;
        depths0 :   The depths where the values are available;
        values0 :   The values to be resampled;

        """

        if not lasfile._issorted(depths1):
            raise ValueError("Input depths are not sorted.")

        outers_above = depths1<depths0.min()
        outers_below = depths1>depths0.max()

        inners = numpy.logical_and(~outers_above,~outers_below)

        depths1_inners_ = depths1[inners]

        lowers = numpy.empty(depths1_inners_.shape,dtype=int)
        uppers = numpy.empty(depths1_inners_.shape,dtype=int)

        lower,upper = 0,0

        for index,depth in enumerate(depths1_inners_):

            while depth>depths0[lower]:
                lower += 1

            while depth>depths0[upper]:
                upper += 1

            lowers[index] = lower-1
            uppers[index] = upper

            # diff = depths0-depth
            # lowers[index] = numpy.where(diff<0,diff,-numpy.inf).argmax()
            # uppers[index] = numpy.where(diff>0,diff,+numpy.inf).argmin()

        delta_depths1 = depths1_inners_-depths0[lowers]
        delta_depths0 = depths0[uppers]-depths0[lowers]
        delta_values0 = values0[uppers]-values0[lowers]

        grads = delta_depths1/delta_depths0

        values = numpy.empty(depths1.shape,dtype=float)

        values[outers_above] = numpy.nan
        values[inners] = values0[lowers]+grads*(delta_values0)
        values[outers_below] = numpy.nan

        return values

class loadlas(lasfile):

    def __init__(self,filepath,homedir=None,filedir=None):

        super().__init__(homedir=homedir,filedir=filedir,filepath=filepath)

        with open(self.filepath,"r",encoding="latin1") as lasmaster:
            dataframe = self.text(lasmaster)

        self.ascii = dataframe

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

                self.sections.append(sectionhead)

                setattr(self,sectionhead,sectionbody)

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

        value_null = float(self.well['NULL'].value)

        dtypes = [numpy.dtype(type_) for type_ in types]

        floatFlags = [True if type_ is float else False for type_ in types]

        lasmaster.seek(0)

        self._seeksection(lasmaster,section="~A")

        if all(floatFlags):
            cols = numpy.loadtxt(lasmaster,comments="#",unpack=True,encoding="latin1")
        else:
            cols = numpy.loadtxt(lasmaster,comments="#",unpack=True,encoding="latin1",dtype='str')

        iterator = zip(cols,self.curve.mnemonic,self.curve.unit,self.curve.description,dtypes)

        running = []

        for vals,head,unit,info,dtype in iterator:

            if dtype.type is numpy.dtype('float').type:
                vals[vals==value_null] = numpy.nan

            datacolumn = column(vals,head=head,unit=unit,info=info,dtype=dtype)

            running.append(datacolumn)

        dataframe = frame(*running)

        if not lasfile._issorted(dataframe.running[0].vals):
            dataframe = dataframe.sort((dataframe.running[0].head,))

        return dataframe

class colors():

    def __init__(self,**kwargs):

        self.SH         = ("Shale","gray",'--')
        self.clean      = ("Clean Formation","navajowhite",'||')
        self.SS         = ("Sandstone","gold","..")
        self.SSH        = ("Shaly Sandstone","gold",'..--')
        self.LS         = ("Limestone","tan","\\\\")
        self.DOL        = ("Dolomite","darkkhaki","//")
        self.PV         = ("Pore Volume","white","OO")

        self.liquid     = ("Liquid","blue","OO")
        self.water      = ("Water","steelblue","OO")
        self.waterCLAY  = ("Water Clay Bound","lightskyblue","XX")
        self.waterCAP   = ("Water Capillary Bound","lightsteelblue","XX")
        self.waterIRRE  = ("Water Irreducible","lightblue","XX")
        self.waterM     = ("Water Movable","aqua",'..')
        self.fluidM     = ("Fluid Movable","teal",'..')

        self.HC         = ("Hydrocarbon","green",'OO')
        self.gas        = ("Gas","lightcoral","OO")
        self.gasR       = ("Gas Residual","indianred",'XX')
        self.gasM       = ("Gas Movable","red",'..')
        self.GC         = ("Condensate","firebrick","OO.")
        self.oil        = ("Oil","seagreen",'OO')
        self.oilR       = ("Oil Residual","forestgreen",'XX')
        self.oilM       = ("Oil Movable","limegreen",'..')
        
        self.set_colors(**kwargs)

    def set_colors(self,**kwargs):

        for key,value in kwargs.items():

            try:
                mcolors.to_rgba(value)
            except ValueError:
                raise ValueError(f"Invalid RGBA argument: '{value}'")

            getattr(self,key)[1] = value

    def set_hatches(self,**kwargs):

        for key,value in kwargs.items():

            getattr(self,key)[2] = value

    def view(self,axis,nrows=(7,7,8),ncols=3,fontsize=10,sizes=(8,5),dpi=100):

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

    @property
    def items(self):
        return list(self.__dict__.keys())
    
    @property
    def names(self):
        return [value[0] for key,value in self.__dict__.items()]

    @property
    def colors(self):
        return [value[1] for key,value in self.__dict__.items()]

    @property
    def hatches(self):
        return [value[2] for key,value in self.__dict__.items()]

class depthview():

    def __init__(self,page_format="Letter"):

        if page_format == "A4":
            figsize = (8.3,11.7)
        elif page_format == "Letter":
            figsize = (8.5,11.0)

        self.figure = pyplot.figure(figsize=figsize,dpi=100)
        
    def set_axes(self,naxes,ncurves_max=3,label_loc=None):

        # naxes shows the number of column axis in the figure, integer
        # ncurves_max shows the maximum number of curves in the axes, integer

        if naxes == 1:
            depth_column = 0
            width_ratios = [1,10]
        elif naxes == 2:
            depth_column = 1
            width_ratios = [10,3,20]
        elif naxes == 3:
            depth_column = 1
            width_ratios = [10,3,10,10]
        elif naxes == 4:
            depth_column = 1
            width_ratios = [5,2,5,5,5]
        elif naxes == 5:
            depth_column = 1
            width_ratios = [2,1,2,2,2,2]
        elif naxes == 6:
            depth_column = 1
            width_ratios = [5,3,5,5,5,5,5]
        else:
            raise ValueError("Maximum number of columns is 6!")

        self.depth_column = depth_column

        numcols = naxes+1

        if label_loc is None:
            numrows = 1
            height_ratios = None
            index = 0
        elif label_loc == "top":
            numrows = 2
            height_ratios = [ncurves_max,19-ncurves_max]
            index = 1
        elif label_loc == "bottom":
            numrows = 2
            height_ratios = [19-ncurves_max,ncurves_max]
            index = 0
        else:
            raise ValueError("The location of box can be top, bottom or None!")

        self.gspecs = gridspec.GridSpec(
            nrows=numrows,ncols=numcols,
            width_ratios=width_ratios,
            height_ratios=height_ratios)

        self.axes_curve = []
        self.axes_label = []

        for i in range(numcols):

            curve_axis = self.figure.add_subplot(self.gspecs[1,i])
            label_axis = self.figure.add_subplot(self.gspecs[0,i])

            if i != depth_column:
                curve_axis = self._set_curveaxis(curve_axis)  
            else:
                curve_axis = self._set_depthaxis(curve_axis)

            label_axis = self._set_labelaxis(label_axis,ncurves_max)

            curve_axis.multipliers = []

            self.axes_curve.append(curve_axis)
            self.axes_label.append(label_axis)

    def set_xcycles(self,index,cycles=2,subskip=0,scale='linear'):

        axis = self.axes_curve[index]

        if scale=="linear":
            xlim = (0+subskip,10*cycles+subskip)
        elif scale=="log":
            xlim = ((subskip+1)*10**0,(subskip+1)*10**cycles)
        else:
            raise ValueError(f"{scale} has not been defined! options: {{linear,log}}")

        axis.set_xlim(xlim)

        axis.set_xscale(scale)

        if scale=="linear":
            axis.xaxis.set_minor_locator(MultipleLocator(1))
            axis.xaxis.set_major_locator(MultipleLocator(10))
        elif scale=="log":
            axis.xaxis.set_minor_locator(LogLocator(base=10,subs=range(1,10),numticks=12))
            axis.xaxis.set_major_locator(LogLocator(base=10,numticks=12))
        else:
            raise ValueError(f"{scale} has not been defined! options: {{linear,log}}")

    def set_ycycles(self,cycles,subskip=0):

        ylim = (10*cycles+subskip,0+subskip)

        for axis in self.axes_curve:
            axis.set_ylim(ylim)

    def _set_curveaxis(self,axis,xscale='linear',xcycles=2,xsubkip=0,ycycles=7,ysubskip=0):

        if xscale=="linear":
            xlim = (0+xsubkip,10*xcycles+xsubkip)
        elif xscale=="log":
            xlim = (1*(xsubkip+1),(xsubkip+1)*10**xcycles)
        else:
            raise ValueError(f"{xscale} has not been defined! options: {{linear,log}}")

        ylim = (10*ycycles+ysubskip,0+ysubskip)

        axis.set_xlim(xlim)
        axis.set_ylim(ylim)

        axis.set_xscale(xscale)

        if xscale=="linear":
            axis.xaxis.set_minor_locator(MultipleLocator(1))
            axis.xaxis.set_major_locator(MultipleLocator(10))
        elif xscale=="log":
            axis.xaxis.set_minor_locator(LogLocator(base=10,subs=range(1,10),numticks=12))
            axis.xaxis.set_major_locator(LogLocator(base=10,numticks=12))
        else:
            raise ValueError(f"{xscale} has not been defined! options: {{linear,log}}")

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.tick_params(axis="x",which="minor",bottom=False)

        axis.grid(axis="x",which='minor',color='k',alpha=0.4)
        axis.grid(axis="x",which='major',color='k',alpha=0.9)

        axis.yaxis.set_minor_locator(MultipleLocator(1))
        axis.yaxis.set_major_locator(MultipleLocator(10))

        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        axis.tick_params(axis="y",which="minor",left=False)

        axis.grid(axis="y",which='minor',color='k',alpha=0.4)
        axis.grid(axis="y",which='major',color='k',alpha=0.9)

        return axis

    def _set_depthaxis(self,axis,cycles=7,subskip=0):

        xlim = (0,1)
        ylim = (10*cycles+subskip,0+subskip)
        
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.yaxis.set_minor_locator(MultipleLocator(1))
        axis.yaxis.set_major_locator(MultipleLocator(10))
        
        axis.tick_params(
            axis="y",which="both",direction="in",right=True,pad=-40)

        pyplot.setp(axis.get_yticklabels(),visible=False)

        return axis

    def _set_labelaxis(self,axis,ncurves_max):

        axis.set_xlim((0,1))
        axis.set_ylim((0,ncurves_max+1))

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)
        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        return axis

    def add_depth(self,depth,**kwargs):

        axis = self.axes_curve[self.depth_column]

        self.yvals,ylim,_ = self._get_linear_normalized(depth,axis.get_ylim(),multp=1,**kwargs)

        axis_yticks = axis.get_yticks()

        calc_yticks = MultipleLocator(base=10).tick_values(*ylim)

        for axis_ytick,calc_ytick in zip(axis_yticks[2:-2],calc_yticks[2:-2]):

            axis.text(0.5,axis_ytick,calc_ytick,
                horizontalalignment='center',
                verticalalignment='center',
                backgroundcolor='white',
                fontsize='small',)

    def add_curve(self,index,curve,**kwargs):

        curve_axis = self.axes_curve[index]
        label_axis = self.axes_label[index]

        xlim = curve_axis.get_xlim()

        xscale = curve_axis.get_xscale()

        if xscale == "linear":
            xvals,xlim,multp = self._get_linear_normalized(curve.vals,xlim,**kwargs)
        elif xscale == "log":
            xvals,xlim,multp = self._get_log_normalized(curve.vals,xlim,**kwargs)
        else:
            raise ValueError(f"{xscale} has not been defined! options: {{linear,log}}")

        curve_axis.plot(xvals,self.yvals,
            color=curve.linecolor,linestyle=curve.linestyle,linewidth=curve.linewidth)

        if curve.fill:
            curve_axis.fill_betweenx(self.yvals,xvals,x2=0,facecolor=curve.fillfacecolor,hatch=curve.fillhatch)

        numlines = len(curve_axis.lines)

        try:
            curve_axis.multipliers[numlines-1] = multp
        except IndexError:
            curve_axis.multipliers.append(multp)

        if curve.fill:
            self._add_label_fill(label_axis,curve,xlim,numlines)
        else:
            self._add_label_line(label_axis,curve,xlim,numlines)

    def _get_linear_normalized(self,values,alim,multp=None,vmin=None,vmax=None):

        amin,amax = min(alim),max(alim)

        if vmin is None:
            vmin = values.min()
        
        if vmax is None:
            vmax = values.max()

        # print(f"{amin=},",f"{amax=}")
        # print(f"given_{vmin=},",f"given_{vmax=}")

        delta_axis = numpy.abs(amax-amin)
        delta_vals = numpy.abs(vmax-vmin)

        delta_powr = -numpy.floor(numpy.log10(delta_vals))

        # print(f"{delta_powr=}")

        vmin = numpy.floor(vmin*10**delta_powr)/10**delta_powr

        vmax_temp = numpy.ceil(vmax*10**delta_powr)/10**delta_powr

        # print(f"{vmin=},",f"{vmax_temp=}")

        if multp is None:

            multp_temp = (vmax_temp-vmin)/(delta_axis)
            multp_powr = -numpy.floor(numpy.log10(multp_temp))

            # print(f"{multp_temp=},")

            multp = numpy.ceil(multp_temp*10**multp_powr)/10**multp_powr

            # print(f"{multp=},")
        
        axis_vals = amin+(values-vmin)/multp

        vmax = delta_axis*multp+vmin
        
        # print(f"normalized_{vmin=},",f"normalized_{vmax=}")

        return axis_vals,(vmin,vmax),multp

    def _get_log_normalized(self,values,alim,multp=None,vmin=None):
        
        if vmin is None:
            vmin = values.min()

        if multp is None:
            multp = numpy.ceil(numpy.log10(1/vmin))

        axis_vals = values*10**multp

        vmin = min(alim)/10**multp
        vmax = max(alim)/10**multp

        return axis_vals,(vmin,vmax),multp

    def _add_label_line(self,label_axis,curve,xlim,numlines=0):

        label_axis.plot((0,1),(numlines-0.7,numlines-0.7),
            color=curve.linecolor,linestyle=curve.linestyle,linewidth=curve.linewidth)

        label_axis.text(0.5,numlines-0.5,f"{curve.head} [{curve.unit}]",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        label_axis.text(0.02,numlines-0.5,f'{xlim[0]:.5g}',horizontalalignment='left')
        label_axis.text(0.98,numlines-0.5,f'{xlim[1]:.5g}',horizontalalignment='right')

    def _add_label_fill(self,label_axis,curve,xlim,numlines=0):

        rect = Rectangle((0,numlines-1),1,1,
            fill=True,facecolor=curve.fillfacecolor,hatch=curve.fillhatch)

        label_axis.add_patch(rect)

        label_axis.text(0.5,numlines-0.5,curve.head,
            horizontalalignment='center',
            verticalalignment='center',
            backgroundcolor='white',
            fontsize='small',)

    def show(self,filename=None,wspace=0.0,hspace=0.0):

        self.gspecs.tight_layout(self.figure)

        self.gspecs.update(wspace=wspace,hspace=hspace)

        if filename is not None:
            self.figure.savefig(filename,format='pdf')

        pyplot.show()

class DepthView(): #Will BE DEPRECIATED

    def __init__(self,root):
        """It initializes the DepthView with listbox and figure canvas."""

        self.root = root

        self.root.title("Well Logs - Depth View")

        self.header = tkinter.Canvas(self.root,height=200)
        self.header.grid(row=0,column=0,sticky=tkinter.EW)

        self.canvas = tkinter.Canvas(self.root)
        self.canvas.grid(row=1,column=0,sticky=tkinter.NSEW)

        # self.hscroll = tkinter.Scrollbar(self.root,orient=tkinter.HORIZONTAL)
        # self.hscroll.grid(row=2,column=0,sticky=tkinter.EW)

        self.vscroll = tkinter.Scrollbar(self.root,orient=tkinter.VERTICAL)
        self.vscroll.grid(row=0,column=1,rowspan=2,sticky=tkinter.NS)

        self.root.rowconfigure(0,weight=0)
        self.root.rowconfigure(1,weight=1)
        # self.root.rowconfigure(2,weight=0)

        self.root.columnconfigure(0,weight=1)
        self.root.columnconfigure(1,weight=0)

        # self.canvas.config(xscrollcommand=self.hscroll.set)
        self.canvas.config(yscrollcommand=self.vscroll.set)

        # self.hscroll.config(command=self.canvas.xview)
        self.vscroll.config(command=self.canvas.yview)

        self.canvas.configure(bg='blue')

        self.canvas.bind_all("<MouseWheel>",self._on_mousewheel)

        # The colors to be used for lines

        # self.colors = ("black","crimson","blue","sienna")
        self.colors = pyplot.rcParams['axes.prop_cycle'].by_key()['color']
        # self.colors.insert(0,"#000000")

    def set_header(self,nrows=(1,3,2,2),ncols=4,fontsize=10,width=3.,height=2.,dpi=100.):

        fig = pyplot.figure(dpi=dpi)

        fig.set_figwidth(width*4)
        fig.set_figheight(height)

        axis = fig.add_subplot(111)

        X,Y = [dpi*size for size in (width*ncols,height)]

        w = X/ncols
        h = Y/(max(nrows)+1)

        names = ["Vsh","NGL","PHIT","PHIE","CBW","BVW","RL8","RL4"]

        # colors = self.colors
        # hatches = self.hatches

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

                axis.add_patch(Rectangle((xmin,ymin),0.8*w,0.7*h,fill=True)
                    ) #fill=True,hatch=hatches[k],facecolor=colors[k]

                k += 1

        axis.set_xlim(0,X)
        axis.set_ylim(0,Y)

        axis.set_axis_off()

        buff = io.BytesIO()

        fig.savefig(buff,format='png')

        buff.seek(0)

        image = ImageTk.PhotoImage(Image.open(buff))

        self.header.create_image(0,0,anchor=tkinter.N,image=image)

    def set_axes(self,numaxes=1,subaxes=None,depth=None,inchdepth=15.,width=3.,height=128.,dpi=100.):
        """Creates the figure and axes and their sub-axes and stores them in the self.axes."""

        # numaxes   : integer
        #            Number of axes in the figure

        # subaxes   : list or tuple of integers
        #            Number of subaxes in each axis

        # depth     : float
        #            Depth of log in meters; every inch will represent inchdepth meter of formation
        #            Default value for inchdepth is 15 meters.

        # inchdepth : float
        #            The depth (meters) to be shown in every inch of the figure

        # width     : float
        #            Width of each axis in inches

        # height    : float
        #            Height of figure in inches

        # dpi       : integer
        #            Resolution of the figure, dots per inches

        self.figure = pyplot.figure(dpi=dpi)

        self.figure.set_figwidth(width*numaxes)

        if depth is None:
            self.figure.set_figheight(height)
        else:
            self.figure.set_figheight(depth/inchdepth)

        self.fgspec = gridspec.GridSpec(1,numaxes)

        self.axes = []

        if subaxes is None:
            subaxes = (1,)*numaxes
        elif not hasattr(subaxes,"__len__"):
            logging.warning(f"Expected subaxes is a list or tuple with the length equal to numaxes; input is {type(subaxes)}")
        elif len(subaxes)!=numaxes:
            logging.warning(f"The length of subaxes should be equal to numaxes; {len(subaxes)} not equal to {numaxes=}")

        for idaxis in range(numaxes):
            self.add_axis(idaxis,subaxes[idaxis])

    def add_axis(self,idaxis,numsubaxes=1):
        """Adds main-axis and its subaxes to the list of self.axes."""

        subaxes = []

        subaxis_main = pyplot.subplot(self.fgspec[idaxis])

        xlims = (0,1)

        ylims = (0,1)

        subaxis_main.set_xticks(numpy.linspace(*xlims,11))
        subaxis_main.set_yticks(ylims)

        subaxis_main.set_ylim(ylims[::-1])

        subaxis_main.yaxis.set_minor_locator(AutoMinorLocator(25))

        subaxis_main.grid(True,which="both",axis='y')

        subaxis_main.grid(True,which="major",axis='x')

        pyplot.setp(subaxis_main.get_xticklabels(),visible=False)
        pyplot.setp(subaxis_main.get_xticklines(),visible=False)

        # pyplot.setp(subaxis_main.xaxis.get_minorticklabels(),visible=False)
        # pyplot.setp(subaxis_main.xaxis.get_minorticklines(),visible=False)

        pyplot.setp(subaxis_main.yaxis.get_minorticklines(),visible=False)
        # subaxis_main.tick_params(axis='y',which='major',length=0)

        if idaxis>0:
            pyplot.setp(subaxis_main.get_yticklabels(),visible=False)

        subaxes.append(subaxis_main)

        self.axes.append(subaxes)

        self.set_subaxes(idaxis,numsubaxes)

    def set_subaxes(self,idaxis,numsubaxes):
        """Creates subaxes and stores them in self.axes."""

        numsubaxes_current = len(self.axes[idaxis])-1

        if numsubaxes_current>=numsubaxes:
            return

        roofpos = 1+0.4*numsubaxes/self.figure.get_figheight()

        self.axes[idaxis][0].spines["top"].set_position(("axes",roofpos))

        for idline in range(numsubaxes_current,numsubaxes):
            self.add_subaxis(idaxis,idline)

    def add_subaxis(self,idaxis,idline):
        """Adds subaxis to the self.axes."""

        axsub = self.axes[idaxis][0].twiny()

        axsub.set_xticks((0.,1.))
        axsub.set_ylim(self.axes[0][0].get_ylim())

        spinepos = 1+0.4*idline/self.figure.get_figheight()

        axsub.spines["top"].set_position(("axes",spinepos))
        axsub.spines["top"].set_color(self.colors[idline])

        axsub.spines["left"].set_visible(False)
        axsub.spines["right"].set_visible(False)
        axsub.spines["bottom"].set_visible(False)

        axsub.tick_params(axis='x',labelcolor=self.colors[idline])

        # self.axes[idaxis][0].yaxis.set_minor_locator(AutoMinorLocator(25))

        # self.axes[idaxis][0].grid(True,which="both",axis='y')

        pyplot.setp(self.axes[idaxis][0].get_xticklabels(),visible=False)
        pyplot.setp(self.axes[idaxis][0].get_xticklines(),visible=False)

        axsub.LineExistFlag = False

        self.set_xaxis(axsub)

        self.axes[idaxis].append(axsub)

    def set_depth(self,depth=None):
        """It will check the depths of axis and set depth which include all depths."""

        for axis in self.axes:
            for axsub in axis:
                axsub.set_ylim(self.axes[0][0].get_ylim())

            # axis[0].yaxis.set_minor_locator(AutoMinorLocator(25))
            # axis[0].grid(True,which="both",axis='y')

    def set_xaxis(self,axis):

        pyplot.setp(axis.xaxis.get_majorticklabels()[1:-1],visible=False)

        pyplot.setp(axis.xaxis.get_majorticklabels()[0],ha="left")
        pyplot.setp(axis.xaxis.get_majorticklabels()[-1],ha="right")

        if not axis.LineExistFlag:

            loffset = transforms.ScaledTranslation(5/72,-5/72,self.figure.dpi_scale_trans)
            
            ltrans = axis.xaxis.get_majorticklabels()[0].get_transform()

            axis.xaxis.get_majorticklabels()[0].set_transform(ltrans+loffset)

            roffset = transforms.ScaledTranslation(-5/72,-5/72,self.figure.dpi_scale_trans)

            rtrans = axis.xaxis.get_majorticklabels()[-1].get_transform()

            axis.xaxis.get_majorticklabels()[-1].set_transform(rtrans+roffset)

        else:

            roffset = transforms.ScaledTranslation(-10/72,0,self.figure.dpi_scale_trans)

            rtrans = axis.xaxis.get_majorticklabels()[-1].get_transform()

            axis.xaxis.get_majorticklabels()[-1].set_transform(rtrans+roffset)

        pyplot.setp(axis.xaxis.get_majorticklines()[2:-1],visible=False)

        pyplot.setp(axis.xaxis.get_majorticklines()[1],markersize=25)
        pyplot.setp(axis.xaxis.get_majorticklines()[-1],markersize=25)

        # axis.xaxis.get_majorticklines()[0].set_markersize(100)

    def set_lines(self,idaxis,idline,xcol,ycol):

        axis = self.axes[idaxis][idline+1]

        axis.plot(xcol.vals,ycol.vals,color=self.colors[idline])

        axis.LineExistFlag = True

        yticks = self.get_yticks(ycol.vals)
        xticks = self.get_xticks(xcol.vals)

        axis.set_xlabel(xcol.head)

        # figheight_temp = (yticks.max()-yticks.min())/128

        # if figheight_temp>self.figure.get_figheight():
        #   self.figure.set_figheight(figheight_temp)

        # figheight = max(self.figure.get_figheight(),figheight_temp)

        axis.set_ylim((yticks.max(),yticks.min()))
        axis.set_yticks(yticks)

        axis.set_xlim((xticks.min(),xticks.max()))
        axis.set_xticks(xticks)

        self.set_xaxis(axis)

        # axis.grid(True,which="both",axis='y')

        # axis.yaxis.set_minor_locator(AutoMinorLocator(10))

        # if idline==0:
            # axis.grid(True,which="major",axis='x')

        # axis.xaxis.set_major_formatter(ScalarFormatter())
        # # axis.xaxis.set_major_formatter(LogFormatter())

    def set_image(self):
        """Creates the image of figure in memory and displays it on canvas."""

        self.fgspec.tight_layout(self.figure,rect=[0,0,1.0,0.995])
        self.fgspec.update(wspace=0)

        buff = io.BytesIO()

        self.figure.savefig(buff,format='png')

        buff.seek(0)

        self.image = ImageTk.PhotoImage(Image.open(buff))

        self.canvas.create_image(0,0,anchor=tkinter.N,image=self.image)

        self.canvas.config(scrollregion=self.canvas.bbox('all'))

    def get_xticks(self,xvals,xmin=None,xmax=None,xscale="normal",xdelta=None,xdelta_count=11):

        xvals_min = numpy.nanmin(xvals)

        if xvals_min is numpy.nan:
            xvals_min = 0.

        xvals_max = numpy.nanmax(xvals)

        if xvals_max is numpy.nan:
            xvals_max= 1.

        xrange_given = xvals_max-xvals_min

        if xdelta is None:
            xdelta = xrange_given/(xdelta_count-1)

        beforeDot,afterDot = format(xdelta,'f').split('.')

        nondim_xunit_sizes = numpy.array([1,2,4,5,10])

        if xdelta>1:

            xdelta_temp = xdelta/10**(len(beforeDot)-1)
            xdelta_temp = nondim_xunit_sizes[(numpy.abs(nondim_xunit_sizes-xdelta_temp)).argmin()]

            xdelta = xdelta_temp*10**(len(beforeDot)-1)

        else:

            zeroCountAfterDot = len(afterDot)-len(afterDot.lstrip('0'))

            xdelta_temp = xdelta*10**(zeroCountAfterDot+1)
            xdelta_temp = nondim_xunit_sizes[(numpy.abs(nondim_xunit_sizes-xdelta_temp)).argmin()]

            xdelta = xdelta_temp/10**(zeroCountAfterDot+1)

        if xscale=="normal":

            if xmin is None:
                xmin = (numpy.floor(xvals_min/xdelta)-1).astype(float)*xdelta

            if xmax is None:
                xmax = (numpy.ceil(xvals_max/xdelta)+1).astype(float)*xdelta

            xticks = numpy.arange(xmin,xmax+xdelta/2,xdelta)

        elif xscale=="log":

            if xmin is None:
                xmin = xvals_min if xvals_min>0 else 0.001

            if xmax is None:
                xmax = xvals_max if xvals_max>0 else 0.1

            xmin_power = numpy.floor(numpy.log10(xmin))
            xmax_power = numpy.ceil(numpy.log10(xmax))

            xticks = 10**numpy.arange(xmin_power,xmax_power+1/2)

        return xticks

    def get_yticks(self,yvals=None,top=None,bottom=None,endmultiple=5.,ydelta=25.):

        if yvals is None:
            yvals = numpy.array([0,1])

        if top is None:
            top = numpy.nanmin(yvals)

        if bottom is None:
            bottom = numpy.nanmax(yvals)

        if top>bottom:
            top,bottom = bottom,top

        ymin = numpy.floor(top/endmultiple)*endmultiple

        ymax = numpy.ceil(bottom/endmultiple)*endmultiple

        yticks = numpy.arange(ymin,ymax+ydelta/2,ydelta)

        return yticks

    def set_DepthViewGRcut(self,GRline,indexI,indexJ,perc_cut=40):

        # indexI index of GR containing axis in the plot
        # indexJ index of GR containing line in the axis

        try:
            depth = self.frames[GRline[0]].columns("MD")
        except ValueError:
            depth = self.frames[GRline[0]].columns("DEPT")

        xvals = self.frames[GRline[0]].columns(GRline[1])

        GRmin = numpy.nanmin(xvals)
        GRmax = numpy.nanmax(xvals)

        GRcut = (GRmin+(GRmax-GRmin)*perc_cut/100)

        cut_line = GRcut*numpy.ones(depth.shape)

        cond_clean = cut_line>=xvals

        indexTop = []
        indexBtm = []

        for i,cond in enumerate(cond_clean):
            
            if i>0:
                old_cond = cond_clean[i-1]
            else:
                old_cond = False
                
            try:
                new_cond = cond_clean[i+1]
            except IndexError:
                new_cond = False
                
            if cond and not old_cond:
                indexTop.append(i)

            if cond and not new_cond:
                indexBtm.append(i)

        net_pay = 0

        for i,j in zip(indexTop,indexBtm):

            net_pay += depth[j]-depth[i]

        self.axes[indexI].subax[indexJ].fill_betweenx(
            depth,xvals,x2=cut_line,where=cond_clean,color=self.color_clean)

        self.netPayThickness = net_pay
        self.netToGrossRatio = net_pay/self.gross_thickness*100

        return GRcut

    def set_DepthViewNeuPorCorr(self,NeuPorLine,indexI,indexJ,Vsh,NeuPorShale):

        # indexI index of Neutron Porosity containing axis in the plot
        # indexJ index of Neutron Porosity containing line in the axis

        try:
            depth = self.frames[NeuPorLine[0]]["MD"]
        except KeyError:
            depth = self.frames[NeuPorLine[0]]["DEPT"]

        xvals = self.frames[NeuPorLine[0]][NeuPorLine[1]]

        NeuPorCorr = xvals-Vsh*NeuPorShale

        self.axes[indexI].subax[indexJ].plot(NeuPorCorr,depth,
            color=self.lineColors[indexJ],linestyle="--")

    def set_DepthViewResistivityCut(self,ResLine,indexI,indexJ,ohmm_cut=10):

        # indexI index of Resistivity containing axis in the plot
        # indexJ index of Resistivity containing line in the axis

        depth = self.frames[ResLine[0]].columns(0)

        xvals = self.frames[ResLine[0]].columns(ResLine[1])

        cut_line = ohmm_cut*numpy.ones(depth.shape)

        self.axes[indexI].subax[indexJ].fill_betweenx(
            depth,xvals,x2=cut_line,where=ohmm_cut<=xvals,color=self.color_HC)

    def set_DepthViewSaturationCut(self,SwLine,indexI,indexJ,Sw_cut=0.5):

        # indexI index of Resistivity containing axis in the plot
        # indexJ index of Resistivity containing line in the axis

        depth = self.frames[SwLine[0]].columns(0)

        xvals = self.frames[SwLine[0]].columns(SwLine[1])

        cut_line = Sw_cut*numpy.ones(depth.shape)

        self.axes[indexI].subax[indexJ].fill_betweenx(
            depth,xvals,x2=cut_line,where=Sw_cut>=xvals,color=self.color_HC)

    def set_DepthViewNMRfluid(self,NMRline,indexI,water_clay,water_capi,water_move,HC):

        # indexL index of NMR containing lasio in the pack
        # indexI index of NMR containing axis in the plot

        try:
            depth = self.frames[NMRline]["MD"]
        except KeyError:
            depth = self.frames[NMRline]["DEPT"]

        xvals0 = numpy.zeros(water_clay.shape)
        xvals1 = water_clay
        xvals2 = water_clay+water_capi
        xvals3 = water_clay+water_capi+water_move
        xvals4 = water_clay+water_capi+water_move+HC

        self.axes[indexI].subax[0].fill_betweenx(
            depth,xvals1,x2=xvals0,where=xvals0<=xvals1,color=self.color_waterclay)

        self.axes[indexI].subax[0].fill_betweenx(
            depth,xvals2,x2=xvals1,where=xvals1<=xvals2,color=self.color_watercapi)

        self.axes[indexI].subax[0].fill_betweenx(
            depth,xvals3,x2=xvals2,where=xvals2<=xvals3,color=self.color_watermove)

        self.axes[indexI].subax[0].fill_betweenx(
            depth,xvals4,x2=xvals3,where=xvals3<=xvals4,color=self.color_HC)

    def set_DepthViewPerfs(self,indexI,indexJ,depths,perfs):

        xtick = self.axes[indexI].subax[indexJ].get_xticks()

        ytick = self.axes[indexI].subax[indexJ].get_yticks()

        perfs = numpy.array(perfs)

        perfs_just = perfs[perfs>0]

        perfs_just[::10] -= perfs_just[::10]*0.5

        perfs[perfs>0] = perfs_just

        perfs_scaled = xtick.min()+(xtick.max()-xtick.min())/10/(perfs.max()-perfs.min())*perfs

        # pfgun_point = xtick.min()

        # for arg in args:

        #     depths = numpy.arange(arg[0],arg[1]+1/2,1.)

        #     for index,depth in enumerate(depths):

        #         if index==0:
        #             marker,size = 11,10
        #         elif index==len(depths)-1:
        #             marker,size = 10,10
        #         else:
        #             marker,size = 9,10

        #         self.axes[indexI].subax[indexJ].plot(pfgun_point,depth,
        #             marker=marker,color='orange',markersize=size,markerfacecolor='black')

        self.axes[indexI].subax[indexJ].plot(perfs_scaled,depths)

    def set_DepthViewCasing(self):
        """It creates an axis to include casing set depths"""

        pass

    def _on_mousewheel(self,event):
        """Lets the scroll work everywhere on the window."""

        self.canvas.yview_scroll(int(-1*(event.delta/120)),"units")

class gammaray():

    def __init__(self):

        pass

    def cut(self,GRline,depth=("None",None,None),perc_cut=40):

        xvals = self.get_interval(*depth[1:],idframes=GRline[0],curveID=GRline[1])[0]

        GRmin = numpy.nanmin(xvals)
        GRmax = numpy.nanmax(xvals)

        GRcut = (GRmin+(GRmax-GRmin)*perc_cut/100)

        return GRcut

    def shalevolume(self,GRline,GRmin=None,GRmax=None,model=None):

        xvals = self.frames[GRline[0]][GRline[1]]

        if GRmin is None:
            GRmin = numpy.nanmin(xvals)

        if GRmax is None:
            GRmax = numpy.nanmax(xvals)

        Ish = (xvals-GRmin)/(GRmax-GRmin)

        if model is None or model=="linear":
            Vsh = Ish

        return Vsh

    def spectral(self):

        self.fig_gscp,self.axis_gscp = pyplot.subplots()

class spotential():

    def __init__(self):

        pass

    def spotential(self,SPline,SPsand,SPshale):

        xvals = self.frames[SPline[0]][SPline[1]]

        Vsh = (xvals-SPsand)/(SPshale-SPsand)

        return Vsh

class crossplots():

    SS = {
        "lithology": "Sandstone",
        "marker": "2",
        "markercolor": "red",
        }

    SS["type1"] = {
        "description": "Sandstone, Porosity > 10%",
        "DTma": 55.5,
        "rhoma": 2.65,
        "phima_SNP": -0.035,
        "phima_CNL": -0.05,
        }

    SS["type2"] = {
        "description": "Sandstone, Porosity < 10%",
        "DTma": 51.2,
        "rhoma": 2.65,
        "phima_SNP": -0.035,
        "phima_CNL": -0.005,
        }

    LS = {
        "lithology": "Limestone",
        "marker": "2",
        "markercolor": "blue",
        }

    LS["type1"] = {
        "description": "Limestone",
        "DTma": 47.5,
        "rhoma": 2.71,
        "phima_SNP": 0,
        "phima_CNL": 0,
        }

    DOL = {
        "lithology": "Dolomite",
        "marker": "2",
        "markercolor": "green",
        }

    DOL["type1"] = {
        "description": "Dolomite, 5.5% < Porosity < 30%",
        "DTma": 43.5,
        "rhoma": 2.87,
        "phima_SNP": 0.035,
        "phima_CNL": 0.085,
        }

    DOL["type2"] = {
        "description": "Dolomite, 1.5% < Porosity < 5.5% && Porosity>30%",
        "DTma": 43.5,
        "rhoma": 2.87,
        "phima_SNP": 0.02,
        "phima_CNL": 0.065,
        }

    DOL["type3"] = {
        "description": "Dolomite, 0% < Porosity < 1.5%",
        "DTma": 43.5,
        "rhoma": 2.87,
        "phima_SNP": 0.005,
        "phima_CNL": 0.04,
        }

    ANH = {
        "lithology": "Anhydrite",
        "marker": "2",
        "markercolor": "cyan",
        }

    ANH["type1"] = {
        "description": "Anhydrite",
        "DTma": 50.0,
        "rhoma": 2.98,
        "phima_SNP": -0.005,
        "phima_CNL": -0.002,
        }

    SLT = {
        "lithology": "Salt",
        "marker": "2",
        "markercolor": "black",
        }

    SLT["type1"] = {
        "description": "Salt",
        "DTma": 67.0,
        "rhoma": 2.03,
        "phima_SNP": 0.04,
        "phima_CNL": -0.01,
        }

    def __init__(self):

        pass

class denneu(crossplots):

    def __init__(self,rhof=1.0,phiNf=1.0,NTool="CNL"):

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

class sonden(crossplots):

    def __init__(self):

        pass

class sonneu(crossplots):

    def __init__(self,DT_FLUID=189,PHI_NF=1):

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

class denphe(crossplots):

    def __init__(self):
        """density photoelectric cross section cross plot"""
        pass

class mnplot(crossplots):

    def __init__(self,DTf=189,rhof=1.0,phiNf=1.0,NTool="SNP"):

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

class midplot(crossplots):

    def __init__(self):

        self.fig_midp,self.axis_midp = pyplot.subplots()

class rhoumaa(crossplots):

    def __init__(self):

        pass

class pickett():

    def __init__(self):

        pass

    def PickettCrossPlot(
        self,
        resLine,
        phiLine,
        returnSwFlag=False,
        showDiffSwFlag=True,
        m=2,
        n=2,
        a=0.62,
        Rw=0.1,
        xmin=None,
        xmax=None,
        ymin=None,
        ymax=None,
        GRconds=None,
        ):

        if returnSwFlag:

            xvalsR = self.frames[resLine[0]].columns(resLine[1])
            xvalsP = self.frames[phiLine[0]].columns(phiLine[1])

            Sw_calculated = ((a*Rw)/(xvalsR*xvalsP**m))**(1/n)

            Sw_calculated[Sw_calculated>1] = 1

            return Sw_calculated

        else:

            self.fig_pcp,self.axis_pcp = pyplot.subplots()

            xaxis_min = 1
            xaxis_max = 100

            yaxis_min = 0.1
            yaxis_max = 1

            for depth in self.depths:

                xaxis = self.get_interval(*depth[1:],idframes=resLine[0],curveID=resLine[1])[0]
                yaxis = self.get_interval(*depth[1:],idframes=phiLine[0],curveID=phiLine[1])[0]

                xaxis_min = min((xaxis_min,xaxis.min()))
                xaxis_max = max((xaxis_max,xaxis.max()))

                yaxis_min = min((yaxis_min,yaxis.min()))
                yaxis_max = max((yaxis_max,yaxis.max()))

                if GRconds is not None:
                    self.axis_pcp.scatter(xaxis[GRconds],yaxis[GRconds],s=1,label="{} clean".format(depth[0]))
                    self.axis_pcp.scatter(xaxis[~GRconds],yaxis[~GRconds],s=1,label="{} shaly".format(depth[0]))
                else:
                    self.axis_pcp.scatter(xaxis,yaxis,s=1,label=depth[0])

            self.axis_pcp.legend(scatterpoints=10)

            indexR = self.frames[resLine[0]].headers.index(resLine[1])
            indexP = self.frames[phiLine[0]].headers.index(phiLine[1])

            mnemR = self.frames[resLine[0]].headers[indexR]
            unitR = self.frames[resLine[0]].units[indexR]

            mnemP = self.frames[phiLine[0]].headers[indexP]
            unitP = self.frames[phiLine[0]].units[indexP]

            xaxis_min = xmin if xmin is not None else xaxis_min
            xaxis_max = xmax if xmax is not None else xaxis_max

            yaxis_min = ymin if ymin is not None else yaxis_min
            yaxis_max = ymax if ymax is not None else yaxis_max

            resexpmin = numpy.floor(numpy.log10(xaxis_min))
            resexpmax = numpy.ceil(numpy.log10(xaxis_max))

            if showDiffSwFlag:

                resSw = numpy.logspace(resexpmin,resexpmax,100)

                Sw75,Sw50,Sw25 = 0.75,0.50,0.25

                philine_atSw100 = (a*Rw/resSw)**(1/m)

                philine_atSw075 = philine_atSw100*Sw75**(-n/m)
                philine_atSw050 = philine_atSw100*Sw50**(-n/m)
                philine_atSw025 = philine_atSw100*Sw25**(-n/m)

                self.axis_pcp.plot(resSw,philine_atSw100,c="black",linewidth=1)#,label="100% Sw")
                self.axis_pcp.plot(resSw,philine_atSw075,c="blue",linewidth=1)#,label="75% Sw")
                self.axis_pcp.plot(resSw,philine_atSw050,c="blue",linewidth=1)#,label="50% Sw")
                self.axis_pcp.plot(resSw,philine_atSw025,c="blue",linewidth=1)#,label="25% Sw")

            phiexpmin = numpy.floor(numpy.log10(yaxis_min))
            phiexpmax = numpy.ceil(numpy.log10(yaxis_max))

            xticks = 10**numpy.arange(resexpmin,resexpmax+1/2)
            yticks = 10**numpy.arange(phiexpmin,phiexpmax+1/2)

            self.axis_pcp.set_xscale('log')
            self.axis_pcp.set_yscale('log')

            self.axis_pcp.set_xlim([xticks.min(),xticks.max()])
            self.axis_pcp.set_xticks(xticks)

            self.axis_pcp.set_ylim([yticks.min(),yticks.max()])
            self.axis_pcp.set_yticks(yticks)

            self.axis_pcp.xaxis.set_major_formatter(LogFormatter())
            self.axis_pcp.yaxis.set_major_formatter(LogFormatter())

            for tic in self.axis_pcp.xaxis.get_minor_ticks():
                tic.label1.set_visible(False)
                tic.tick1line.set_visible(False)

            for tic in self.axis_pcp.yaxis.get_minor_ticks():
                tic.label1.set_visible(False)
                tic.tick1line.set_visible(False)

            self.axis_pcp.set_xlabel("{} {}".format(mnemR,unitR))
            self.axis_pcp.set_ylabel("{} {}".format(mnemP,unitP))

            self.axis_pcp.grid(True,which="both",axis='both')

class hingle():

    def __init__(self):

        pass

    def HingleCrossPlot(self):

        self.fig_hcp,self.axis_hcp = pyplot.subplots()

class lasbatch(dirmaster):

    def __init__(self,filepaths=None,**kwargs):

        homedir = None if kwargs.get("homedir") is None else kwargs.pop("homedir")
        filedir = None if kwargs.get("filedir") is None else kwargs.pop("filedir")

        super().__init__(homedir=homedir,filedir=filedir)

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

