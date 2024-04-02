import numpy

from borepy.utils._wrappers import trim

class density():

    def __init__(self,values,depths=None,rhofluid=1.0):
        """Initializes bulk density values and depths for porosity calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

        self.rhofluid = rhofluid

    @trim
    def phi(self,rhomat=2.65,rhofluid=1.0):
        """Calculates porosity based on bulk density, matrix density (rhomat), and fluid density (rhofluid)."""
        return (rhomat-self.values)/(rhomat-rhofluid)

    @trim
    def phie(self,phid,vshale,phidsh=0.1):
        """Calculates shale corrected density porosity based on shale volume (vshale) and
        phidsh (density porosity at shale)."""
        return phid-vshale*phidsh
