from dataclasses import dataclass

@dataclass(frozen=True)
class Theoretical:
    """It is a variogram property dictionary."""
    model       : str   = "spherical"
    sill        : float = None
    radius      : float = None
    nugget      : float = 0.0
    power       : float = 1.0

    def __call__(self,bins):

    	return getattr(self,self.model)(bins)

    @property
    def params(self):
        return {
            "model"     : self.model,
            "sill"      : self.sill,
            "radius"    : self.radius,
            "power"     : self.power,
            "nugget"    : self.nugget
            }

    def powermodel(self,bins):
        """Power Model: """
        
        gamma = numpy.zeros_like(bins)
        
        gamma[bins>0] = self.nugget+(self.sill-self.nugget)*(bins[bins>0])**self.power
        
        return gamma

    def spherical(self,bins):
        """Spherical Model: """
        
        gamma = numpy.zeros_like(bins)
        
        ratio = bins[bins>0]/self.radius
        
        gamma[bins>0] = self.nugget+(self.sill-self.nugget)*(3/2*ratio-1/2*ratio**3)
        
        gamma[bins>self.radius] = self.sill
        
        return gamma

    def exponential(self,bins):
        """Exponential Model: """
        
        gamma = numpy.zeros_like(bins)
        
        ratio = bins[bins>0]/self.radius
        
        gamma[bins>0] = self.nugget+(self.sill-self.nugget)*(1-numpy.exp(-3*ratio))
        
        return gamma

    def gaussian(self,bins):
        """Gaussian Model: """
        
        gamma = numpy.zeros_like(bins)
        
        ratio = bins[bins>0]/self.radius
        
        gamma[bins>0] = self.nugget+(self.sill-self.nugget)*(1-numpy.exp(-3*ratio**2))
        
        return gamma

    def holeeffect(self,bins):
        """Hole-Effect Model: """
        
        gamma = numpy.zeros_like(bins)
        
        ratio = bins[bins>0]/self.radius
        
        gamma[bins>0] = self.nugget+(self.sill-self.nugget)*(1-numpy.sin(ratio)/ratio)
        
        return gamma

    def cubic(self,bins):
        """Cubic Model: """
        
        gamma = numpy.zeros_like(bins)
        
        ratio = bins[bins>0]/self.radius
        
        gamma[bins>0] = self.nugget+(self.sill-self.nugget)*(7*ratio**2-35/4*ratio**3+7/2*ratio**5-3/4*ratio**7)
        
        gamma[bins>self.radius] = self.sill
        
        return gamma

    def cauchy(self,bins):
        """Cauchy Model: """
        
        gamma = numpy.zeros_like(bins)
        
        ratio = bins[bins>0]/self.radius
        
        gamma[bins>0] = self.nugget+(self.sill-self.nugget)*(1-1/(1+ratio**2))
        
        return gamma

    def dewijs(self,bins):
        """Dewijs Model: """
        
        gamma = numpy.zeros_like(bins)
        
        gamma[bins>0] = self.nugget+(self.sill-self.nugget)*numpy.log(bins[bins>0])
        
        return gamma

if __name__ == "__main__":

    pass