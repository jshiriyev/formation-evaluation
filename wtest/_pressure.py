from matplotlib import pyplot

import numpy

from scipy import integrate

from scipy.special import expi

from scipy.special import j0 as BJ0
from scipy.special import j1 as BJ1
from scipy.special import y0 as BY0
from scipy.special import y1 as BY1

class pressure():
    """Calculates well bottomhole pressure in field units for the given
    constant flow rate oil production, single phase flow.
    """

    def __init__(self,res,oil,well):
        """Initializes reservoir, oil and well properties."""
        
        self.k = res.permeability
        self.phi = res.porosity
        self.h = res.thickness
        self.cr = res.compressibility

        self.muo = oil.viscosity
        self.co = oil.compressibility
        self.Bo = oil.formation_volume_factor
        self.rhoo = oil.density

        self.qo = well.rate
        self.tp = well.time
        self.rw = well.radius
        self.skin = well.skin
        self.Awb = (numpy.pi*well.radius**2)/4

    def set_irreducible(self,water,saturation):
        """Sets the irreducible water saturation amount and water properties."""

        self.muw = water.viscosity
        self.cw = water.compressibility
        self.Bw = water.formation_volume_factor

        self.Swirr = saturation

    def set_compressibility(self,total=None):
        """Sets the total compressibility. If None,
        it will try to calculate it from rock and fluid compressibilities."""

        if total is not None:
            self.ct = total
            return

        self.cr = 0 if self.cr is None else self.cr

        if hasattr(self,"Swirr"):
            if self.Swirr>0:
                self.cf = (1-self.Swirr)*self.co+self.Swirr*self.cw
            else:
                self.cf = self.co

        if hasattr(self,"cf"):
            if self.cf is None:
                self.cf = self.co
        else:
            self.cf = self.co

        self.ct = self.cr+self.cf

    def set_wellborestorage(self):

        self.Cs = (144*self.Awb)/(5.615*self.rhoo)

    def initialize(self,time=None,size=50,scale='linear'):
        """It calculates delta bottom hole flowing pressure for constant
        flow rate production at transient state, exponential integral solution.
        """

        if time is not None:
            self.time = time[time>=self.twell]

        else:

            if scale == "linear":
                self.time = numpy.linspace(self.twell,self.tp,size)
            elif scale == "log":
                self.time = numpy.logspace(*numpy.log10([self.twell,self.tp]),size)

            self._scale = scale

        Ei = expi(-39.5*(self.rw**2)/(self.eta*self.time))

        self._delta = -self.flowterm*(1/2*Ei-self.skin)

    def set_dimensionless(self,pinitial):

        self.pD = (self.k*self.h)/(141.2*self.qo*self.Bo*self.muo)*(pinitial-self.delta)

        self.tD = (0.00632829*self.k*self.time)/(self.phi*self.muo*self.ct*self.rw**2)

        self.CD = (0.8936*self.Cs)/(self.phi*self.ct*self.h*self.rw**2)

    def set_boundary(self,radius=None,area=None):
        """Sets the radius of outer circular boundary, ft and calculates
        pseudo steady state solution correcting pressure for boundary effects.
        
        If area is not None, the radius is calculated from area [acre].
        """

        if area is not None:
            radius = numpy.sqrt(area*43560/numpy.pi)

        self._radius = radius

        pseudo_cond = self.time>=self.tbound

        pseudo_time = self.time[pseudo_cond]

        term_time = -0.012648*(self.eta*pseudo_time)/self.radius**2

        term_boundary = -numpy.log(self.radius/self.rw)

        delta = -self.flowterm*(term_time+term_boundary+3/4-self.skin)

        self._delta[pseudo_cond] = delta

    def view(self,axis=None,pinitial=None,scale=None):

        showFlag = True if axis is None else False

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        if pinitial is None:
            yaxis,ylabel = -self.delta,f"Wellbore Pressure Drop [psi]"
        else:
            yaxis,ylabel = pinitial+self.delta,"Wellbore Pressure [psi]"

        axis.plot(self.time,yaxis)

        if scale is None:
            try:
                scale = self._scale
            except AttributeError:
                scale = "linear"

        axis.set_xscale(scale)

        if pinitial is None:
            axis.invert_yaxis()

        axis.set_xlabel("Time [days]")
        axis.set_ylabel(ylabel)

        if showFlag:
            pyplot.show()

    @property
    def eta(self):

        return self.k/(self.phi*self.muo*self.ct)

    @property
    def flowterm(self):

        return -141.2*(self.qo*self.Bo*self.muo)/(self.k*self.h)

    @property
    def radius(self):

        return self._radius

    @property
    def delta(self):

        return self._delta

    @property
    def twell(self):

        return 15802*self.rw**2/self.eta

    @property
    def tbound(self):

        return 39.5*self.radius**2/self.eta

class ramey():

    gamma = 0.57722

    def __init__(self,tD,CD,sf):
        """
        tD  : dimensionless time (k*t)/(phi*mu*ct*rw**2)
        CD  : dimensionless wellbore storage constant C/(2*pi*phi*h*ct*rw**2)
        sf  : skin factor, dimensionless
        """

        self.tD = numpy.array(tD).flatten()

        self.CD = float(CD)
        self.sf = float(sf)

    def pwD(self):

        if self.CD==0:

            return 1/2*(numpy.log(4*self.tD)-self.gamma)+self.sf

        pressure = numpy.zeros(self.tD.shape)

        for index,time in enumerate(self.tD):
            u = numpy.logspace(-8,2,10000)
            y = self.integrand(u,time,self.CD,self.sf)
            z = integrate.simpson(y,u)

            pressure[index] = 4*z/numpy.pi**2

        return pressure

    def derivative(self):

        pass

    @staticmethod
    def integrand(u,tD,C,s):

        term1 = 1-numpy.exp(-u**2*tD)
        term2 = u*C*BJ0(u)-(1-C*s*u**2)*BJ1(u)
        term3 = u*C*BY0(u)-(1-C*s*u**2)*BY1(u)

        return term1/(u**3*(term2**2+term3**2))

class dimensionless_models():

    def __init__(self,tD,CD=0,SF=0):

        self.tD = tD # dimensionless time
        self.CD = CD # wellbore storage dimensionless constant
        self.SF = SF # near wellbore skin factor

    def pressure(self):
        """Ramey type curve for finite reservoir with wellbore storage."""
        pass

    def pressure_infinite(self):
        """Infinite reservoir solution. No wellbore storage."""
        return -0.5*expi(-1/(4*self.tD))+self.SF
        
    def pressure_infinite_approximation(self):
        """Approximation to infinite solution. No wellbore storage."""

        term1 = numpy.log(self.tD/self.CD)

        term3 = numpy.log(self.CD)

        return 0.5*term1+0.80908+term3+self.SF

    def pressure_storage(self):
        """Wellbore storage model."""

        # return -0.5*(expi(-self.CD/(4*self.tD))+numpy.log(self.CD))+self.SF
        return self.tD/self.CD

    def derivative(self):

        return 0.5/self.tD
        # return 0.5*numpy.exp(-1/(4*self.tD))

def shorttime(tD,C,s): #useless actuall

    if s==0 and C!=0:
        term1 = 0
        term2 = -(4*tD**(3/2))/(3*C*numpy.sqrt(numpy.pi))

        return 1/C*(tD+term1+term2)

    elif s!=0 and C!=0:
        term1 = -(tD**2)/(2*C*s)
        term2 = (8*tD**(5/2))/(15*numpy.sqrt(numpy.pi)*C*s**2)

        return 1/C*(tD+term1+term2)

def shorttime_derivative(tD,C,s): #useless actuall

    if s==0 and C!=0:
        return 1-2*numpy.sqrt(tD/numpy.pi)/C+1/C*(1/C-1/2)*tD
    elif s!=0 and C!=0:
        return 1-tD/(C*s)

def longtime(tD,C,s): #useless actuall

    gamma = 0.57722

    term1 = numpy.log(4*tD)-gamma
    term2 = term1+2*s

    # return 1/2*(term2+1/(2*tD)*(term1+1-2*C*term2))

    return 1/2*(term2)

def longtime_derivative(tD,C,s): #useless actuall

    gamma = 0.57722

    term1 = C/(2*tD)
    term2 = C**2/(2*tD**2)*(2*s-1)
    term3 = C*(1-2*C)/(4*tD**2)*(numpy.log(4*tD)-gamma)

    return term1+term2-term3

if __name__ == "__main__":

    # u = numpy.logspace(-5,0,1000)

    # y1 = integrand(u,1e3,0,-5)
    # y2 = integrand(u,1e3,0,0)
    # y3 = integrand(u,1e3,0,5)
    # y4 = integrand(u,1e3,0,10)
    # y5 = integrand(u,1e3,0,20)

    # pyplot.loglog(u,y1)
    # pyplot.loglog(u,y2)
    # pyplot.loglog(u,y3)
    # pyplot.loglog(u,y4)
    # pyplot.loglog(u,y5)

    # pyplot.show()

    tD = numpy.logspace(2,7,100)

    # model1 = dimensionless_models(tD,C=0,s=0)
    # model2 = dimensionless_models(TD,C=1000,s=10)

    # st = shorttime(tD,0,-5)
    # lt = longtime(tD,0,5)

    ft01 = ramey(tD,0,-5).pwD()
    ft02 = ramey(tD,100,-5).pwD()
    ft03 = ramey(tD,1000,-5).pwD()
    ft04 = ramey(tD,10000,-5).pwD()
    ft05 = ramey(tD,100000,-5).pwD()

    ft06 = ramey(tD,0,0).pwD()
    ft07 = ramey(tD,100,0).pwD()
    ft08 = ramey(tD,1000,0).pwD()
    ft09 = ramey(tD,10000,0).pwD()
    ft10 = ramey(tD,100000,0).pwD()

    ft11 = ramey(tD,0,5).pwD()
    ft12 = ramey(tD,100,5).pwD()
    ft13 = ramey(tD,1000,5).pwD()
    ft14 = ramey(tD,10000,5).pwD()
    ft15 = ramey(tD,100000,5).pwD()

    ft16 = ramey(tD,0,10).pwD()
    ft17 = ramey(tD,100,10).pwD()
    ft18 = ramey(tD,1000,10).pwD()
    ft19 = ramey(tD,10000,10).pwD()
    ft20 = ramey(tD,100000,10).pwD()

    ft21 = ramey(tD,0,20).pwD()
    ft22 = ramey(tD,100,20).pwD()
    ft23 = ramey(tD,1000,20).pwD()
    ft24 = ramey(tD,10000,20).pwD()
    ft25 = ramey(tD,100000,20).pwD()

    figure,axis = pyplot.subplots(nrows=1,ncols=1)

    # axis.plot(tD,st,label="short-time")
    # axis.plot(tD,lt,label="long-time")

    axis.plot(tD,ft01,color="k",linewidth=0.5)
    axis.plot(tD,ft02,color="k",linewidth=0.5)
    axis.plot(tD,ft03,color="k",linewidth=0.5)
    axis.plot(tD,ft04,color="k",linewidth=0.5)
    axis.plot(tD,ft05,color="k",linewidth=0.5)

    axis.plot(tD,ft06,color="r",linewidth=0.5)
    axis.plot(tD,ft07,color="r",linewidth=0.5)
    axis.plot(tD,ft08,color="r",linewidth=0.5)
    axis.plot(tD,ft09,color="r",linewidth=0.5)
    axis.plot(tD,ft10,color="r",linewidth=0.5)

    axis.plot(tD,ft11,color="b",linewidth=0.5)
    axis.plot(tD,ft12,color="b",linewidth=0.5)
    axis.plot(tD,ft13,color="b",linewidth=0.5)
    axis.plot(tD,ft14,color="b",linewidth=0.5)
    axis.plot(tD,ft15,color="b",linewidth=0.5)

    axis.plot(tD,ft16,color="g",linewidth=0.5)
    axis.plot(tD,ft17,color="g",linewidth=0.5)
    axis.plot(tD,ft18,color="g",linewidth=0.5)
    axis.plot(tD,ft19,color="g",linewidth=0.5)
    axis.plot(tD,ft20,color="g",linewidth=0.5)

    axis.plot(tD,ft21,color="m",linewidth=0.5)
    axis.plot(tD,ft22,color="m",linewidth=0.5)
    axis.plot(tD,ft23,color="m",linewidth=0.5)
    axis.plot(tD,ft24,color="m",linewidth=0.5)
    axis.plot(tD,ft25,color="m",linewidth=0.5)

    # axis.plot(model1.tD,model1.pressure_infinite(),label="Pressure1")
    # axis.plot(model1.tD,model1.pressure_infinite_approximation(),linestyle="--",label="Storage1")
    # axis.plot(model2.tD,model2.pressure_infinite(),label="Pressure2")
    # axis.plot(model2.tD,model2.pressure_infinite_approximation(),linestyle="--",label="Storage2")
    # axis.plot(model.tD,model.derivative(),label="Derivative")

    axis.set_ylim((0.1,100))
    axis.set_xlim((1e2,1e7))

    axis.set_xscale("log")
    axis.set_yscale("log")

    axis.grid()

    # axis.legend()

    pyplot.show()