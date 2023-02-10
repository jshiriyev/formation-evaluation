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

def NanView(lasfile,axis=None,zonedepths=None,zonenames=None,xrotation=90,yrotation=0,xfmt=False,yfmt=None,ignorenansteps=None):
    """ """

    show = True if axis is None else False

    if axis is None:
        axis = pyplot.figure().add_subplot()

    xvals,yvals = getnans(lasfile,ignorenansteps=ignorenansteps)

    yvalues = numpy.unique(numpy.concatenate(yvals))

    raxis = axis.twinx()

    yvalues = gettops(raxis,lasfile,yvalues,zonedepths,zonenames)

    for (xval,yval) in zip(xvals,yvals):
        axis.step(xval,numpy.where(yvalues==yval.reshape((-1,1)))[1])

    axis.set_xlim((-1,len(lasfile.keys())))
    axis.set_ylim((yvalues.size,-1))

    axis.set_yticks(numpy.arange(yvalues.size))

    if yfmt is None:
        yticklabels = lasfile[0][yvalues]
    else:
        yticklabels = [yfmt.format(val) for val in lasfile[0][yvalues]]

    axis.set_yticklabels(yticklabels,rotation=yrotation,verticalalignment='center')

    axis.set_xticks(numpy.arange(len(lasfile.keys())))

    heads = lasfile.keys()

    if xfmt is True:
        heads = [head.split('_')[0] for head in heads]
        
    axis.set_xticklabels(heads,rotation=xrotation,horizontalalignment="center")

    axis.xaxis.tick_top()

    axis.grid(True,which="both",axis='y')

    if show:
        pyplot.tight_layout()
        pyplot.show()

def getnans(lasfile,ignorenansteps=None):
    """It creates xval and yval for each curve to indicate at which points we have non-nan values.

    example xval: numpy.array([1,numpy.nan,1,numpy.nan])    
    example yval: numpy.array([5,9,10,15])
    
    """

    xvals = []
    yvals = []

    depth = lasfile[0]

    for index,curve in enumerate(lasfile.curves):

        isnan = numpy.isnan(curve.data)

        isnan = ignorenans(isnan,steps=ignorenansteps)

        L_shift = numpy.ones(curve.data.size,dtype=bool)
        R_shift = numpy.ones(curve.data.size,dtype=bool)

        L_shift[:-1] = isnan[1:]
        R_shift[1:] = isnan[:-1]

        lower = numpy.where(numpy.logical_and(~isnan,R_shift))[0]
        upper = numpy.where(numpy.logical_and(~isnan,L_shift))[0]

        yval = numpy.concatenate((lower,upper),dtype=int).reshape((2,-1)).T.flatten()

        xval = numpy.full(yval.size,index,dtype=float)
        
        xval[1::2] = numpy.nan

        xvals.append(xval)
        yvals.append(yval)

    return xvals,yvals

def ignorenans(array,steps:int=None):
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

def gettops(axis,lasfile,yvalues,zonedepths,zonenames):

    if zonedepths is None:
        return yvalues

    lasdepths = lasfile[0]

    laszones,laszoneindices = [],[]

    for zonedepth,zonename in zip(zonedepths,zonenames):
        
        if zonedepth<lasdepths[0]:
            continue
        
        if zonedepth>lasdepths[-1]:
            continue
        
        lasindex = numpy.argmin(numpy.abs(lasdepths-zonedepth))

        laszones.append(zonename)
        laszoneindices.append(lasindex)

        yvalues = numpy.insert(yvalues,0,lasindex)

        yvalues.sort()

    laszones = numpy.array(laszones)
    laszoneindices = numpy.array(laszoneindices)

    axis.set_ylim((yvalues.size,-1))

    yticks = numpy.arange(yvalues.size)

    axis.set_yticks(yticks)

    yticklabels = []

    for ytick in yticks:

        if numpy.any(laszoneindices==yvalues[ytick]):
            yticklabels.append(laszones[laszoneindices==yvalues[ytick]][0])
        else:
            yticklabels.append("")

    print(yticklabels,len(yticklabels))
    print()

    axis.set_yticklabels(yticklabels)

    return yvalues