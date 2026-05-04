from matplotlib import pyplot

import numpy

from scipy.stats import norm

class StatMeasures():

    def __init__(self,perm,poro=None,height=None):
        """
        perm    : permeability of layers representing flow capacity

        poro    : porosity of layers representing storage capacity

        height  : height of layers; default value None is the case when
                  layers have the same height list or array if layers have
                  different height
        """

        self._perm = numpy.asarray(perm).flatten()

        self._poro = None if poro is None else numpy.asarray(poro).flatten()

        self._height = None if height is None else numpy.asarray(height).flatten()

    @property
    def perm(self):
        return self._perm

    @property
    def poro(self):
        return self._poro

    @property
    def height(self):
        if self._height is None
            return numpy.ones(self.perm.shape)
        elif self._height.size==1:
            return numpy.full(self.perm.shape,self.height)
        return self._height

    def mean(self,param="perm"):

        return numpy.nanmean(getattr(self,param))

    def var(self,param="perm"):

        return numpy.nanvar(getattr(self,param))

    def std(self,param="perm"):

        return numpy.sqrt(self.var(param))

    @property
    def varcoeff(self):

        return self.std("perm")/self.mean("perm")

    def sort(self,*args,flip=False):

        indices = numpy.argsort(getattr(self,args[0]))

        if flip:
            indices = numpy.flip(indices)

        return tuple([getattr(self,arg)[indices] for arg in args])

    def fraction(self,param="perm"):

        capacity = self.height*getattr(self,param)

        fraction = numpy.cumsum(capacity)/numpy.sum(capacity)

        return numpy.insert(fraction,0,0)

    @property
    def dykstra(self):
        """
        Calculates Dykstra-Parson coefficient for permeability and
            height (optional) values.

        Returned value is the Dykstra-Parson coefficient where 0 stands for
            homogeneous reservoirs and 1 for hypothetical infinitely
            heterogeneous reservoir

        In general, Dykstra-Parson and Lorenz coefficient are not equal each other.
        """

        perm,height = self.sort("perm","height")

        ppf = self.ppf(height/numpy.sum(height))

        slope,intercept = numpy.polyfit(ppf,numpy.log10(perm),1)

        k50_0 = 10**(slope*norm.ppf(0.500)+intercept)
        k15_9 = 10**(slope*norm.ppf(0.159)+intercept)

        return (k50_0-k15_9)/k50_0

    @property
    def lorenz(self):
        """
        Calculates Lorenz coefficient for permeability, porosity and
            height values.

        Returned value is the Lorenz coefficient where 0 means perfect equality,
            homogeneous reservoirs and 1 means perfect inequality, infinitely
            heterogeneous reservoir

        In general, Dykstra-Parson and Lorenz coefficient are not equal each other.
        """

        perm,poro,height = self.sort("perm","poro","height",flip=True)

        ffrac = self.fraction("perm")
        sfrac = self.fraction("poro")

        area = numpy.trapz(ffrac,sfrac)
        
        return (area-0.5)/0.5

    @property
    def gelhar(self):

        pass

    def show_DP(self,axis):

        axis.scatter(ppf,perm)
        axis.set_yscale('log')

        xaxis = axis.get_xlim()

        x_abs = max([abs(x) for x in xaxis])

        xaxis = numpy.array([-x_abs,x_abs])

        ybest = slope*xaxis+intercept

        axis.plot(xaxis,10**ybest,'k')

        axis.set_xlabel("Normal Quantiles")

        axis.set_ylabel("Log10(Permeability)")

        axis.grid(which="both")

    def show_LC(self,axis):

        axis.plot(sfrac,ffrac,color='k',linewidth=0.5)

        for sf,ff in zip(sfrac,ffrac):
            axis.vlines(sf,ymin=sfrac,ymax=ff,color='k',linewidth=0.5)

        axis.scatter(sfrac,ffrac,s=10,zorder=3)

        axis.plot((0,1),(0,1),color='red')
        
        axis.fill_between(x=sfrac,y1=sfrac,y2=ffrac,facecolor="gray",alpha=0.2)

        axis.set_xlim((0,1))
        axis.set_ylim((0,1))

        axis.set_xlabel("Fraction of Total Storage Capacity")
        axis.set_ylabel("Fraction of Total Flow Capacity")

    @staticmethod
    def ppf(prob):
        return norm.ppf(numpy.cumsum(prob)-prob/2)
    