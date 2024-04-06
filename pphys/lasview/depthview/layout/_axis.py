from dataclasses import dataclass

import numpy

@dataclass
class Skip:
	lower : int
	upper : int

class Axis():

	def __init__(self,*,cycle=2,minor=None,scale='linear',skip:tuple=None):
		"""
		It initializes axis of box in track plot:

		cycle 	: sets the number of cycles in the axis
		scale   : axis scale: linear or logarithmic

		minor 	: sets the frequency of minor ticks

		skip 	: how many minor units to skip from lower and
				  upper side, tuple of two integers
		"""

		self._cycle = cycle
		self._minor = range(1,10) if minor is None else minor

		self._scale = scale

		skip = (0,0) if skip is None else skip

		self._skip = Skip(*skip)

	@property
	def cycle(self):
		return self._cycle

	@property
	def scale(self):
		return self._scale

	@property
	def minor(self):
		return self._minor

	@property
	def skip(self):
		return self._skip

	@property
	def lower(self):
		"""Returns the lower end value of axis."""
		if self.scale == "linear":
			return 0+self.skip.lower

		if self.scale == "log":
			return 1+self.skip.lower
	
	@property
	def upper(self):
		"""Returns the upper end value of axis."""
		if self.scale == "linear":
			return self.cycle*10+self.skip.upper

		if self.scale == "log":
			return (1+self.skip.upper)*10**self.cycle
	
	@property
	def limit(self):
		return (self.lower,self.upper)

	@property
	def length(self):
		return self.get_length(self.limit)
	
	def __call__(self,data:numpy.ndarray,limit:tuple=None,reverse:bool=False):

		multp = self.get_multp(limit)

		if reverse:
			return self.upper-data*multp,numpy.flip(numpy.array(self.limit)/multp)

		return data*multp,numpy.array(self.limit)/multp

	def get_sorted(self,data:numpy.ndarray=None,limit:tuple=None):

		if limit is None:

			lower = self.floor(numpy.nanmin(data))
			upper = self.ceil(numpy.nanmax(data))
			
			return (upper,lower) if reverse else (lower,upper)

		return self.get_limit(limit)

	def get_multp(self,limit:tuple):

		if self.scale == "linear":
			return self.floor(self.length/self.get_length(limit))

		if self.scale == "log":
			return 10**self.ceil(-numpy.log10(min(limit)))

	@staticmethod
	def get_length(limit:tuple):
		"""Returns the length based on limits."""
		return max(limit)-min(limit)

	@staticmethod
	def isreverse(limit:tuple):
		"""Returns flag based on the limit values order."""
		return True if limit[0]>limit[-1] else False

	@staticmethod
	def power(x):
		"""Returns the tenth power that brings float point next to the first significant digit."""
		return -int(numpy.floor(numpy.log10(abs(x))))

	@staticmethod
	def ceil(x):
		"""Returns the ceil value for the first significant digit."""
		return numpy.ceil(x*10**Axis.power(x))/10**Axis.power(x)

	@staticmethod
	def floor(x):
		"""Returns the floor value for the first significant digit."""
		return numpy.floor(x*10**Axis.power(x))/10**Axis.power(x)

	@staticmethod
	def round(x):
		"""Returns the rounded value for the first significant digit."""
		return numpy.round(x*10**Axis.power(x))/10**Axis.power(x)

if __name__ == "__main__":

	xaxis = Axis(scale="log",skip=(1,3))

	# print(xaxis.skip.upper)

	# print(xaxis.limit)

	# print(Axis.ceil(0.03573465))
	# print(Axis.floor(0.03573465))
	# print(Axis.round(0.03573465))

	# print(Axis.ceil(3459))
	# print(Axis.floor(3459))
	# print(Axis.round(3459))

	print(Axis(cycle=2).get_multp((0.1,0.4)))
	print(Axis(cycle=3).get_multp((0.1,0.5)))
	print(Axis(cycle=1,skip=(6,0)).get_multp((0.1,0.4)))


