from matplotlib import pyplot

import numpy

from ._pressure import pressure

from ._items import well

class buildup():
    """Calculates well bottomhole pressure in field units for the given constant
    flow rate production and shutin period.
    """

    def __init__(self,_well):

        self._pwell = well(radius=_well.radius,skin=_well.skin)
        self._iwell = well(radius=_well.radius,skin=_well.skin)

        self.rates = numpy.array(_well.rate)
        self.times = numpy.array(_well.time)

        self.Nprod = numpy.sum(self.rates*self.times)

        nzrates = self.rates[self.rates!=0]
        nztimes = self.times[self.rates!=0]

        index = numpy.argmax(nztimes/numpy.sum(nztimes))

        self.qprod = nzrates[index]

        self.tprod = self.Nprod/self.qprod

        index = numpy.nonzero(self.times)[0][-1]

        self.tshut = numpy.sum(self.times[index:])

        self.ttime = self.tprod+self.tshut

        self._pwell.rate = self.qprod
        self._pwell.time = self.ttime

        self._iwell.rate = -self.qprod
        self._iwell.time = self.tshut

    def set_parameters(self,res,oil):

        self._pprod = pressure(res,oil,self._pwell)

        self._pinj = pressure(res,oil,self._iwell)

    def set_irreducible(self,water,saturation):

        self._pprod.set_irreducible(water,saturation)

        self._pinj.set_irreducible(water,saturation)

    def set_compressibility(self,total):

        self._pprod.set_compressibility(total)

        self._pinj.set_compressibility(total)

    def initialize(self,scale="linear",size=50):

        twellp = self._pprod.twell
        twelli = self._pinj.twell

        if scale=="linear":
            tprods = numpy.linspace(twellp,self.tprod,size)
            tshuts = numpy.linspace(twelli,self.tshut,size)
        elif scale=="log":
            tprods = numpy.logspace(*numpy.log10([twellp,self.tprod]),size)
            tshuts = numpy.logspace(*numpy.log10([twelli,self.tshut]),size)

        ctimes = numpy.append(tprods,self.tprod+tshuts)

        self._pprod.initialize(time=ctimes)

        self._pinj.initialize(time=tshuts)

    def set_boundary(self,radius=None,area=None):

        self._pprod.set_boundary(radius=radius,area=area)

        self._pinj.set_boundary(radius=radius,area=area)

    def view(self,axis=None):

        showFlag = True if axis is None else False

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        yaxis,ylabel = -self.delta,f"Wellbore Pressure Change [psi]"

        axis.plot(self._pprod.time,yaxis)

        axis.set_xscale("linear")

        axis.set_ylim(ymin=0)

        axis.invert_yaxis()

        axis.set_xlabel("Time [days]")
        axis.set_ylabel(ylabel)

        if showFlag:
            pyplot.show()

    def horner(self,axis=None):

        showFlag = True if axis is None else False

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        dt = self.time-self.tprod#[1:]-self.time[:-1]

        delta = self.sdelta

        dp = delta-delta[0]

        ht = (self.tprod+dt[1:])/dt[1:]

        slope = (dp[1:]-dp[:-1])/(dt[1:]-dt[:-1])

        Pd = (slope[:-1]+slope[1:])/2*ht[:-1]*dt[1:-1]**2/self.qprod

        axis.plot(dt[1:],dp[1:])
        axis.plot(dt[1:-1],Pd)

        axis.set_xscale("log")
        axis.set_yscale("log")

        axis.set_xlabel("Delta Time [days]")
        axis.set_ylabel("Pressure Difference and Derivative")

        if showFlag:
            pyplot.show()

    @property
    def delta(self):

        delta = self._pprod.delta.copy()

        delta[self._pprod.time>self.tprod] += self._pinj.delta

        return delta

    @property
    def sdelta(self):

        return self.delta[self._pprod.time>=self.tprod]

    @property
    def time(self):

        return self._pprod.time[self._pprod.time>=self.tprod]
    

