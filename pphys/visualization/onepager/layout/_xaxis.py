from dataclasses import dataclass, field

import numpy

class Unary:

	@staticmethod
	def power(x:float):
		"""
		Returns the tenth power that brings float point next to the first
		significant digit.
		"""
		return -int(numpy.floor(numpy.log10(abs(x))))

	@staticmethod
	def ceil(x:float,power:int=None):
		"""
		Returns the ceil value for the first significant digit by default.
		
		If the power is specified, it is used as a factor before ceiling.
		"""
		if power is None:
			power = Curve.upower(x)

		return (numpy.ceil(x*10**power)/10**power).tolist()

	@staticmethod
	def floor(x:float,power:int=None):
		"""
		Returns the floor value for the first significant digit by default.
		
		If the power is specified, it is used as a factor before flooring.
		"""
		if power is None:
			power = Curve.upower(x)

		return (numpy.floor(x*10**power)/10**power).tolist()

	@staticmethod
	def round(x:float,power:int=None):
		"""Returns the rounded value for the first significant digit."""
		
		if power is None:
			power = Curve.upower(x)

		return (numpy.round(x*10**power)/10**power).tolist()

@dataclass(frozen=True)
class Xaxis:
	"""
	It initializes the axis of plane in a track:

	limit 	: lower and upper values of the axis
	
	major 	: sets the frequency of major ticks
	minor 	: sets the frequency of minor ticks

	scale   : axis scale: linear or log10, check the link below
			https://matplotlib.org/stable/users/explain/axes/axes_scales.html
			for the available scales in matplotlib.

	spot 	: location of axis in the layout, int
			index of trail in the layout

	"""
	limit 	: tuple[float] = None

	major 	: int = 10
	minor 	: range = range(1,10)

	scale 	: str = "linear"

	spot 	: int = None

	def __post_init__(self):

		if self.limit is not None:
			return

		if self.scale=="linear":
			object.__setattr__(self,'limit',(0,20))
		elif self.scale=="log10":
			object.__setattr__(self,'limit',(1,100))

	@property
	def lower(self):
		return min(self.limit)

	@property
	def upper(self):
		return max(self.limit)

	@property
	def length(self):
		return self.upper-self.lower
	
	@property
	def flip(self):
		return self.limit != tuple(sorted(self.limit))

	@property
	def unary(self):
		return Unary

if __name__ == "__main__":

	axis = BaseAxis(scale="log")

	print(axis.scale)
	print(axis)