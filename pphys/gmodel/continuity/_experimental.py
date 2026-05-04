from dataclasses import dataclass

@dataclass(frozen=True)
class Experimental:
    """It is a variogram property dictionary."""
    lagdist     : float = None
    lagtol      : float = None
    outbound    : float = None
    azimuth     : float = 0.0
    azimtol     : float = numpy.pi
    bdwidth     : float = numpy.inf

    @property
    def params(self):
        return {
            "lagdist"   : self.lagdist,
            "lagtol"    : self.lagtol,
            "outbound"  : self.outbound
            }
    
    @property
    def anisoparams(self):
        return {
            "azimuth"   : numpy.radians(self.azimuth),
            "azimtol"   : numpy.radians(self.azimtol),
            "bdwidth"   : self.bdwidth
            }