from dataclasses import dataclass, field

@dataclass(frozen=True)
class LabelDict:
	"""
	A frozen dataclass representing a labeled axis in a header layout 
    (e.g., top of a log track or plot).

	limit 	: the depth range (upper and lower) values of the axis
	
	major 	: the interval between major ticks on the depth axis.

	spot 	: location of lable in the layout, str
			top, bottom, or None

	"""
	limit	: tuple[float, float] = (0,50)

	major 	: int = 10

	spot 	: str = field(
		repr = False,
		default = "top",
		)

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

	label = LabelDict((0,100))

	print(label.limit)
	print(label.major)
	print(label.scale)
	print(label.spot)
	print(label.lower)
	print(label.upper)
	print(label.length)