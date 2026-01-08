from ._label import LabelDict
from ._depth import DepthDict
from ._xaxis import XAxisDict

class Layout():

	def __init__(
		self,
		ntrail : int = 3,
		ncycle : int = 3,
		label : dict | None = None,
		depth : dict | None = None,
		widths : tuple[float, ...] | None = None,
		heights : tuple[float, float] | None = None
		):
		"""It sets elements for different trails in the axes:

		ntrail 	: number of trails including depth trail in the figure, integer
		ncycle 	: maximum number of curves in trails, integer

		label   : defines label axis that contains mnemonics, units, colors, etc.
		depth 	: defines depth axis that contains main depth values (MD or TVD).

		widths 	: width of trails, len(widths) must be equal to either one,
				two or the number of trails; tuple of float

		heights : height per label row and height per unit distance,
				len(heights) must be equal to two; tuple of float

		"""
		self.ntrail  = ntrail
		self.ncycle  = ncycle

		self._xaxes  = [XAxisDict() for _ in range(self.ntrail)]
		self._label  = LabelDict(**(label or {}))
		self._depth  = DepthDict(**(depth or {}))

		self.widths  = widths
		self.heights = heights

	@property
	def ntrail(self):
		return self._ntrail

	@ntrail.setter
	def ntrail(self,value:int):
		self._ntrail = value

	def __len__(self):
		return self._ntrail

	@property
	def ncycle(self):
		return self._ncycle

	@ncycle.setter
	def ncycle(self,value):
		self._ncycle = value
	
	@property
	def shape(self):
		return (self.ntrail,self.ncycle)

	def set(self,index:int,**kwargs):
		self[index] = XAxisDict(**kwargs)

	def __setitem__(self,index:int,xaxis:XAxisDict):
		self._xaxes[index] = xaxis

	def __getitem__(self,index):
		return self._xaxes[index]

	@property
	def widths(self):
		return self._widths

	@widths.setter
	def widths(self,value:tuple[float, ...] | None):

		if value is None:
			self._widths = (2.0,4.0)

		elif len(value)==1:
			self._widths = value*self.ntrail

		elif len(value)==2:

			wlist = list((value[1],)*self.ntrail)

			for spot in self._depth.spot:
				wlist[spot] = value[0]

			self._widths = tuple(wlist)

		elif len(value)==self.ntrail:
			self._widths = value

		else:
			raise Warning("Length of widths and number of columns does not match.")

	@property
	def heights(self):
		head_height = int(self._heights[0]*self.ncycle)
		body_height = int(self._heights[1]*self._depth.length)

		return (head_height,body_height)

	@heights.setter
	def heights(self,value:tuple[float, float] | None):
		self._heights = (50.0,20.0) if value is None else value

	@property
	def size(self):
		return (sum(self.widths),sum(self.heights))

if __name__ == "__main__":

	layout = Layout(ntrail=5,ncycle=3,widths=(2,))

	print(layout.widths)