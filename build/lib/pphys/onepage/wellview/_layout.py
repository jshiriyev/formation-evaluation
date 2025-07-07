from ._label import Label
from ._depth import Depth
from ._xaxis import Xaxis

class Layout():

	def __init__(self,ntrail:int=3,ncycle:int=3,label:dict=None,depth:dict=None,widths:tuple[float]=None,heights:tuple[float]=None):
		"""It sets elements for different trails in the axes:

		ntrail 	: number of trails including depth trail in the figure, integer
		ncycle 	: maximum number of curves in trails, integer

		label   : defines head axis containing curve labels and units
		depth 	: defines depth axis containing main depth values

		widths 	: width of trails, len(widths) must be equal to either one,
				two or the number of trails; tuple of float

		heights : height per label row and height per unit distance,
				len(heights) must be equal to two; tuple of float

		"""
		self.ntrail  = ntrail
		self.ncycle  = ncycle

		self.label   = label or {}
		self.depth   = depth or {}

		self.widths  = widths
		self.heights = heights

		self._xaxes  = [Xaxis() for _ in range(self.ntrail)]

	@property
	def ntrail(self):
		return self._ntrail

	@ntrail.setter
	def ntrail(self,value):
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

	@property
	def label(self):
		return self._label

	@label.setter
	def label(self,value:dict):

		if value.get("limit") is None:
			value["limit"] = (0,10*self.ncycle)

		self._label = Label(**value)

	@property
	def depth(self):
		return self._depth

	@depth.setter
	def depth(self,value:dict):
		self._depth = Depth(**value)

	@property
	def widths(self):
		return self._widths

	@widths.setter
	def widths(self,value:tuple[int]):

		if value is None:
			self.widths = (2,4)

		elif len(value)==1:
			self._widths = value*self.ntrail

		elif len(value)==2:

			wlist = list((value[1],)*self.ntrail)

			wlist[self.depth.spot] = value[0]

			self._widths = tuple(wlist)

		elif len(value)==self.ntrail:
			self._widths = value

		else:
			raise Warning("Length of widths and number of columns does not match")

	@property
	def heights(self):

		head_height = int(self._heights[0]*self.ncycle)
		body_height = int(self._heights[1]*self.depth.length)

		return (head_height,body_height)

	@heights.setter
	def heights(self,value:tuple[int]):
		self._heights = (50,20) if value is None else value

	@property
	def size(self):
		return (sum(self.widths),sum(self.heights))

	@property
	def xaxes(self):
		return self._xaxes

	def set(self,index:int,**kwargs):
		self[index] = Xaxis(**kwargs)

	def __setitem__(self,index:int,xaxis:Xaxis):
		self._xaxes[index] = xaxis

	def __getitem__(self,index):
		return self._xaxes[index]

if __name__ == "__main__":

	layout = Layout(ntrail=5,ncycle=3,widths=(2,),label_loc="top")

	print(layout.widths)

	print(layout.head.curves)
	print(layout.head.height)
	print(layout.body.height)