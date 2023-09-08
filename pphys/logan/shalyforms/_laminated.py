import numpy

class laminated():
	"""The model for analysis of laminated shale proposes a multilayer
	sandwich of alternating layers of clean sand and shale (lithified clay materials).
	The thickness of each layer is small in relation to the vertical resolution of the
	porosity and resistivity devices used to log it. Therefore, both porosity and
	resistivity devices “see” an “average” that is not a true indicator of the
	properties of either the clean-sand laminae or the intervening shales."""

	def __init__(self,archie,phinsh=0.35,phidsh=0.1):

		self._archie = archie

		self.phinsh = phinsh 	# 
		self.phidsh = phidsh 	# apparent density porosity in the shale

	def phie(self,phin,phid):
		"""Calculates the true porosity in the clean sand."""
		upper = (self.phinsh*phid-self.phidsh*phin)
		lower = (self.phinsh-self.phidsh)-(phin-phid)
		return upper/lower

	def vshale(self,phin,phid):
		"""Calculates the shale content in a laminated shale."""
		return (phin-phid)/(self.phinsh-self.phidsh)

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
	def effective_porosity(self):
		return self.phie
	
	@property
	def shale_volume(self):
		return self.vshale

	@property
	def water_saturation(self):
		return self.sw
	