import lasio

from ._label import Label
from ._depth import Depth
from ._xaxis import Xaxis

class Layout():

	def __init__(self,trail:int=3,cycle:int=3,label:dict=None,depth:dict=None,width:tuple[float]=None,height:tuple[float]=None):
		"""It sets elements for different trails in the axes:

		trail 	: number of trails including depth trail in the figure, integer
		cycle 	: maximum number of curves in trails, integer

		width 	: width of trail, len(width) must be equal to either one,
				two or the number of trails; tuple of float

		height 	: height per label row and height per unit distance,
				len(height) must be equal to two; tuple of float
		"""
		self.trail  = trail
		self.cycle  = cycle

		self.label  = label or {}
		self.depth  = depth or {}

		self.width  = width
		self.height = height

		self._xaxes = [Xaxis() for _ in range(self.trail)]

	@property
	def trail(self):
		return self._trail

	@trail.setter
	def trail(self,value):
		self._trail = value

	def __len__(self):
		return self._trail

	@property
	def cycle(self):
		return self._cycle

	@cycle.setter
	def cycle(self,value):
		self._cycle = value
	
	@property
	def shape(self):
		return (self.trail,self.cycle)

	@property
	def label(self):
		return self._label

	@label.setter
	def label(self,value:dict):

		if value.get("limit") is None:
			value["limit"] = (0,10*self.cycle)

		self._label = Label(**value)

	@property
	def depth(self):
		return self._depth

	@depth.setter
	def depth(self,value:dict):
		self._depth = Depth(**value)

	@property
	def width(self):
		return self._width

	@width.setter
	def width(self,value:tuple[int]):

		if value is None:
			self.width = (2,4)

		elif len(value)==1:
			self._width = value*self.trail

		elif len(value)==2:

			wlist = list((value[1],)*self.trail)

			wlist[self.depth.spot] = value[0]

			self._width = tuple(wlist)

		elif len(value)==self.trail:
			self._width = value

		else:
			raise Warning("Length of width and number of columns does not match")

	@property
	def height(self):

		head_height = int(self._height[0]*self.cycle)
		body_height = int(self._height[1]*self.depth.length)

		return (head_height,body_height)

	@height.setter
	def height(self,value:tuple[int]):
		self._height = (50,20) if value is None else value

	@property
	def size(self):
		return (sum(self.width),sum(self.height))

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

	layout = Layout(trails=5,curves=3,width=(2,),label_loc="top")

	print(layout.width)

	print(layout.head.curves)
	print(layout.head.height)
	print(layout.body.height)