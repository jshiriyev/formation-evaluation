class indonesia():

	def __init__(self,archie):

		self._archie = archie

	def sw(self,phie,vshale,rwater,rshale,rtotal):
		"""Calculates water saturation based on Poupon-Leveaux Indonesia model"""

		term1 = (vshale**(2-vshale)/rshale)**(1/2)
		term2 = ((phie**self._archie.m)/(self._archie.a*rwater))**(1/2)

		swn_indonesia = 1/rtotal/(term1+term2)**2

		return numpy.power(swn_indonesia,1/self._archie.n)

	@property
	def archie(self):
		return self._archie

	@property
	def water_saturation(self):
		return self.sw