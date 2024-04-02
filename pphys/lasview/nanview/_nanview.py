import re

import lasio

from matplotlib import colors as mcolors
from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import transforms

from matplotlib.backends.backend_pdf import PdfPages

from matplotlib.patches import Polygon
from matplotlib.patches import Rectangle

from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import FormatStrFormatter
from matplotlib.ticker import LogFormatter
from matplotlib.ticker import LogFormatterExponent
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.ticker import LogLocator
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import NullLocator
from matplotlib.ticker import ScalarFormatter

import numpy

class NanView():

    def __init__(self,lasfile,zonedepths=None,zonenames=None,ignorenansteps=None):

        self.lasfile = lasfile

        self._xvals,self._yvals = [],[] # x and y values of each las curve

        self._nans(ignorenansteps=ignorenansteps)

        self._yaxis = numpy.unique(numpy.concatenate(self._yvals)) # yvalues of combined curve plot

        self._tops(zonedepths,zonenames)

    def _nans(self,ignorenansteps=None):
        """It creates xval and yval for each curve to indicate at which points we have non-nan values.

        example xval: numpy.array([1,numpy.nan,1,numpy.nan])    
        example yval: numpy.array([5,9,10,15])
        
        """

        depth = self.lasfile[0]

        for index,curve in enumerate(self.lasfile.curves):

            isnan = numpy.isnan(curve.data)

            isnan = self._ignore_nans(isnan,steps=ignorenansteps)

            L_shift = numpy.ones(curve.data.size,dtype=bool)
            R_shift = numpy.ones(curve.data.size,dtype=bool)

            L_shift[:-1] = isnan[1:]
            R_shift[1:] = isnan[:-1]

            lower = numpy.where(numpy.logical_and(~isnan,R_shift))[0]
            upper = numpy.where(numpy.logical_and(~isnan,L_shift))[0]

            yval = numpy.concatenate((lower,upper),dtype=int).reshape((2,-1)).T.flatten()

            xval = numpy.full(yval.size,index,dtype=float)
            
            xval[1::2] = numpy.nan

            self._xvals.append(xval)
            self._yvals.append(yval)

    def _ignore_nans(self,array,steps:int=None):
        """This function helps to ignore small intervals missing in the logs."""

        if steps is None: # returns the same thing if steps is None.
            return array

        iarray = array.astype("int32")

        iarray[1:] += iarray[:-1]

        iarray[~array] = 0

        segments,segment = [],[]

        for index,value in enumerate(iarray):
            if value>0:
                segment.append(index)
            else:
                if len(segment)>0:
                    segments.append(segment)
                segment = []

        for segment in segments:
            iarray[slice(segment[0],segment[-1])] = len(segment)

        iarray[iarray<=steps] = 0

        return iarray.astype(bool)

    def _tops(self,zonedepths,zonenames):

        self._yaxis2 = []

        if zonedepths is None:
            return

        lasdepths = self.lasfile[0]

        laszones,laszoneindices = [],[]

        for zonedepth,zonename in zip(zonedepths,zonenames):
            
            if zonedepth<lasdepths[0]:
                continue
            
            if zonedepth>lasdepths[-1]:
                continue
            
            lasindex = numpy.argmin(numpy.abs(lasdepths-zonedepth))

            laszones.append(zonename)
            laszoneindices.append(lasindex)

            self._yaxis = numpy.insert(self._yaxis,0,lasindex)

            self._yaxis.sort()

        laszones = numpy.array(laszones)

        laszoneindices = numpy.array(laszoneindices)

        for ytick in numpy.arange(self._yaxis.size):

            if numpy.any(laszoneindices==self._yaxis[ytick]):
                self._yaxis2.append(laszones[laszoneindices==self._yaxis[ytick]][0])
            else:
                self._yaxis2.append("")

    def view(self,axis=None,**kwargs):

        show = True if axis is None else False

        if axis is None:

            self.figure = pyplot.figure(figsize=(8,6))

            self.axis = self.figure.add_subplot()

        self._plot(axis,**kwargs)

        self._show(show)

    def save(self,filepath,**kwargs):

        self.figure = pyplot.figure()

        self.axis = self.figure.add_subplot()

        self._plot(None,**kwargs)

        self.figure.set_figwidth(0.4*len(self.lasfile.keys()))

        self.figure.set_figheight(0.4*self._yaxis.size)

        self.figure.savefig(filepath)

        pyplot.close()

    def _plot(self,axis,xrotation=90,yrotation=0,xfmt=False,yfmt=None):

        if axis is None:
            axis = self.axis
            
        axis2 = axis.twinx()

        for (xval,yval) in zip(self._xvals,self._yvals):
            axis.step(xval,numpy.where(self._yaxis==yval.reshape((-1,1)))[1])

        axis.set_xlim((-1,len(self.lasfile.keys())))
        axis.set_ylim((self._yaxis.size,-1))

        axis2.set_ylim((self._yaxis.size,-1))

        axis.set_yticks(numpy.arange(self._yaxis.size))

        axis2.set_yticks(numpy.arange(self._yaxis.size))

        if len(self._yaxis2)>0:
            axis2.set_yticklabels(self._yaxis2)

        yticklabels = self.lasfile[0][self._yaxis]

        if yfmt is not None:
            yticklabels = [yfmt.format(val) for val in yticklabels]

        axis.set_yticklabels(yticklabels,rotation=yrotation,verticalalignment='center')

        axis.set_xticks(numpy.arange(len(self.lasfile.keys())))

        heads = self.lasfile.keys()

        if xfmt is True:
            heads = [head.split('_')[0] for head in heads]
            
        axis.set_xticklabels(heads,rotation=xrotation,horizontalalignment="center")

        axis.xaxis.tick_top()

        axis.grid(True,which="both",axis='y')

    def _show(self,show=False):

        if not show:
            return

        pyplot.tight_layout()

        pyplot.show()