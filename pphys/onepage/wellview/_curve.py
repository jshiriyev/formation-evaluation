from dataclasses import dataclass, field

import lasio
import numpy

from ._unary import Unary
from ._xaxis import XAxisDict

@dataclass(frozen=True)
class Datum():

	array 	: lasio.CurveItem

	lower 	: float | None = None
	upper 	: float | None = None

	flip 	: bool = False

	power 	: int | None = None

	def __post_init__(self):
		"""Assigns corrected lower and upper values."""
		if numpy.all(numpy.isnan(self.array)):
			lower, upper = float('nan'), float('nan')
		else:
			lower = numpy.nanmin(self.array).tolist()
			upper = numpy.nanmin(self.array).tolist()

		lower = lower if self.lower is None else self.lower
		upper = upper if self.upper is None else self.upper

		power = min([Unary.power(lower),Unary.power(upper)])
		power = power if self.power is None else self.power

		lower,upper = Unary.floor(lower,power),Unary.ceil(upper,power)

		if self.lower is None:
			object.__setattr__(self,'lower',lower)

		if self.upper is None:
			object.__setattr__(self,'upper',upper)

		if self.power is None:
			object.__setattr__(self,'power',power)

	@property
	def limit(self):
		"""Returns the limit based on lower and upper values."""
		return (self.upper,self.lower) if self.flip else (self.lower,self.upper)

	@property
	def length(self):
		"""Returns the length based on limits."""
		return float('nan') if self.lower is None or self.upper is None else self.upper-self.lower
	
	@property
	def unary(self):
		"""Return the Unary class for external operations involving this axis."""
		return Unary

@dataclass(frozen=True)
class Curve(Datum):

	colid 	: int | None = None
	rowid 	: int | None = None

	trail	: numpy.ndarray | None = field(
		init = False,
		repr = False,
		default = None,
		)

	def __call__(self,xaxis:XAxisDict):
		"""Returns the axis values and limit (left,right) for the data."""

		if xaxis.scale == "linear":
			multp = Unary.floor(xaxis.length/self.length)
		elif xaxis.scale == "log10":
			lower = float('nan') if self.lower is None else self.lower
			multp = 10**Unary.ceil(-numpy.log10(lower))

		if xaxis.scale == "linear":
			trail = xaxis.lower+(self.upper-self.array if self.flip else self.array-self.lower)*multp
		elif xaxis.scale == "log10":
			trail = self.array*multp

		object.__setattr__(self,'trail',trail)

		return self

if __name__ == "__main__":

	a = Curve([0.1,2,9],upper=10)
	print(a.unary.power(1312))

	object.__setattr__(a,'trail',7)

	print(a.array)
	print(a.lower)
	print(a.upper)
	print(a.power)
	print(a.trail)