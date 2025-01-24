import numpy

class porosity():

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