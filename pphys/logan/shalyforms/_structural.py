import numpy

class structural_shale():

	def __init__(self,archie):

		self._archie = archie

		self.phinsh = phinsh 	# 
		self.phidsh = phidsh 	# apparent density porosity in the shale

	def phie(self,phin,phid):
		"""Calculates the effective porosity."""
		return (self.phinsh*phid-self.phidsh*phin)/(self.phinsh-self.phidsh)

	def vshale(self,phin,phid):
		"""Calculates the shale content in a structural shale model."""
		return (phin-phid)/(self.phinsh*(1-phid)-self.phidsh*(1-phin))
	
	def sw(self,phie,vshale,rwater,rshale,rtotal):
		"""Calculates water saturation based on structural shale model."""

		swn_clean = self._archie.swn(phie,rwater,rtotal)
		swn_shale = self._archie.swn(phie,rwater,rtotal)

		swn_structural = swn_clean-swn_shale*vshale

		return numpy.power(swn_structural,1/self._archie.n)

	@property
	def archie(self):
		return self._archie

	@property
	def effective_porosity(self):
		return self.phie
	
	@property
	def shale_volume(self):
		return self.vshale

	@property
	def water_saturation(self):
		return self.sw
	