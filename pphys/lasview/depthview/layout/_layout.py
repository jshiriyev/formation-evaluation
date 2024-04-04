from dataclasses import dataclass

from matplotlib import pyplot

@dataclass
class Head:

	height  : float = None  	# height per row of head
	spot 	: str   = "top" 	# spot of head: top, bottom or None
	nrows 	: int   = 3 		# maximum number of curves in all columns

@dataclass
class Body:

	height 	: float = None 		# heigth per unit distance

class Layout():

	def __init__(self,*,ncols:int=None,width:tuple=None,height:tuple=None,depth:int=1,spot:str="top",nrows:int=None):
		"""
		It sets grid number for different elements in the axes:

		ncols       : number of column axis including depth axis in the figure, integer
		width       : width of columns, len(width) must be equal to ncols
		
		height      : height per row and height per unit distance, (float,)*2
	
		depth       : location of depth axis, integer

		spot 		: spot of label plots

		nrows 		: maximum number of curves in all columns
		"""

		self._ncols = ncols

		if len(width)==1:
			self._width = width*ncols
		elif len(width)==ncols:
			self._width = width
		else:
			raise Warning("Length of width and number of columns does not match")

		self._depth = depth

		if height is None:
			height = (1.,0.5)

		self._head = Head(height[0],spot,nrows)
		self._body = Body(height[1])

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
	def head(self):
		return self._head

	@property
	def body(self):
		return self._body

	def boot(self,axis):

        axis.set_xlim((0,1))

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.set_ylim((0,self.head.nrows))

        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        return axis

if __name__ == "__main__":

	layout = Layout(ncols=5,width=(2,),spot="top",nrows=3)

	print(layout.width)

	print(layout.head.nrows)
	print(layout.head.height)
	print(layout.body.height)