from matplotlib import pyplot

import numpy

from scipy import integrate

from scipy.optimize import root_scalar

from scipy.sparse import csr_matrix as csr
from scipy.sparse.linalg import spsolve as sps

from scipy.special import expi

from scipy.special import j0 as BJ0
from scipy.special import j1 as BJ1
from scipy.special import y0 as BY0
from scipy.special import y1 as BY1

class dimless():
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

class everdingen1949():

    @staticmethod
    def pressure(tD):

        tD = numpy.array(tD).flatten()

        pwD = numpy.zeros(tD.shape)

        for index,time in enumerate(tD):

            umin = numpy.sqrt(1/time)/1e6
            umax = numpy.sqrt(1/time)*1e5

            u = numpy.logspace(numpy.log10(umin),numpy.log10(umax),2000)

            y = everdingen1949.pressure_integrand(u,time)
            z = integrate.simpson(y,u)

            pwD[index] = 4*z/numpy.pi**2

        return pwD

    @staticmethod
    def pressure_integrand(u,tD):
        """Integral kernel of the equation #VI-24, page 313"""

        tD = numpy.array(tD).flatten()

        term1 = 1-numpy.exp(-u**2*tD)
        term2 = BJ1(u)**2+BY1(u)**2

        return term1/(u**3*term2)

    @staticmethod
    def pressure_bounded(tD,R,numterms=2):

        tD,R = numpy.array(tD).flatten(),float(R)

        term1 = 2/(R**2-1)*(1/4.+tD)

        term2 = (3*R**4-4*R**4*numpy.log(R)-2*R**2-1)/(4*(R**2-1)**2)

        tD = tD.reshape((-1,1))

        betan = everdingen1949.pressure_bounded_find_roots(R,numterms)

        # print(f"{R=} {betan=}")

        betan = betan.reshape((1,-1))

        term3a = numpy.exp(-betan**2*tD)*BJ1(betan*R)**2

        term3b = betan**2*(BJ1(betan*R)**2-BJ1(betan)**2)

        term3 = (term3a/term3b).sum(axis=1)

        return term1-term2+2*term3

    @staticmethod
    def pressure_bounded_find_roots(R,numterms=2):

        roots = numpy.empty(numterms)

        for index in range(numterms):

            lower_bound = ((2*index+1)*numpy.pi)/(2*R-2)
            upper_bound = ((2*index+3)*numpy.pi)/(2*R-2)

            bracket = (lower_bound,upper_bound)

            solver = root_scalar(everdingen1949.pressure_bounded_root_function,
                args=(R,),method="brentq",bracket=bracket)

            roots[index] = solver.root

        return roots

    @staticmethod
    def pressure_bounded_root_function(beta,R):

        return BJ1(beta*R)*BY1(beta)-BJ1(beta)*BY1(beta*R)

class agarwal1970():
    """
    tD  : dimensionless time (k*t)/(phi*mu*ct*rw**2)
    CD  : dimensionless wellbore storage constant C/(2*pi*phi*h*ct*rw**2)
    SF  : skin factor, dimensionless
    """

    gamma = 0.57722

    @staticmethod
    def pressure(tD,CD=0,SF=0):
        """Returns the pressure solution to diffusivity equation for the well with
            - finite dimensions,
            - wellbore storage effect,
            - skin effect,
            - infinite reservoir
        Equation # 9, page 281
        """

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        if CD==0:
            return 1/2*(numpy.log(4*tD)-agarwal1970.gamma)+SF

        u = numpy.logspace(-8,1,2000)
        # u = numpy.linspace(1e-8,1e1,100000)

        if SF<0:
            TSF,SF = SF,0
            tD = tD*numpy.exp(2*TSF)
            CD = CD*numpy.exp(2*TSF)
            u = u/numpy.exp(2*TSF)

        pwD = numpy.zeros(tD.shape)

        for index,time in enumerate(tD):
            y = agarwal1970.pressure_integrand(u,time,CD,SF)
            z = integrate.simpson(y,u)

            pwD[index] = 4*z/numpy.pi**2

        return pwD

    @staticmethod
    def pressure_integrand(u,tD,CD=0,SF=0):
        """Integral kernel of the equation # 9, page 281"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        term1 = 1-numpy.exp(-u**2*tD)
        term2 = u*CD*BJ0(u)-(1-CD*SF*u**2)*BJ1(u)
        term3 = u*CD*BY0(u)-(1-CD*SF*u**2)*BY1(u)

        return term1/(u**3*(term2**2+term3**2))

    @staticmethod
    def pressure_lineSource(tD,CD=0,SF=0):
        """Equation # 11, page 281"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        u = numpy.logspace(-8,1,2000)

        if SF<0:
            TSF,SF = SF,0
            tD *= numpy.exp(2*TSF)
            CD *= numpy.exp(2*TSF)
            u /= numpy.exp(2*TSF)

        pwDline = numpy.zeros(tD.shape)

        for index,time in enumerate(tD):
            y = agarwal1970.pressure_lineSource_integrand(u,time,CD,SF)
            z = integrate.simpson(y,u)

            pwDline[index] = z

        return pwDline

    @staticmethod
    def pressure_lineSource_integrand(u,tD,CD=0,SF=0):
        """Internal kernel of the equation # 11, page 281"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        term1 = (1-numpy.exp(-u**2*tD))*BJ0(u)
        term2 = 1-u**2*CD*SF+1/2*numpy.pi*u**2*CD*BY0(u)
        term3 = 1/2*numpy.pi*CD*u**2*BJ0(u)

        return term1/(u*(term2**2+term3**2))

    @staticmethod
    def pressure_shorttime(tD,CD=0,SF=0):
        """Short-time approximation of pressure equation, Equation #14 & 15, page 282"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        if SF==0 and CD!=0:
            term1 = tD-(4*tD**(3/2))/(3*CD*numpy.sqrt(numpy.pi))

            return 1/CD*term1

        elif SF!=0 and CD!=0:
            term1 = tD-(tD**2)/(2*CD*SF)
            term2 = (8*tD**(5/2))/(15*numpy.sqrt(numpy.pi)*CD*SF**2)

            return 1/CD*(term1+term2)

        else:
            raise Warning("Not Implemented")

    @staticmethod
    def pressure_longtime(tD,CD=0,SF=0):
        """Long-time approximation of pressure equation, Equation #13, page 282"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        term1 = numpy.log(4*tD)-agarwal1970.gamma
        term2 = term1+2*SF

        return 1/2*(term2+1/(2*tD)*(term1+1-2*CD*term2))

    @staticmethod
    def derivative(tD,CD=0,SF=0):
        """Equation #26, page 284"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        pwDder = numpy.zeros(tD.shape)

        for index,time in enumerate(tD):
            u = numpy.logspace(-8,-1,1000)
            y = agarwal1970.derivative_integrand(u,time,CD,SF)
            z = integrate.simpson(y,u)

            pwDder[index] = 4*CD*z/numpy.pi**2

        return pwDder

    @staticmethod
    def derivative_integrand(u,tD,CD=0,SF=0):
        """Integral kernel of the equation 26, page 284"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        term1 = numpy.exp(-u**2*tD)
        term2 = u*CD*BJ0(u)-(1-CD*SF*u**2)*BJ1(u)
        term3 = u*CD*BY0(u)-(1-CD*SF*u**2)*BY1(u)

        return term1/(u*(term2**2+term3**2))

    @staticmethod
    def derivative_shorttime(tD,CD=0,SF=0):
        """Short-time approximation, equation 27 & 28, page 284"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        if SF==0 and CD!=0:
            return (1-2*numpy.sqrt(tD/numpy.pi)/CD+1/CD*(1/CD-1/2)*tD)/CD
        elif SF!=0 and CD!=0:
            return (1-tD/(CD*SF))

    @staticmethod
    def derivative_longtime(tD,CD=0,SF=0):
        """Long-time approximation, equation 29, page 284"""

        tD,CD,SF = numpy.array(tD).flatten(),float(CD),float(SF)

        term1 = CD/(2*tD)
        term2 = CD**2/(2*tD**2)*(2*SF-1)
        term3 = CD*(1-2*CD)/(4*tD**2)*(numpy.log(4*tD)-agarwal1970.gamma)

        return (term1+term2-term3)

class finite():

    def __init__(self,R,r=1,deltat=0.1,nsteps=10000,alpha=1,ngrids1=100,ngrids2=100):
        """
        R       : radius of reservoir
        r       : radius of impaired zone

        alpha   : permeability reduction in impaired zone, k_impaired/k_unharmed

        ngrids1 : number of grids in the impaired zone
        ngrids2 : number of grids in the unharmed zone

        deltat  : time steps for the time loop
        nsteps  : number of time steps
        """

        self.R = R
        self.r = r

        self.deltat = deltat
        self.nsteps = nsteps

        self.alpha = alpha

        self.ngrids1 = ngrids1
        self.ngrids2 = ngrids2

        # impaired = numpy.linspace(1,self.r,self.ngrids1+1)
        unharmed = numpy.linspace(self.r,self.R,self.ngrids2+1)

        # self._nodes = numpy.append(impaired,unharmed[1:])
        self._nodes = unharmed

    def pressure(self,CD=0):

        Tmat,Tl0 = self.transmat(CD)

        pform = numpy.zeros(self.radii.shape)

        pwell = numpy.zeros(self.nsteps+1)

        beta2 = self.beta2(CD)

        for index in range(1,self.nsteps+1):

            beta1 = self.beta1(pwell[index-1],CD)

            pform[0] += Tl0*beta1

            pform = sps(Tmat,pform)

            pwell[index] = beta1+beta2*pform[0]

        return pwell[1:]

    def derivative(self):

        pass

    @property
    def nodes(self):

        return self._nodes
    
    @property
    def radii(self):
        
        return (self._nodes[1:]+self._nodes[:-1])/2

    @property
    def deltar(self):

        radii = self.radii

        temp = radii[1:]-radii[:-1]

        temp = numpy.insert(temp,0,radii[0]-self._nodes[0])

        return numpy.append(temp,temp[-1])

    @property
    def transvec(self):

        vectors = {}

        gamma = self.gamma

        radii,deltar = self.radii,self.deltar

        deltar_sum = deltar[:-1]+deltar[1:]
        deltar_mul = deltar[:-1]*deltar[1:]

        vectors["inner"] = -gamma/deltar_sum*(2/deltar[1:]+1/radii)
        vectors["outer"] = -gamma/deltar_sum*(2/deltar[:-1]-1/radii)

        vectors["center"] = gamma/deltar_mul*2+1

        return vectors

    def transmat(self,CD=0):

        vectors = self.transvec

        Tl = vectors["inner"]
        Tc = vectors["center"]
        Tr = vectors["outer"]

        deltar = self.deltar

        N = deltar.size-1

        indices = numpy.arange(N)

        Tmat = csr((N,N))

        Tc[0] -= self.beta2(CD)*Tl[0] # inner boundary correction

        Tc[-1] -= Tr[-1] # outer boundary correction

        Tmat += csr((Tc,(indices,indices)),shape=(N,N))
        Tmat += csr((Tl[1:],(indices[1:],indices[:-1])),shape=(N,N))
        Tmat += csr((Tr[:-1],(indices[:-1],indices[1:])),shape=(N,N))

        return Tmat,Tl[0]

    def beta1(self,pwelln,CD=0):

        theta = CD/self.deltat

        return (1+theta*pwelln)/(self.alpha/self.deltar[0]+theta)

    def beta2(self,CD=0):

        return self.gamma/(self.gamma+CD*self.deltar[0])

    @property
    def skin(self):

        return (1/self.alpha-1)*numpy.log(self.r)

    @property
    def gamma(self):

        return self.alpha*self.deltat

    @property
    def times(self):

        return numpy.linspace(self.deltat,self.nsteps*self.deltat,self.nsteps)
    

if __name__ == "__main__":

    tD = 1e-2

    umin = numpy.sqrt(1/tD)/1e6
    umax = numpy.sqrt(1/tD)*1e5

    u = numpy.logspace(numpy.log10(umin),numpy.log10(umax),2000)

    y1 = everdingen1949.pressure_integrand(u,tD)
    y2 = everdingen1949.pressure_integrand(u,1e8)
    y1 = everdingen1949.pressure_integrand(u,0.0001)

    y1 = agarwal1970.pressure_integrand(u,1e8,1e5,0)
    y2 = agarwal1970.pressure_integrand(u,1e8,1e5,0)
    y2 = agarwal1970.pressure_lineSource_integrand(u,1e3,10000,0)
    y3 = agarwal1970.pressure_lineSource_integrand(u,1e3,10000,5)
    y4 = agarwal1970.pressure_lineSource_integrand(u,1e3,10000,10)
    y5 = agarwal1970.pressure_lineSource_integrand(u,1e3,10000,20)

    print(f"{agarwal1970.pressure(1e8,1e5,0)[0]:8.5f}")

    pyplot.loglog(u,y1)
    pyplot.loglog(u,y1)
    pyplot.loglog(u,y2)
    pyplot.loglog(u,y3)
    pyplot.loglog(u,y4)
    pyplot.loglog(u,y5)

    pyplot.show()



