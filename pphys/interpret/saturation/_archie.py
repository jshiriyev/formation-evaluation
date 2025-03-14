from dataclasses import dataclass

import numpy

from borepy.utils._wrappers import trim

@dataclass
class archie:
    """It is the implementation of Archie's equation."""
    a  : float = 1.00 # tortuosity constant
    m  : float = 2.00 # cementation exponent
    n  : float = 2.00 # saturation exponent

    def ff(self,porosity):
        """Calculates formation factor based on Archie's equation."""
        return self.a/(porosity**self.m)

    def swn(self,porosity,rwater,rtotal):
        """Calculates water saturation to the power n based on Archie's equation."""
        return self.ff(porosity)*rwater/rtotal

    @trim
    def sw(self,porosity,rwater,rtotal):
        """Calculates water saturation based on Archie's equation."""
        return numpy.power(self.swn(porosity,rwater,rtotal),1/self.n)

    def bwv(self,porosity,swater):
        """Calculates bulk water volume."""
        return porosity*swater

    @property
    def formation_factor(self):
        return self.ff

    @property
    def water_saturation_to_n(self):
        return self.swn
    
    @property
    def water_saturation(self):
        return self.sw

    @property
    def bulk_water_volume(self):
        return self.bwv