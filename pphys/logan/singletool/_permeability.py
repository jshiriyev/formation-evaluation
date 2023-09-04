import numpy

class conventional():

    def __init__(self,phi,swirr,depths=None):
        """Initializes fractional porosity (phi) and fractional irreducible water saturation (swirr)
        values and depths for permeability calculations. If depths values are provided, they must be
        the same size as those values."""

        self.phi = phi
        self.swirr = swirr

        self.depths = depths

    def timur(self):
        """Calculates permeaility (mD) based on Timur (1968) equation."""
        return 8581*self.phi**4.4/self.swirr**2

    def oils(self):
        """Calculates permeaility (mD) based on Wyllie and Rose (1950) equation."""
        return (250*self.phi**3/self.swirr)**2

    def drygas(self):
        """Calculates permeaility (mD) based on Wyllie and Rose (1950) equation."""
        return (79*self.phi**3/self.swirr)**2

    def schlumberger(self):
        """Calculates permeaility (mD) based on Schlumberger Perm-1 equation."""
        return 10000*self.phi**4.5/self.swirr**2

    def oilwater(self,height,rhow=1,rhoo=0.8):
        """Calculates oil-water transition zone permeaility (mD) based on
        Raymer and Freeman (1984) equation.

        height   : is the height (ft) from free-water level to the top of the transition zone

        rhow     : water density (g/cm3)
        rhoo     : oil density (g/cm3)
        """
        return self.phi*(122/h/(rhow-rhoo))**2

    def gaswater(self,height,rhow=1,rhog=0.1):
        """Calculates gas-water transition zone permeaility (mD) based on
        Raymer and Freeman (1984) equation.

        height   : is the height (ft) from free-water level to the top of the transition zone

        rhow     : water density (g/cm3)
        rhog     : gas density (g/cm3)
        """
        return self.phi*(140/h/(rhow-rhog))**2

class nmr():

    def __init__(self,mphi,ffi,mcbw,depths=None):
        """Initializes NMR values and depths for porosity calculations.
        If depths values are provided, they must be the same size as those values.

        mphi :  NMR effective porosity, decimal
        ffi  :  NMR free-fluid index
        mcbw :  NMR clay bound water
        """

        self.mphi = mphi
        self.ffi = ffi
        self.mcbw = mcbw

        self.depths = depths

    def coates(self,bvi,C=10):
        """Calculates permeability (mD) based on Timur-Coates or Coates model.
        
        bvi     : capillary bound water
        C       : formation dependent variable, 10 is frequently used
        """
        return (self.mphi*100/C)**4*(self.ffi/bvi)**2

    def sdr(self,T2gm,a=4.6):
        """Calculates permeability (mD) based on Schlumberger-Doll-Research model.
        
        T2gm    : is the geometric mean of the T2 distribution, ms
        a       : formation dependent variable

        The SDR model works very well in water-saturated zones. In the presence of
        oil or oil filtrates, the mean T2 is skewed toward the T2bulk, because of
        the effects of partial polarization, leading to an overestimate of permeability.

        In unflushed gas zones, mean-T2 values are too low relative to the flushed-gas zone;
        and permeability is underestimated. Because hydrocarbon effects on T2gm are not correctable,
        the SDR model fails in hydrocarbon-bearing formations.

        The Coates and SDR models represent matrix permeability and, therefore, are not
        applicable to estimation of permeability in fractured formations.
        """
        return a*(T2gm)**2*(self.mphi)**4*1000