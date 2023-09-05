import numpy

class laminated_shale():

	def __init__(self,archie):

		self._archie = archie

	def sw(self,phie,vshale,rwater,rshale,rtotal):
		"""Calculates water saturation based on laminated shale model."""

		swn_clean = self._archie.swn(phie,rwater,rtotal)
		swn_shale = self._archie.swn(phie,rwater,rshale)

		swn_laminated = (swn_clean-swn_shale*vshale)/(1-vshale)

		return numpy.power(swn_laminated,1/self._archie.n)

	@property
	def archie(self):
		return self._archie

	@property
	def water_saturation(self):
		return self.sw
	