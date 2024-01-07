import numpy

from frames.linear import ints
from frames.linear import floats
from frames.linear import strs
from frames.linear import dates
from frames.linear import datetimes

class Raster():
	"""The idea is to have 2D numpy array where row and column keys are defined."""

	def __init__(self,matrix=None,rows=None,cols=None):
		""" Initializes 2D array with row and column headers.

		matrix: 	Two dimensional array

		rows: 		Row Headers
		cols: 		Column Headers

		"""
		self.matrix = numpy.asarray(matrix)

		self.rows = rows
		self.cols = cols

	def __repr__(self):
		return repr(self.matrix)

	def __str__(self):
		return str(self.matrix)

	def __getattr__(self,key):

		return getattr(self.matrix,key)
	
	def __getitem__(self,key):

		if isinstance(key,tuple):
			row,col = key
		else:
			row,col = key,slice(None,None,None)

		row = self._strcheck(row,self.rows)
		col = self._strcheck(col,self.cols)

		row = self._slicecheck(row,self.rows)
		col = self._slicecheck(col,self.cols)

		return self.matrix[row,col]

	@staticmethod
	def _strcheck(key,listObject):

		if isinstance(key,str):
			return listObject.index(key)
		else:
			return key

	@staticmethod
	def _slicecheck(key,listObject):

		if isinstance(key,slice):
			strt = Raster._strcheck(key.start,listObject)
			stop = Raster._strcheck(key.stop,listObject)
			return slice(strt,stop,key.step)
		else:
			return key

if __name__ == "__main__":

	"""
				day	month	year
	   javid	1	2 		3
	shiriyev 	4 	5 		6
	"""

	rt = Raster([[1,2,3],[4,5,6]],
		rows=["javid","shiriyev"],
		cols=["day","month","year"])

	# print(rt[:,"month"])

	# print(rt.cols)

	print(rt.matrix[0])