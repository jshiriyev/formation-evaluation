import lasio

import numpy

class Curve(lasio.CurveItem):
	"""It is Curve Item with additional plotting properties."""

	def __init__(self,column:int,depth:numpy.ndarray,*,row:int=None,xmin:float=None,xmax:float=None,multp:float=None,**kwargs):

		super().__init__(**kwargs)

		self._column = column
		self._depth	 = depth
		self._row 	 = row
		self._xmin 	 = xmin
		self._xmax 	 = xmax	
		self._multp	 = multp

	@property
	def column(self):
		return self._column

	@property
	def depth(self):
		return self._depth
	
	@property
	def row(self):
		return self._row

	@property
	def xmin(self):
		if self._xmin is None:
			return numpy.nanmin(self.data)
		return self._xmin

	@property
	def xmax(self):
		if self._xmax is None:
			return numpy.nanmax(self.data)
		return self._xmax

	@property
	def limit(self):
		return (self.xmin,self.xmax)

	@property
	def multp(self):
		return self._multp

if __name__ == "__main__":

	curve = Curve(0,"DEPT")

	print(curve)