from dataclasses import dataclass, field

@dataclass(frozen=True)
class Depth:
	"""
	It represents a vertical axis in a layout or plot.

	limit 	: the depth range (upper and lower) values of the axis
		This will be automatically reversed to (lower, upper) in __post_init__.
	
	major 	: the interval between major ticks on the depth axis.
	minor 	: the interval between minor ticks on the depth axis.

	spot 	: A layout index or trail position for the depth axis.
		This is excluded from representation (__repr__) for cleaner output.

	"""
	limit 	: tuple[float, float] = (0.,100.)

	major 	: int = 10
	minor 	: int|range = 1

	spot 	: tuple[int, ...] = field(
		repr = False,
		default = (0,),
		)

	def __post_init__(self):
		# Reverse the limit to ensure it is ordered from top to bottom
		object.__setattr__(self,'limit',self.limit[::-1])

	@property
	def lower(self):
		"""Return the deeper depth (bottom of the range)."""
		return max(self.limit)

	@property
	def upper(self):
		"""Return the shallower depth (top of the range)."""
		return min(self.limit)

	@property
	def length(self):
		"""Return the total depth interval (lower - upper)."""
		return self.lower-self.upper

	@property
	def scale(self):
		"""Return the type of scale used for plotting (it is always 'linear')."""
		return "linear"
	

if __name__ == "__main__":

	depth=dict(limit=(3200,3310),major=10,minor=range(2,10,2),spot=(1,))

	d = Depth(**depth)

	print(d)

	print(d.length)

	print(d.spot)