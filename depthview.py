from matplotlib import gridspec
from matplotlib import pyplot

from matplotlib.patches import Rectangle

from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import LogLocator

import numpy

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

        xlim = curve_axis.get_xlim()
        ylim = curve_axis.get_ylim()

        xscale = curve_axis.get_xscale()

        if xscale == "linear":
            xvals,xlim = self._get_linear_normalized(curve.vals,xlim)
        elif xscale == "log":
            xvals,xlim = self._get_log_normalized(curve.vals,xlim)
        else:
            raise ValueError(f"{xscale} has not been defined! options: {{linear,log}}")

        yvals,ylim = self._get_linear_normalized(curve.depths,ylim,multp=1)

        curve_axis.plot(xvals,yvals,
            color=curve.linecolor,linestyle=curve.linestyle,linewidth=curve.linewidth)

        if curve.fill:
            curve_axis.fill_betweenx(yvals,xvals,x2=0,facecolor=curve.fillfacecolor,hatch=curve.fillhatch)

        numlines = len(curve_axis.lines)

        if curve.fill:
            self._add_label_fill(label_axis,curve,xlim,numlines)
        else:
            self._add_label_line(label_axis,curve,xlim,numlines)

    @staticmethod
    def _get_rounded(xmin,xmax):

        xdelta = numpy.abs(xmax-xmin)

        power = -numpy.floor(numpy.log10(xdelta))

        xmin = numpy.floor(xmin*10**power)/10**power
        xmax = numpy.ceil(xmax*10**power)/10**power

        return xmin,xmax

    @staticmethod
    def _get_linear_normalized(values,axis_limits,shift=None,multp=None):

        axis_min,axis_max = min(axis_limits),max(axis_limits)
        vals_min,vals_max = values.min(),values.max()

        # print(f"{axis_min=},",f"{axis_max=}")
        # print(f"given_{vals_min=},",f"given_{vals_max=}")

        vals_min_temp,vals_max_temp = depthview._get_rounded(vals_min,vals_max)

        # print(f"{vals_min_temp=},",f"{vals_max_temp=}")
            
        if multp is None:
            multp = numpy.floor((axis_max-axis_min)/(vals_max_temp-vals_min_temp))

        if shift is None:
            shift = -numpy.floor((vals_min_temp*multp-axis_min)/10)*10

        # print(f"{multp=},",f"{shift=}")
        
        vals = shift+values*multp

        vals_min = (axis_min-shift)/multp
        vals_max = (axis_max-shift)/multp
        
        # print(f"normalized_{vals_min=},",f"normalized_{vals_max=}")

        return vals,(vals_min,vals_max)

    @staticmethod
    def _get_log_normalized(values,axis_limits,shift=None,multp=None):

        if multp is None:

            pass

        if shift is None:

            pass

    def _add_label_line(self,label_axis,curve,xlim,numlines=0):

        label_axis.plot((0,1),(numlines-0.7,numlines-0.7),
            color=curve.linecolor,linestyle=curve.linestyle,linewidth=curve.linewidth)

        label_axis.text(0.5,numlines-0.5,f"{curve.head} [{curve.unit}]",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        label_axis.text(0.02,numlines-0.5,f'{xlim[0]}',horizontalalignment='left')
        label_axis.text(0.98,numlines-0.5,f'{xlim[1]}',horizontalalignment='right')

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

if __name__ == "__main__":

    dv = depthview()

    dv.set_axes(naxes=3,ncurves_max=3,label_loc="top")

    dv.set_xcycles(0,xcycles=2,xcycleskip=0,xscale='linear')
    dv.set_xcycles(3,xcycles=3,xcycleskip=0,xscale='log')
    dv.set_ycycles(7,4)

    ulas = {}

    ulas['depths'] = numpy.linspace(1033,1083,num=50)

    ulas['GR'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    ulas['CALI'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)/50
    ulas['NPHI'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    ulas['RHOB'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    ulas['R001'] = numpy.random.rand(50)*10**numpy.random.randint(0,4,50)
    ulas['R002'] = numpy.random.rand(50)*10**numpy.random.randint(0,5,50)

    class curve():

        def __init__(self,ulas,head,unit,info,
            linecolor="k",linestyle="-",linewidth=0.75,
            fill=False,fillhatch='..',fillfacecolor='gold'):

            self.depths = ulas['depths']
            self.vals = ulas[head]
            self.head = head
            self.unit = unit
            self.info = info
            
            self.linecolor = linecolor
            self.linestyle = linestyle
            self.linewidth = linewidth

            self.fill = fill
            self.fillhatch = fillhatch
            self.fillfacecolor = fillfacecolor

    dv.add_curve(0,curve(ulas,"GR","API","",linestyle='-'))
    dv.add_curve(0,curve(ulas,"CALI",'in','',linestyle='--'))
    dv.add_curve(2,curve(ulas,"NPHI",'p.u.','',linestyle='-'))
    dv.add_curve(2,curve(ulas,"RHOB",'g/cm3','',linestyle='--'))
    # dv.add_curve(3,curve(ulas,"R001",'ohm.m','',linestyle='-'))
    # dv.add_curve(3,curve(ulas,"R002",'ohm.m','',linestyle='--'))

    dv.show() #"sample.pdf"