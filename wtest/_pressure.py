from matplotlib import pyplot

import numpy

from scipy.special import expi

class pressure():
    """Calculates well bottomhole pressure in field units for the given constant
    flow rate production at transient state, single phase flow.
    """

    def __init__(self,k,phi,mu,ct,h,rw,rate,time,fvf=1,skin=0):
        """
        k       : permeability in mD
        phi     : porosity
        mu      : viscosity in cp
        ct      : total compressibility in 1/psi
        h       : formation thickness, ft
        rw      : wellbore radius, ft
        rate    : constant flow rate, STB/day
        time    : time array when to calculate bottom hole pressure, days
        fvf     : formation volume factor, bbl/STB
        skin    : skin factor, dimensionless

        """

        self.k = k
        self.phi = phi
        self.mu = mu

        self.ct = ct

        self.h = h
        self.rw = rw

        self.rate = rate
        self.time = time

        self.fvf = fvf

        self.skin = skin

        self._initialize()

    def _initialize(self):
        """It calculates delta bottom hole flowing pressure for constant
        flow rate production."""

        self._eta = self.k/(self.phi*self.mu*self.ct)

        self._flowterm = -141.2*(self.rate*self.mu*self.fvf)/(self.k*self.h)

        self._delta = numpy.zeros(self.time.shape)

        self._twell = 15802*self.rw**2/self.eta

        self._delta[self.time<=self.twell] = numpy.nan

        self._transient()

    def _transient(self):

        transient_cond = self.time>self.twell

        transient_time = self.time[transient_cond]

        Ei = expi(-39.5*(self.rw**2)/(self.eta*transient_time))

        delta = -self.flowterm*(1/2*Ei-self.skin)

        self.delta[transient_cond] = delta

    def set_boundary(self,radius=None,area=None):
        """Sets the radius of outer circular boundary, ft.
        If area is not None, the radius is calculated from area [acre].
        """

        if area is not None:
            radius = numpy.sqrt(area*43560/numpy.pi)

        self._radius = radius

        self._tbound = 39.5*self.radius**2/self.eta

        self._pseudo()

    def _pseudo(self):

        pseudo_cond = self.time>=self.tbound

        pseudo_time = self.time[pseudo_cond]

        term_time = -0.012648*(self.eta*pseudo_time)/self.radius**2

        term_boundary = -numpy.log(self.radius/self.rw)

        delta = -self.flowterm*(term_time+term_boundary+3/4-self.skin)

        self.delta[pseudo_cond] = delta

    def view(self,axis=None,initial=None):

        showFlag = True if axis is None else False

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        if initial is None:
            yaxis,ylabel = -self.delta,f"Wellbore Pressure Drop [psi]"
        else:
            yaxis,ylabel = initial+self.delta,"Wellbore Pressure [psi]"

        axis.plot(self.time,yaxis)

        axis.set_xscale("log")

        if initial is None:
            axis.invert_yaxis()

        axis.set_xlabel("Time [days]")
        axis.set_ylabel(ylabel)

        if showFlag:
            pyplot.show()

    @property
    def eta(self):

        return self._eta

    @property
    def flowterm(self):

        return self._flowterm

    @property
    def radius(self):

        return self._radius

    @property
    def delta(self):

        return self._delta

    @property
    def twell(self):

        return self._twell

    @property
    def tbound(self):

        return self._tbound
    
    
    
    
    

