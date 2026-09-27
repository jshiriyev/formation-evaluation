"""The horizontal axis of a track: value range, scale, grid spacing."""

from dataclasses import dataclass

import numpy as np

from ._unary import decimals, floor

SCALES = ("linear", "log10")

# Default range of a track for each scale.
_LIMITS = {"linear": (0.0, 20.0), "log10": (1.0, 100.0)}


@dataclass(frozen=True)
class XAxisDict:
	"""The horizontal axis of one track.

	limit 	: (left, right) values of the track. A left value larger than the
			right one flips the track, e.g. (0.45, -0.15) for neutron
			porosity. Defaults to (0, 20) on a linear and (1, 100) on a log10
			scale.

	major 	: spacing of the major grid lines on a linear scale. Defaults to
			five minor spacings. Unused on a log10 scale, whose major lines
			fall on the decades.
	minor 	: spacing of the minor grid lines on a linear scale. Defaults to
			a tenth of the range, rounded down at its first significant digit:
			10 for (0, 150). On a log10 scale, the multiples of each decade
			that get a minor line, by default 1 to 9.

	scale 	: 'linear' or 'log10'.

	grid 	: whether the track draws grid lines, along and across it.

	"""
	limit 	: tuple[float, float] | None = None

	major 	: float | None = None
	minor 	: float | tuple[float, ...] | None = None

	scale 	: str = "linear"

	grid 	: bool = True

	def __post_init__(self):

		if self.scale not in SCALES:
			raise ValueError(f"scale must be one of {SCALES}, not {self.scale!r}.")

		limit = _LIMITS[self.scale] if self.limit is None else self.limit

		if len(limit)!=2 or limit[0]==limit[1]:
			raise ValueError(f"limit must be two different values, not {limit!r}.")

		if self.scale=="log10" and min(limit)<=0:
			raise ValueError(f"A log10 track needs positive limits, not {limit!r}.")

		object.__setattr__(self,'limit',(float(limit[0]),float(limit[1])))

		if self.scale=="log10":
			minor = range(1,10) if self.minor is None else self.minor
			object.__setattr__(self,'minor',tuple(float(sub) for sub in np.atleast_1d(minor)))
			return

		minor = floor(self.length/10) if self.minor is None else float(self.minor)
		# round off float noise such as 5*0.06 = 0.30000000000000004
		major = round(5*minor,decimals(minor)) if self.major is None else float(self.major)

		if minor<=0 or major<=0:
			raise ValueError("major and minor must be positive.")

		object.__setattr__(self,'minor',minor)
		object.__setattr__(self,'major',major)

	@property
	def lower(self) -> float:
		"""Return the smaller limit."""
		return min(self.limit)

	@property
	def upper(self) -> float:
		"""Return the larger limit."""
		return max(self.limit)

	@property
	def length(self) -> float:
		"""Return the span of the axis (upper - lower)."""
		return self.upper-self.lower

	@property
	def middle(self) -> float:
		"""Return the midpoint of the axis, geometric on a log10 scale."""
		if self.scale=="log10":
			return float(np.sqrt(self.lower*self.upper))

		return (self.lower+self.upper)/2

	@property
	def flipped(self) -> bool:
		"""Return True if the values decrease from left to right."""
		return self.limit[0]>self.limit[1]

	def lower_off(self,perc:float=2.) -> float:
		"""Return the value perc % of the axis in from the lower limit."""
		if self.scale=="log10":
			return self.lower**(1-perc/100.)*self.upper**(perc/100.)

		return self.lower+self.length*perc/100.

	def upper_off(self,perc:float=2.) -> float:
		"""Return the value perc % of the axis in from the upper limit."""
		if self.scale=="log10":
			return self.upper**(1-perc/100.)*self.lower**(perc/100.)

		return self.upper-self.length*perc/100.
