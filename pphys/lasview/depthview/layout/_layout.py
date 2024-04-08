from ._trail import Trail

class Layout():

	def __init__(self,*,ncols:int=3,nrows:int=3,width:tuple=None,height:tuple=None,depth:int=1,label:str="top"):
		"""
		It sets grid number for different elements in the axes:

		ncols       : number of column axis including depth axis in the figure, integer
		nrows 		: number of curves in columns, integer

		width       : width of curve trail and width of depth trail,
					  len(width) must be equal to either one, two or ncols.
					  tuple of floats

		height      : height per row and height per unit distance,
					  len(height) must be equal to either one or two.
					  tuple of floats
	
		depth       : location of depth axis, integer

		label 		: location of label plots, top, bottom or None
		"""

		self._ncols  = ncols
		self._nrows  = nrows

		self._width  = self.get_width(width)
		self._height = self.get_height(height)

		self._depth  = depth
		self._label  = label

		self._trails = tuple([Trail() for _ in ncols])

	def __setitem__(self,index,trail:Trail):
		self._trails[index] = trail

	def __getitem__(self,index):
		return self._trails[index]

	@property
	def ncols(self):
		return self._ncols

	@property
	def width(self):
		return self._width

	@property
	def depth(self):
		return self._depth

	@property
	def label(self):
		return self._label

	def get_width(self,width):

		if len(width)==1:
			return width*self.ncols

		if len(width)==2:
			return width[0]+width[1]*(self.ncols-1)

		if len(width)==self.ncols:
			return width

		raise Warning("Length of width and number of columns does not match")

	def get_height(self,height):

		if height is None:
			height = (1.,0.5)

		return height

if __name__ == "__main__":

	layout = Layout(ncols=5,width=(2,),label="top",nrows=3)

	print(layout.width)

	print(layout.head.nrows)
	print(layout.head.height)
	print(layout.body.height)