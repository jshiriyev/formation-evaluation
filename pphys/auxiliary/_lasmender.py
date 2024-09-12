import numpy

import lasio

class LasMender():

	def __init__(self):

		pass

	def mask(self,depthmin,depthmax):
		return numpy.logical_and(self.depth>=depthmin,self.depth<=depthmax)

	@staticmethod
	def isvalid(vals):
		return numpy.all(~numpy.isnan(vals))

	@staticmethod
	def ispositive(vals):
		return numpy.all(vals>=0)

	@staticmethod
	def issorted(vals):
		return numpy.all(vals[:-1]<vals[1:])

	def resample(self,depth):
		"""Resamples the frame data based on given depth:

		depth :   The depth values where new curve data will be calculated;
		"""

		depth_current = self.ascii.running[0].vals

		if not LasMender.isvalid(depth):
		    raise ValueError("There are none values in depth.")

		if not LasMender.issorted(depth):
		    depth = numpy.sort(depth)

		outers_above = depth<depth_current.min()
		outers_below = depth>depth_current.max()

		inners = numpy.logical_and(~outers_above,~outers_below)

		depth_inners = depth[inners]

		lowers = numpy.empty(depth_inners.shape,dtype=int)
		uppers = numpy.empty(depth_inners.shape,dtype=int)

		lower,upper = 0,0

		for index,depth in enumerate(depth_inners):

		    while depth>depth_current[lower]:
		        lower += 1

		    while depth>depth_current[upper]:
		        upper += 1

		    lowers[index] = lower-1
		    uppers[index] = upper

		delta_depth = depth_inners-depth_current[lowers]

		delta_depth_current = depth_current[uppers]-depth_current[lowers]

		grads = delta_depth/delta_depth_current

		for index,_column in enumerate(self.ascii.running):

		    if index==0:
		        self.ascii.running[index].vals = depth
		        continue

		    delta_values = _column.vals[uppers]-_column.vals[lowers]

		    self.ascii.running[index].vals = numpy.empty(depth.shape,dtype=float)

		    self.ascii.running[index].vals[outers_above] = numpy.nan
		    self.ascii.running[index].vals[inners] = _column.vals[lowers]+grads*(delta_values)
		    self.ascii.running[index].vals[outers_below] = numpy.nan

	@staticmethod
	def resample_curve(depth,curve):
		"""Resamples the curve.vals based on given depth, and returns curve:

		depth       :   The depth where new curve values will be calculated;
		curve       :   The curve object to be resampled

		"""

		if not LasMender.isvalid(depth):
		    raise ValueError("There are none values in depth.")

		if not LasMender.issorted(depth):
		    depth = numpy.sort(depth)

		outers_above = depth<curve.depth.min()
		outers_below = depth>curve.depth.max()

		inners = numpy.logical_and(~outers_above,~outers_below)

		depth_inners = depth[inners]

		lowers = numpy.empty(depth_inners.shape,dtype=int)
		uppers = numpy.empty(depth_inners.shape,dtype=int)

		lower,upper = 0,0

		for index,depth in enumerate(depth_inners):

		    while depth>curve.depth[lower]:
		        lower += 1

		    while depth>curve.depth[upper]:
		        upper += 1

		    lowers[index] = lower-1
		    uppers[index] = upper

		delta_depth = depth_inners-curve.depth[lowers]

		delta_depth_current = curve.depth[uppers]-curve.depth[lowers]

		delta_values_current = curve.vals[uppers]-curve.vals[lowers]

		grads = delta_depth/delta_depth_current

		values = numpy.empty(depth.shape,dtype=float)

		values[outers_above] = numpy.nan
		values[inners] = curve.vals[lowers]+grads*(delta_values_current)
		values[outers_below] = numpy.nan

		curve.depth = depth

		curve.vals = values

		return curve