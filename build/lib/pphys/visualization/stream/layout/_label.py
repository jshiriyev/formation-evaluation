from dataclasses import dataclass, field

from ._unary import Unary

@dataclass(frozen=True)
class Label:
	"""
	It initializes the axis of Label in a head:

	limit 	: lower and upper values of the axis
	
	major 	: sets the frequency of major ticks

	spot 	: location of lable in the layout, str
			top, bottom, or None

	"""
	limit	: tuple[float] = (0,30)

	major 	: int = 10
	minor 	: range = field(
		init = False,
		repr = False,
		default = None,
		)

	scale 	: str = field(
		init = False,
		repr = False,
		default = "linear",
		)

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

	@property
	def unary(self):
		return Unary

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