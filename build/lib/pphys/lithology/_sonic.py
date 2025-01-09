import numpy

from borepy.utils._wrappers import trim

class sonic():

    def __init__(self,values,depths=None):
        """Initializes sonic transit times and depths for porosity calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

    @trim
    def phi(self,dtmat=55.6,dtfluid=189,dtshale=100):
        """Calculates porosity based on transit times, matrix transit time (dtmat),
        fluid transit time (dtfluid), and (optional) adjacent shale transit time (dtshale)."""
        return (self.values-dtmat)/(dtfluid-dtmat)*(100/dtshale)