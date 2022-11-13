from matplotlib import gridspec
from matplotlib import pyplot

from matplotlib.patches import Rectangle

from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import LogLocator

import numpy

class depthview():

    def __init__(self,page_format="Letter"):

        # self.file = file

        if page_format == "A4":
            figsize = (8.3,11.7)
        elif page_format == "Letter":
            figsize = (8.5,11.0)

        self.figure = pyplot.figure(figsize=figsize,dpi=100)

        self.ylim = (70,0)
        
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

            self.axes_curve.append(curve_axis)
            self.axes_label.append(label_axis)

    def set_xcycles(self,index,xcycles=2,xcycleskip=0,xscale='linear'):

        axis = self.axes_curve[index]

        if xscale=="linear":
            xlim = (0+xcycleskip,10*xcycles+xcycleskip)
        elif xscale=="log":
            xlim = (1*(xcycleskip+1),(xcycleskip+1)*10**xcycles)
        else:
            raise ValueError(f"{xscale} has not been defined! options: {{linear,log}}")

        axis.set_xlim(xlim)

        axis.set_xscale(xscale)

        if xscale=="linear":
            axis.xaxis.set_minor_locator(MultipleLocator(1))
            axis.xaxis.set_major_locator(MultipleLocator(10))
        elif xscale=="log":
            axis.xaxis.set_minor_locator(LogLocator(10,subs=range(1,10)))
            axis.xaxis.set_major_locator(LogLocator(10))
        else:
            raise ValueError(f"{xscale} has not been defined! options: {{linear,log}}")

    def set_ycycles(self,ycycles,ycycleskip=0):

        ylim = (10*ycycles+ycycleskip,0+ycycleskip)

        for axis in self.axes_curve:
            axis.set_ylim(ylim)

    def _set_curveaxis(self,axis,xscale='linear',xcycles=2,xcycleskip=0,ycycles=7,ycycleskip=0):

        if xscale=="linear":
            xlim = (0+xcycleskip,10*xcycles+xcycleskip)
        elif xscale=="log":
            xlim = (1*(xcycleskip+1),(xcycleskip+1)*10**xcycles)
        else:
            raise ValueError(f"{xscale} has not been defined! options: {{linear,log}}")

        ylim = (10*ycycles+ycycleskip,0+ycycleskip)

        axis.set_xlim(xlim)
        axis.set_ylim(ylim)

        axis.set_xscale(xscale)

        if xscale=="linear":
            axis.xaxis.set_minor_locator(MultipleLocator(1))
            axis.xaxis.set_major_locator(MultipleLocator(10))
        elif xscale=="log":
            axis.xaxis.set_minor_locator(LogLocator(10,subs=range(1,10)))
            axis.xaxis.set_major_locator(LogLocator(10))
        else:
            raise ValueError(f"{xscale} has not been defined! options: {{linear,log}}")

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.tick_params(axis="x",which="minor",bottom=False)

        axis.grid(axis="x",which='minor',alpha=0.5)
        axis.grid(axis="x",which='major',alpha=1)

        axis.yaxis.set_minor_locator(MultipleLocator(1))
        axis.yaxis.set_major_locator(MultipleLocator(10))

        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        axis.tick_params(axis="y",which="minor",left=False)

        axis.grid(axis="y",which='minor',alpha=0.5)
        axis.grid(axis="y",which='major',alpha=1)

        return axis

    def _set_depthaxis(self,axis,ycycles=7,ycycleskip=0):

        xlim = (0,1)
        ylim = (10*ycycles+ycycleskip,0+ycycleskip)
        
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

    def add_curve(self,index,curve):

        curve_axis = self.axes_curve[index]
        label_axis = self.axes_label[index]

        curve_axis.plot(self.file[curve.head],self.file['depth'],
            color=curve.linecolor,linestyle=curve.linestyle,linewidth=curve.linewidth)

        numlines = len(curve_axis.lines)

        if curve.fill:
            self._add_label_fill(label_axis,curve,numlines)
        else:
            self._add_label_line(label_axis,curve,numlines)

    def _add_label_line(self,label_axis,curve,numlines=0):

        label_axis.plot((0,1),(numlines-0.7,numlines-0.7),
            color=curve.linecolor,linestyle=curve.linestyle,linewidth=curve.linewidth)

        label_axis.text(0.5,numlines-0.5,curve.head,
            horizontalalignment='center',
            verticalalignment='center',
            fontsize='small',)

    def _add_label_fill(self,label_axis,curve,numlines=0):

        rect = Rectangle((0,numlines-1),1,1,
            fill=True,hatch=curve.fillhatch,facecolor=curve.fillfacecolor)

        label.add_patch(rect)

        label.text(0.5,numlines-0.5,curve.head,
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

if __name__ == "__main__":

    dv = depthview()

    dv.set_axes(naxes=3,ncurves_max=3,label_loc="top")

    # dv.set_xcycles(0,xcycles=3,xcycleskip=0,xscale='linear')
    # dv.set_xcycles(2,xcycles=3,xcycleskip=0,xscale='linear')
    dv.set_xcycles(3,xcycles=3,xcycleskip=2,xscale='log')
    dv.set_ycycles(7,3)

    # ulas = {}

    # ulas['depth'] = numpy.linspace(1033,1083,num=50)

    # ulas['GR'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    # ulas['CALI'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    # ulas['NPHI'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    # ulas['RHOB'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    # ulas['R001'] = numpy.random.rand(50)*10**numpy.random.randint(0,4,50)
    # ulas['R002'] = numpy.random.rand(50)*10**numpy.random.randint(0,5,50)

    # class curve():

    #     def __init__(self,head,
    #         linecolor="k",linestyle="-",linewidth=0.75,
    #         fill=False,fillhatch='..',fillfacecolor='gold'):

    #         self.head = head
            
    #         self.linecolor = linecolor
    #         self.linestyle = linestyle
    #         self.linewidth = linewidth

    #         self.fill = fill
    #         self.fillhatch = fillhatch
    #         self.fillfacecolor = fillfacecolor

    # dv.add_curve(0,curve("GR",linestyle='-'))
    # dv.add_curve(0,curve("CALI",linestyle='--'))
    # dv.add_curve(2,curve("NPHI",linestyle='-'))
    # dv.add_curve(2,curve("RHOB",linestyle='--'))
    # dv.add_curve(3,curve("R001",linestyle='-'))
    # dv.add_curve(3,curve("R002",linestyle='--'))

    dv.show() #"sample.pdf"