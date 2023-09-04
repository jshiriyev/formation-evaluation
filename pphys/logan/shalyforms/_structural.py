import numpy

class structural():

	def __init__(self,archie):

		self.archie = archie
	
	def saturation(self,phie,vshale,rshale,rtotal):

		sw_clean = self.archie.saturation(phie,rwater,rtotal)
		sw_shale = self.archie.saturation(phie,rwater,rtotal)

		return sw_clean-sw_shale*vshale