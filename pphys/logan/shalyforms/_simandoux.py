import numpy

from scipy.optimize import root_scalar

from borepy.utils._wrappers import trim

class simandoux():

	def __init__(self,archie):

		self._archie = archie

	@trim
	def sw(self,porosity,vshale,rwater,rshale,rtotal):
		"""Calculates water saturation based on simandoux model."""

		size = porosity.size

		saturation = numpy.zeros(size)

		vshale = set_value_iterable(vshale,size)
		rwater = set_value_iterable(rwater,size)
		rshale = set_value_iterable(rshale,size)
		rtotal = set_value_iterable(rtotal,size)

		zipped = zip(porosity,vshale,rwater,rshale,rtotal)

		for index,(por,vsh,rw,rsh,rt) in enumerate(zipped):

			solver = root_scalar(
				simandoux.sw_forward,
				method = 'newton', x0 = 1,
				fprime = simandoux.sw_derivative,
				args = (por,vsh,rw,rsh,rt,
					self._archie.a,
					self._archie.m,
					self._archie.n,
					),
				)

			saturation[index] = solver.root

		return saturation

	def bwv(self,porosity,swater):
		"""Calculates bulk water volume."""
		return porosity*swater

	@staticmethod
	def sw_forward(sw,por,vsh,rw,rsh,rt,a,m,n):
		"""Implementing forward saturation equation for each depth point
		based on the Simandoux model, A*(Sw)**n+B*(Sw)+C = 0"""
		return (por**m)/(a*rw)*sw**n+vsh/rsh*sw-1/rt

	@staticmethod
	def sw_derivative(sw,por,vsh,rw,rsh,rt,a,m,n):
		"""Implementing derivative of forward saturation equation for each
		depth point based on the Simandoux model"""
		return n*(por**m)/(a*rw)*sw**(n-1)+vsh/rsh

	@property
	def archie(self):
		return self._archie

	@property
	def water_saturation(self):
		return self.sw

	@property
	def bulk_water_volume(self):
		return self.bwv

class totalshale():

	def __init__(self,archie):
		"""It is a modified Simandoux model for the saturation
		calculations in shaly formations."""

		self._archie = archie

	@trim
	def sw(self,porosity,vshale,rwater,rshale,rtotal):
		"""Calculates water saturation based on total shale model."""
		size = porosity.size

		saturation = numpy.zeros(size)

		vshale = set_value_iterable(vshale,size)
		rwater = set_value_iterable(rwater,size)
		rshale = set_value_iterable(rshale,size)
		rtotal = set_value_iterable(rtotal,size)

		zipped = zip(porosity,vshale,rwater,rshale,rtotal)

		for index,(por,vsh,rw,rsh,rt) in enumerate(zipped):

			solver = root_scalar(
				totalshale.sw_forward,
				method = 'newton', x0 = 1,
				fprime = totalshale.sw_derivative,
				args = (por,vsh,rw,rsh,rt,
					self._archie.a,
					self._archie.m,
					self._archie.n,
					),
				)

			saturation[index] = solver.root

		return saturation

	def bwv(self,porosity,swater):
		"""Calculates bulk water volume."""
		return porosity*swater

	@staticmethod
	def sw_forward(sw,por,vsh,rw,rsh,rt,a,m,n):
		"""Implementing forward saturation equation for each depth point
		based on the total shale model, A*(Sw)**n+B*(Sw)+C = 0"""
		return (por**m)/(a*rw)/(1-vsh)*sw**n+vsh/rsh*sw-1/rt

	@staticmethod
	def sw_derivative(sw,por,vsh,rw,rsh,rt,a,m,n):
		"""Implementing derivative of forward saturation equation for each
		depth point based on the total shale model"""
		return n*(por**m)/(a*rw)/(1-vsh)*sw**(n-1)+vsh/rsh

	@property
	def archie(self):
		return self._archie

	@property
	def water_saturation(self):
		return self.sw

	@property
	def bulk_water_volume(self):
		return self.bwv

def set_value_iterable(entry,size):

	try:
		iter(entry)
	except TypeError:
		entry = [entry for _ in range(size)]

	return entry

if __name__ == "__main__":

	class archie:
		pass

	archie.a = 1
	archie.m = 2
	archie.n = 2

	phie = numpy.array([0.1,0.15,0.2])
	vshale = numpy.array([0.5,0.7,0.3])
	rwater = numpy.array([0.02,0.01,0.015])
	rshale = numpy.array([0.05,0.05,0.05])
	rtotal = numpy.array([1,5,2])

	model = simandoux(archie)
	sw = model.sw(phie,vshale,rwater,rshale,rtotal)

	# print(simandoux.sw_forward(1,0.1,0.5,0.02,0.05,1,1,2,2))

	print(sw)