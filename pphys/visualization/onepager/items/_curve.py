from dataclasses import dataclass, field

import lasio
import numpy

from .layout._xaxis import Xaxis

@dataclass(frozen=True)
class Datum:

	array 	: lasio.CurveItem

	lower 	: float = None
	upper 	: float = None

	flip 	: bool = False

	power 	: int = None

	def __post_init__(self):
		"""Assigns corrected lower and upper values."""

		lower = numpy.nanmin(self.array).tolist()
		upper = numpy.nanmax(self.array).tolist()

		lower = lower if self.lower is None else self.lower
		upper = upper if self.upper is None else self.upper

		power = min([self.unary.power(lower),self.unary.power(upper)])

		power = power if self.power is None else self.power

		lower,upper = self.unary.floor(lower,power),self.unary.ceil(upper,power)

		if self.lower is None:
			object.__setattr__(self,'lower',lower)

		if self.upper is None:
			object.__setattr__(self,'upper',upper)

		if self.power is None:
			object.__setattr__(self,'power',power)

	@property
	def limit(self):
		"""
		Returns the limit based on lower and upper values.
		"""
		return (self.upper,self.lower) if self.flip else (self.lower,self.upper)

	@property
	def length(self):
		"""
		Returns the length based on limits.
		"""
		return self.upper-self.lower

@dataclass(frozen=True)
class Curve(Datum):

	colid 	: int = None
	rowid 	: int = None

	trail	: numpy.ndarray = field(
		init = False,
		repr = False,
		default = None,
		)

	def __call__(self,xaxis:Xaxis):
		"""Returns the axis values and limit (left,right) for the data."""

		if xaxis.scale == "linear":
			multp = self.unary.floor(xaxis.length/self.length)
		elif xaxis.scale == "log10":
			multp = 10**self.unary.ceil(-numpy.log10(self.lower))

		if xaxis.scale == "linear":
			trail = xaxis.lower+(self.upper-self.array if self.flip else self.array-self.lower)*multp
		elif xaxis.scale == "log10":
			trail = self.array*multp

		object.__setattr__(curve,'trail',trail)

		return curve

if __name__ == "__main__":

	print(Curve.upower(1312))

	a = Curve([0.1,2,9],upper=10)

	object.__setattr__(a,'trail',7)

	print(a.array)
	print(a.lower)
	print(a.upper)
	print(a.power)
	print(a.trail)