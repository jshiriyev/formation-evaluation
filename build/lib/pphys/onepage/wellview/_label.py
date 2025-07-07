from dataclasses import dataclass, field

@dataclass(frozen=True)
class Label:
	"""
	It initializes the axis of Label in a head:

	limit 	: lower and upper values of the axis
	
	major 	: sets the frequency of major ticks

	spot 	: location of lable in the layout, str
			top, bottom, or None

	"""
	limit	: tuple[float]

	major 	: int = 10

	spot 	: str = field(
		repr = False,
		default = "top",
		)

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

	label = Label()

	print(label.limit)
	print(label.major)
	print(label.minor)
	print(label.scale)
	print(label.spot)
	print(label.lower)
	print(label.upper)
	print(label.length)