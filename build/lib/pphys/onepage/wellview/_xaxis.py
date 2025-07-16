from dataclasses import dataclass, field

import numpy as np

from ._unary import Unary

@dataclass(frozen=True)
class XAxisDict:
	"""
	A frozen dataclass representing the X-axis of a plane in a track layout.

	limit 	: Range of the axis (lower, upper). If not provided, a default is
			chosen based on the `scale`
	
	major 	: interval between major ticks on the axis.
	minor 	: Interval between minor ticks on the axis.

	scale	: axis scale: either 'linear' or 'log10', check the link below
			https://matplotlib.org/stable/users/explain/axes/axes_scales.html
			for the available scales in matplotlib.

	spot 	: Index in the layout for axis positioning.
	grid 	: To create major and minor grids or not.

	"""
	limit 	: tuple[float, float] = None

	major 	: int = 10
	minor 	: int|range = 1

	scale 	: str = "linear"

	spot 	: int = None

	grid 	: bool = True

	def __post_init__(self):

		if self.limit is not None:
			return

		if self.scale=="linear":
			object.__setattr__(self,'limit',(0,20))
		elif self.scale=="log10":
			object.__setattr__(self,'limit',(1,100))

	@property
	def lower(self):
		"""Return the lower bound of the axis range."""
		return min(self.limit)

	def lower_off(self,perc=2.):
		"""Return the perc(%) off of the lower bound."""
		if self.scale=="linear":
			return self.lower+self.length*perc/100.

		if self.scale=="log10":
			return self.lower**(1-perc/100)*self.upper**(perc/100.)

	@property
	def upper(self):
		"""Return the upper bound of the axis range."""
		return max(self.limit)

	def upper_off(self,perc=2.):
		"""Return the perc(%) off of the upper bound."""
		if self.scale=="linear":
			return self.upper-self.length*perc/100.

		if self.scale=="log10":
			return self.upper**(1-perc/100)*self.lower**(perc/100.)

	@property
	def length(self):
		"""Return the total span of the axis (upper - lower)."""
		return self.upper-self.lower

	@property
	def middle(self):
		"""Return the midpoint of the 'limit' range depending on the scale."""
		if self.scale=="linear":
			return np.mean(self.limit)

		if self.scale=="log10":
			if any(val <= 0 for val in self.limit):
				raise ValueError("All limit values must be positive for log10 scale.")
			return float(10**np.mean(np.log10(self.limit)))

		raise ValueError("scale must be either 'linear' or 'log10'.")

	@property
	def flipped(self):
		"""Return True if axis values are decreasing (flipped direction)."""
		return self.limit != tuple(sorted(self.limit))

	@property
	def unary(self):
		"""Return the Unary class for external operations involving this axis."""
		return Unary

if __name__ == "__main__":

	axis = BaseAxis(scale="log")

	print(axis.scale)
	print(axis)