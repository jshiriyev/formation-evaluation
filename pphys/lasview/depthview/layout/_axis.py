from dataclasses import dataclass

import numpy

@dataclass
class Skip:
	lower : int
	upper : int

class Axis():

	def __init__(self,*,cycle=2,minor=None,scale='linear',skip:tuple=None,flip=False):
		"""
		It initializes the axis of box in a track plot:

		cycle 	: sets the number of cycles in the axis
		scale   : axis scale: linear or logarithmic

		minor 	: sets the frequency of minor ticks

		skip 	: how many minor units to skip from lower and
				  upper side, tuple of two integers, values may
				  change in between (0-9), 0 means no skip.
		"""

		self._cycle = cycle
		self._minor = range(1,10) if minor is None else minor

		self._scale = scale

		skip = (0,0) if skip is None else skip

		self._skip  = Skip(*skip)

		self._flip  = flip

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
	def flip(self):
		return self._flip

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
		"""Returns the lower and upper end of axis."""
		if self._flip:
			return (self.upper,self.lower)
			
		return (self.lower,self.upper)

	@property
	def length(self):
		"""Returns the length of axis."""
		return self.upper-self.lower
	
	def __call__(self,data:numpy.ndarray,limit:tuple=None):
		"""Returns the axis values and limit (left,right) for the data."""

		if limit is None:

			limit = self.get_limit((numpy.nanmin(data),numpy.nanmax(data)))

		multp = self.get_multp(limit)

		if self.scale == "linear":
			
			if limit == tuple(sorted(limit)):

				return self.lower+(data-min(limit))*multp,limit

			return self.lower+(max(limit)-data)*multp,limit

		if self.scale == "log":

			return data*multp,tuple([limit/multp for limit in self.limit])

	def get_multp(self,limit:tuple):
		"""Returns the multiplication factor that will bring the limit to the axis scale."""

		if self.scale == "linear":
			return self.floor(self.length/self.get_length(limit))

		if self.scale == "log":
			return 10**self.ceil(-numpy.log10(min(limit)))

	@staticmethod
	def get_limit(limit:tuple):
		"""Returns the limit by using the same power for lower and upper values."""

		power = Axis.get_power(limit)

		lower = Axis.floor(lower,power)
		upper = Axis.ceil(upper,power)
		
		return (lower,upper)

	@staticmethod
	def get_power(limit:tuple):
		"""Returns the tenth power that brings float point next to the first significant digit
		based on the absolutely largest value in the limit."""
		return min([Axis.power(x) for x in limit])

	@staticmethod
	def get_length(limit:tuple):
		"""Returns the length based on limits."""
		return max(limit)-min(limit)

	@staticmethod
	def power(x):
		"""Returns the tenth power that brings float point next to the first significant digit."""
		return -int(numpy.floor(numpy.log10(abs(x))))

	@staticmethod
	def ceil(x,power=None):
		"""Returns the ceil value for the first significant digit."""
		power = Axis.power(x) if power is None else power
		return numpy.ceil(x*10**power)/10**power

	@staticmethod
	def floor(x,power=None):
		"""Returns the floor value for the first significant digit."""
		power = Axis.power(x) if power is None else power
		return numpy.floor(x*10**power)/10**power

	@staticmethod
	def round(x,power=None):
		"""Returns the rounded value for the first significant digit."""
		power = Axis.power(x) if power is None else power
		return numpy.round(x*10**power)/10**power

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

	# print(Axis(cycle=2).get_multp((0.1,0.4)))
	# print(Axis(cycle=3).get_multp((0.1,0.5)))

	xaxis = Axis(cycle=1,skip=(6,0))

	data = numpy.array([0.61,0.7,0.8,0.9,0.99])

	data,limit = xaxis(data,limit=(1,0.6))

	print(data,limit)

	# print(Axis(cycle=1,skip=(6,0)).get_multp((0.1,0.4)))


