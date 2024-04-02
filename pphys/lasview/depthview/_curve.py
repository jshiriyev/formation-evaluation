import numpy

from dataclasses import dataclass

@dataclass
class Curve:
	"""It is a view Curve item dictionary."""

	col: int

	mnemonic: str

	row: int = None

	xmin: float = None
	xmax: float = None

	multp: float = None

	color: str = "black"
	style: str = "solid"
	width: float = 0.75

	data: numpy.ndarray = None

	unit: str = None
	value: str = None
	descr: str = None

	depth: numpy.ndarray = None

	@property
	def vmin(self):
		if self._vmin is None:
			return numpy.nanmin(curve.data)
		else:
			return self._vmin

	@property
	def limit(self):
		return(self.vmin,self.vmax)
	

if __name__ == "__main__":

	curve = Curve(0,"DEPT")

	print(curve)