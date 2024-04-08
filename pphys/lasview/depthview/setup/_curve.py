import lasio

import numpy

class Curve(lasio.CurveItem):
	"""It is Curve Item with additional plotting properties."""

	def __init__(self,column:int,*,row:int=None,lower:float=None,upper:float=None,multp:float=None,**kwargs):

		super().__init__(**kwargs)

		self._column = column
		self._row 	 = row
		self._lower  = lower
		self._upper  = upper	
		self._multp	 = multp

	@property
	def column(self):
		return self._column
	
	@property
	def row(self):
		return self._row

	@property
	def lower(self):
		if self._lower is None:
			return numpy.nanmin(self.data)
		return self._lower

	@property
	def upper(self):
		if self._upper is None:
			return numpy.nanmax(self.data)
		return self._upper

	@property
	def limit(self):
		return (self.lower,self.upper)

	@property
	def multp(self):
		return self._multp

if __name__ == "__main__":

	curve = Curve(0,"DEPT")

	print(curve)