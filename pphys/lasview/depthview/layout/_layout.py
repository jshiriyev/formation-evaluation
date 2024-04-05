from dataclasses import dataclass

from matplotlib import pyplot

class Layout():

	def __init__(self,*,ncols:int=None,nrows:int=3,width:tuple=None,height:tuple=None,depth:int=1,label:str="top"):
		"""
		It sets grid number for different elements in the axes:

		ncols       : number of column axis including depth axis in the figure, integer

		width       : width of curve track and width of depth track,
					  len(width) must be equal to either one, two or ncols.
					  tuple of floats

		height      : height per row and height per unit distance,
					  len(height) must be equal to either one or two.
					  tuple of floats
	
		depth       : location of depth axis, integer

		label 		: label of label plots

		nrows 		: maximum number of curves in all columns
		"""

		self._ncols  = ncols
		self._nrows  = nrows

		self._width  = self.get_width(width)
		self._height = self.get_height(height)

		self._depth  = depth
		self._label  = label 	# label of head: top, bottom or None

		self._tracks = ()

	def get_width(width):

		if len(width)==1:
			return width*ncols

		if len(width)==2:
			return width[0]+width[1]*(ncols-1)

		if len(width)==ncols:
			return width

		raise Warning("Length of width and number of columns does not match")

	def get_height(height):

		if height is None:
			height = (1.,0.5)

		return height

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
	
	def boot(self,axis):

        axis.set_xlim((0,1))

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.set_ylim((0,self.head.nrows))

        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        return axis

if __name__ == "__main__":

	layout = Layout(ncols=5,width=(2,),label="top",nrows=3)

	print(layout.width)

	print(layout.head.nrows)
	print(layout.head.height)
	print(layout.body.height)