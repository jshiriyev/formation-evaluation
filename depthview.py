from matplotlib import gridspec
from matplotlib import pyplot

from matplotlib.patches import Rectangle

import numpy

class depthview():

    def __init__(self,file,page_format="Letter"):

        self.file = file

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

        self.axes_label = []
        self.axes_curve = []

        for i in range(numcols):

            label = self.figure.add_subplot(self.gspecs[0,i])
            curve = self.figure.add_subplot(self.gspecs[1,i])

            if i != depth_column:
                label = self._set_labelaxis(label)
                curve = self._set_curveaxis(curve)
            else:
                label = self._set_depth_labelaxis(label)
                curve = self._set_depth_curveaxis(curve)

            self.axes_label.append(label)
            self.axes_curve.append(curve)

    def set_curveaxis(self,index,**kwargs):

        axis = self.axes_curve[index]

        self._set_curveaxis(axis,**kwargs)

    def _set_curveaxis(self,axis,logscale=False,xcycles=2,xcycleskip=0):

        if logscale:
            xlim = (1*(xcycleskip+1),(xcycleskip+1)*10**xcycles)
        else:
            xlim = (0+xcycleskip,10*xcycles+xcycleskip)

        ylim = (0,70)

        axis.set_xlim(xlim)
        axis.set_ylim(ylim)

        if logscale:
            axis.set_xscale("log")
        else:
            xminors = self.get_yticks(xlim,delta=1.)
            xmajors = self.get_yticks(xlim,delta=10.)

            axis.set_xticks(xminors,minor=True)
            axis.set_xticks(xmajors,minor=False)

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.tick_params(axis="x",which="minor",bottom=False)

        axis.grid(axis="x",which='minor',alpha=0.5)
        axis.grid(axis="x",which='major',alpha=1)

        yminors = self.get_yticks(ylim,delta=1.)
        ymajors = self.get_yticks(ylim,delta=10.)

        axis.set_yticks(yminors,minor=True)
        axis.set_yticks(ymajors,minor=False)

        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        axis.tick_params(axis="y",which="minor",left=False)

        axis.grid(axis="y",which='minor',alpha=0.5)
        axis.grid(axis="y",which='major',alpha=1)

        return axis

    def _set_labelaxis(self,axis):

        axis.set_xlim((0,1))
        axis.set_ylim((0,4))

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)
        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        return axis

    def _set_depth_labelaxis(self,axis):

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)
        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        return axis

    def _set_depth_curveaxis(self,axis):

        xlim = (0,1)
        ylim = (0,70)

        axis.set_xlim(xlim)
        axis.set_ylim(ylim)

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        yminors = self.get_yticks(ylim,delta=1.)
        ymajors = self.get_yticks(ylim,delta=10.)

        axis.set_yticks(yminors,minor=True)
        axis.set_yticks(ymajors,minor=False)
        
        axis.tick_params(
            axis="y",which="both",direction="in",right=True,pad=-40)

        pyplot.setp(axis.get_yticklabels(),visible=False)

        return axis

    def set_depth_curveaxis_(self,axis):

        self.yminors = self.get_yticks(self.file['depth'],delta=1.)
        self.ymajors = self.get_yticks(self.file['depth'],delta=10.)

        self.ylim = (max(self.yminors),min(self.yminors))

        axis.vlines(10,min(self.ymajors),max(self.ymajors))

        axis.set_ylim(self.ylim)

        axis.set_yticks(self.yminors,minor=True)
        axis.set_yticks(self.ymajors,minor=False)

        axis.set_xlim((0,1))
        
        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)
        
        axis.tick_params(
            axis="y",which="both",direction="in",right=True,pad=-40)

        return axis

    def add_curve(self,index,curve):

        axis = self.axes_curve[index]

        axis.plot(self.file[curve.head],self.file['depth'],
            color=curve.linecolor,linestyle=curve.linestyle,linewidth=curve.linewidth)

        axis.set_ylim(self.ylim)

        axis.set_yticks(self.yminors,minor=True)
        axis.set_yticks(self.ymajors,minor=False)

        axis.tick_params(axis="y",which="minor",left=False)

        axis.grid(axis="y",which='minor',alpha=0.2)
        axis.grid(axis="y",which='major',alpha=1)

        numlines = len(axis.lines)

        if curve.fill:

            rect = Rectangle((0,numlines-1),1,1,
                fill=True,hatch=curve.fillhatch,facecolor=curve.fillfacecolor)

            self.axes_label[index].add_patch(rect)

            self.axes_label[index].text(0.5,numlines-0.5,curve.head,
                horizontalalignment='center',
                verticalalignment='center',
                backgroundcolor='white',
                fontsize='small',)

        else:

            self.axes_label[index].plot((0,1),(numlines-0.7,numlines-0.7),
                color=curve.linecolor,linestyle=curve.linestyle,linewidth=curve.linewidth)

            self.axes_label[index].text(0.5,numlines-0.5,curve.head,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize='small',)

    def get_yticks(self,vals,delta=10.):

        tmin = numpy.floor(numpy.min(vals))
        tmax = numpy.ceil(numpy.max(vals))

        Tmin = numpy.ceil(tmin/delta)*delta
        Tmax = numpy.floor(tmax/delta)*delta

        ticks = numpy.arange(Tmin,Tmax+delta/2,delta)

        return ticks

    def show(self,filename=None,wspace=0.0,hspace=0.0):

        self.gspecs.tight_layout(self.figure)

        self.gspecs.update(wspace=wspace,hspace=hspace)

        if filename is not None:
            self.figure.savefig(filename,format='pdf')

if __name__ == "__main__":

    ulas = {}

    ulas['depth'] = numpy.linspace(1033,1083,num=50)

    ulas['GR'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    ulas['CALI'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    ulas['NPHI'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    ulas['RHOB'] = numpy.random.rand(50)*10**numpy.random.randint(0,1,50)
    ulas['R001'] = numpy.random.rand(50)*10**numpy.random.randint(0,4,50)
    ulas['R002'] = numpy.random.rand(50)*10**numpy.random.randint(0,5,50)

    dv = depthview(ulas)

    dv.set_axes(naxes=3,ncurves_max=3,label_loc="top")

    dv.set_curveaxis(3,logscale=True,xcycles=2,xcycleskip=0)

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

    pyplot.show()
