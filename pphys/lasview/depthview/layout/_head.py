from ._axis import Axis

class Head(Box):

	def __init__(self,xaxis:Axis,yaxis:Axis,nrows:int=3):
		"""
		nrows 	: number of curves in the associated body
		"""

		super().__init__(xaxis,yaxis)

		self._nrows  = nrows

	@property
	def nrows(self):
		return self._nrows