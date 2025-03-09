from dataclasses import dataclass, field

from ._unary import Unary

@dataclass(frozen=True)
class Depth:
	"""
	It initializes the axis of Depth in a body:

	limit 	: lower and upper values of the axis
	
	major 	: sets the frequency of major ticks
	minor 	: sets the frequency of minor ticks

	spot 	: location of axis in the layout, int
			index of trail in the layout

	"""
	limit 	: tuple[float] = (0,100)

	major 	: int = 10
	minor 	: range = range(1,10)

	scale 	: str = field(
		init = False,
		repr = False,
		default = "linear",
		)

	spot 	: int = field(
		repr = False,
		default = 1,
		)

	def __post_init__(self):

		object.__setattr__(self,'limit',self.limit[::-1])

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
	def unary(self):
		return Unary
	