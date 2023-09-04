import numpy

class laminated():

	def __init__(self,archie):

		self.archie = archie

	def saturation(self,phie,vshale,rwater,rshale,rtotal):

		sw_clean = self.archie.saturation(phie,rwater,rtotal)
		sw_shale = self.archie.saturation(phie,rwater,rshale)

		return (sw_clean-sw_shale*vshale)/(1-vshale)