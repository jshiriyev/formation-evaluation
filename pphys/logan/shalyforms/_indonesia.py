import numpy

from borepy.pphys.logan._wrappers import trim

class indonesia():

	def __init__(self,archie):

		self._archie = archie

	def swn(self,porosity,vshale,rwater,rshale,rtotal,shalepower):
		"""Calculates water saturation to the power n based on Poupon-Leveaux Indonesia model"""
		formfact = self._archie.a/(porosity**self._archie.m)

		swnclean = formfact*(rwater/rtotal)
		swnshale = vshale**(-2*shalepower)*(rshale/rtotal)
		
		return (swnclean**(-1/2)+swnshale**(-1/2))**(-2)

	@trim
	def sw(self,porosity,vshale,rwater,rshale,rtotal,shalepower=None):
		"""Calculates water saturation based on Poupon-Leveaux Indonesia model"""

		if shalepower is None:
			shalepower = 1-vshale/2

		swntotal = self.swn(porosity,vshale,rwater,rshale,rtotal,shalepower)

		return numpy.power(swntotal,1/self._archie.n)

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