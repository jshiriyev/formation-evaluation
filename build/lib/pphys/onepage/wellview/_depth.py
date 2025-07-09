from dataclasses import dataclass, field

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
	minor 	: int = 1

	spot 	: tuple = field(
		repr = False,
		default = (0,),
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

if __name__ == "__main__":

	depth=dict(limit=(3200,3310),major=10,minor=range(2,10,2),spot=(1,))

	d = Depth(**depth)

	print(d)

	print(d.length)

	print(d.spot)