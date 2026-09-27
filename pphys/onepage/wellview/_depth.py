"""The depth axis shared by every track."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DepthDict:
	"""The vertical (depth) axis shared by every track.

	limit 	: the depth window, top and base in either order. It is stored as
			(base, top), the y limits that put depth increasing downwards.

	major 	: spacing of the major depth ticks and grid lines.
	minor 	: spacing of the minor depth ticks and grid lines.

	spot 	: indices of the depth tracks, which show depth ticks instead of
			grid lines.
	grid 	: whether the other tracks draw depth grid lines; a track whose
			own grid is off draws none.

	"""
	limit 	: tuple[float, float] = (0.,100.)

	major 	: float = 10.
	minor 	: float = 1.

	spot 	: tuple[int, ...] = (0,)
	grid 	: bool = True

	def __post_init__(self):

		top,base = sorted(float(value) for value in self.limit)

		if top==base:
			raise ValueError(f"The depth limit needs two different depths, not {self.limit!r}.")

		if self.major<=0 or self.minor<=0:
			raise ValueError("major and minor must be positive.")

		spot = (self.spot,) if isinstance(self.spot,int) else tuple(self.spot)

		object.__setattr__(self,'limit',(base,top))
		object.__setattr__(self,'spot',spot)

	@property
	def lower(self) -> float:
		"""Return the deeper depth (base of the window)."""
		return self.limit[0]

	@property
	def upper(self) -> float:
		"""Return the shallower depth (top of the window)."""
		return self.limit[1]

	@property
	def length(self) -> float:
		"""Return the depth interval (lower - upper)."""
		return self.lower-self.upper
