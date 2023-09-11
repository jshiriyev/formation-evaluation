import numpy

from borepy.pphys.logan._wrappers import trim

class indonesia():

	def __init__(self,archie):

		self._archie = archie

	@trim
	def sw(self,phie,vshale,rwater,rshale,rtotal):
		"""Calculates water saturation based on Poupon-Leveaux Indonesia model"""

		term1 = (vshale**(2-vshale)/rshale)**(1/2)
		term2 = ((phie**self._archie.m)/(self._archie.a*rwater))**(1/2)

		swn_indonesia = 1/rtotal/(term1+term2)**2

		return numpy.power(swn_indonesia,1/self._archie.n)

	def bwv(self,porosity,swater):
		"""Calculates bulk water volume."""
		return porosity*swater

	@property
	def archie(self):
		return self._archie

	@property
	def water_saturation(self):
		return self.sw

	@property
	def bulk_water_volume(self):
		return self.bwv