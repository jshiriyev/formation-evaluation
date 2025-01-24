from dataclasses import dataclass, field

import lasio

import numpy

from .layout._datum import Datum
from .layout._xaxis import Xaxis

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