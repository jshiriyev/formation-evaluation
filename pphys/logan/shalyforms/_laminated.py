import numpy

from borepy.bhole.pphys.logan._wrappers import trim

class laminated():
	"""The model for analysis of laminated shale proposes a multilayer
	sandwich of alternating layers of clean sand and shale (lithified clay materials).
	The thickness of each layer is small in relation to the vertical resolution of the
	porosity and resistivity devices used to log it. Therefore, both porosity and
	resistivity devices “see” an “average” that is not a true indicator of the
	properties of either the clean-sand laminae or the intervening shales."""

	def __init__(self,archie):

		self._archie = archie

	@trim
	def phisd(self,porosity,vshale):
		"""Returns sand-streak porosity based on measured bulk formation porosity"""
		return porosity/(1-vshale)

	def swn(self,porosity,vshale,rwater,rshale,rtotal):

		term1 = (rwater/rtotal)-vshale*(rwater/rshale)

		formfact = self._archie.a/(porosity**self._archie.m)

		term2 = formfact*(1-vshale)**(self._archie.m-1)

		return term1*term2

	@trim
	def sw(self,porosity,vshale,rwater,rshale,rtotal):
		"""Calculates water saturation based on laminated shale model."""
		return self.swn(porosity,vshale,rwater,rshale,rtotal)**(1/self._archie.n)

	@property
	def archie(self):
		return self._archie

	@property
	def sand_streak_porosity(self):
		return self.phisd
	
	@property
	def water_saturation(self):
		return self.sw
	