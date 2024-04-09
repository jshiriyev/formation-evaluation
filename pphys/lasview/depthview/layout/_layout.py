from ._axis import Axis

class Layout():

	def __init__(self,*,ntrail:int=3,ncurve:int=3,ldepth:int=1,llabel:str="top",width:tuple=None,height:tuple=None):
		"""
		It sets elements for different trails in the axes:

		ntrail      : number of trails including depth trail in the figure, integer
		ncurve 		: maximum number of curves in trails, integer

		ldepth      : location of depth trail, integer
		llabel 		: location of label head, top, bottom or None

		width       : width of trail, len(width) must be equal to either one,
					  two or the number of trails; tuple of floats

		height      : height per label row and height per unit distance,
					  len(height) must be equal to two; tuple of floats
	
		"""

		self._ntrail = ntrail
		self._ncurve = ncurve

		self._ldepth = ldepth
		self._llabel = llabel

		self._width  = self.get_width(width)
		self._height = self.get_height(height)

		self._xaxes  = tuple([Axis() for _ in range(ntrail)])
		
		self._depth  = Axis(flip=True)
		self._label  = Axis(cycle=ncurve)

	def __setitem__(self,index,xaxis:Axis):
		self._xaxes[index] = xaxis

	def __getitem__(self,index):
		return self._xaxes[index]

	@property
	def ntrail(self):
		return self._ntrail

	@property
	def ncurve(self):
		return self._ncurve

	@property
	def ldepth(self):
		return self._ldepth

	@property
	def llabel(self):
		return self._llabel

	@property
	def width(self):
		return self._width

	@property
	def height(self):
		return self._height

	@property
	def depth(self):
		return self._depth

	@property
	def label(self):
		return self._label

	@property
	def figsize(self):

		return (sum(self._width),sum([h*g for h,g in zip(self.height,(self.ncurve,self.depth.length))]))
	
	def get_width(self,width):

		if width is None:
			return self.get_width((2,4))

		if len(width)==1:
			return width*self.ntrail

		if len(width)==2:
			_width = list((width[1],)*self.ntrail)
			_width[self.ldepth] = width[0]
			return tuple(_width)

		if len(width)==self.ntrail:
			return width

		raise Warning("Length of width and number of columns does not match")

	def get_height(self,height):

		if height is None:
			height = (1.,0.5)

		return height

if __name__ == "__main__":

	layout = Layout(ntrail=5,width=(2,),llabel="top",ncurve=3)

	print(layout.width)

	print(layout.head.ncurve)
	print(layout.head.height)
	print(layout.body.height)