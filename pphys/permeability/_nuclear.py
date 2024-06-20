class nuclear():

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