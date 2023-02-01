import numpy

class OnePhase():

    UGC = 8.314     # universal gas constant

    def __init__(self,T=293.15):

        self.Pipe = get_Pipes()()

        self.Fluid = Fluids(number=1)

        self.temperature = T

    def set_uppressure(self,P_upstream):

        self.Pup = P_upstream

    def set_downpressure(self,P_downstream):

        self.Pdown = P_downstream

    def set_Reynolds(self,velocity=None,mass_rate=None):

        if velocity is not None:
            self.velocity = velocity
            self.reynolds_number = self.Fluid.density[0]*velcoity*self.Pipe.diameter/self.Fluid.viscosity[0]
        elif mass_rate is not None:
            self.mass_rate = mass_rate
            self.reynolds_number = mass_rate*self.Pipe.diameter/self.Fluid.viscosity[0]/self.Pipe.csa

    def set_friction(self,method="simple",pipe_smoothness=True):

        if pipe_smoothness:
            if method=="simple":
                if 2.5e-3<self.reynolds_number and self.reynolds_number<1e5:
                    print("The selected method is correct for the calculated Reynold's number.")
                else:
                    print("Check the conditions at which this friction factor equation can be used.")
                self.phi = 0.0396*self.reynolds_number**(-0.25)
        
    def incompressible(self):

        pass

    def DarcyWeisbach(self,NReynolds,tol=1e-5):

        if NReynolds<1000:
            
            f = 64/NReynolds
            
        elif NReynolds>2000:
            
            f0 = 64/NReynolds
            
            converged = False
            
            while not converged:
                
                Lp = (self.epsilon)/(3.7*self.diameter)
                Rp = (2.51)/(NReynolds*np.sqrt(f0))
                
                f1 = 1/(-2*np.log10(Lp+Rp))**2
                
                if np.abs(f1-f0)>tol:
                    
                    f0 = f1
                    
                else:
                    
                    converged = True

    def HazenWilliams(self,C=120):

        k = 0.849

        Rhydraulic = self.diameter/4

        f = ((self.average_velocity)/(k*C*Rhydraulic**0.63))**(1/0.54)

    def compressible(self,P2,P1):

        rho1 = (P1*self.Fluid.molarweight[0])/(self.UGC*self.temperature)
        rho2 = (P2*self.Fluid.molarweight[0])/(self.UGC*self.temperature)

        nu1 = 1/rho1
        nu2 = 1/rho2

        Dp = P1**2-P2**2
        Rp = np.log(P1/P2)
        Ft = 4*self.phi*self.Pipe.length/self.Pipe.diameter
        
        G = self.Pipe.csa*np.sqrt(Dp/(2*P1*nu1*(Rp+Ft)))

        return G

    def set_criticalRatio(self):

        def objective(wc,LHS):
            RHS = (1/wc)**2-(np.log(1/wc))**2-1
            return (RHS-LHS)**2

        LHS = 8*self.phi*self.Pipe.length/self.Pipe.diameter

        self.omega = minimize_scalar(objective,args=(LHS,),bounds=((1e-5,1)),method='bounded').x

    def get_downpressure(self):

        def objective(P2):

            Gc = self.compressible(P2,self.Pup)

            return (self.mass_rate-Gc)**2

        self.Pup_critical = self.omega*self.Pup

        print("Downstream pressure is {} psi when mass rate is maximum".format(self.Pup_critical/6894.76))

        Pdown = minimize_scalar(objective,bounds=((self.Pup_critical,self.Pup)),method='bounded').x

        print("Downstream pressure is {} psi when mass rate is {} kg/sec".format(Pdown/6894.76,self.mass_rate))

        return Pdown
