import numpy

class Layout():

	def __init__(self,nums,xpad=0.1,ypad=0.1):

		self.nums = nums
		self.xpad = xpad
		self.ypad = ypad

	@property
	def xlen(self):
		"""Computes x-length dynamically based on nums and xpad."""
		return 1./self.nums-self.xpad

	@property
	def ylen(self):
		"""Computes y-length dynamically based on ypad."""
		return 1.-self.ypad
	
	def bounds(self,index):
		"""Returns the bounds of the axin given the index."""
		return [self.xpad*3/4.+index/self.nums, self.ypad*1/4, self.xlen, self.ylen]

	def xloc(self,index):
		"""Returns the x bounds of the axin given the index."""
		return [self.xpad*3/4.+index/self.nums, (index+1)/self.nums-self.xpad*1/4.]

	def yloc(self):
		"""Returns the y bounds of the axis."""
		return [self.ypad*1/4., 1.-self.ypad*3/4]

	def xcenter(self,index):
		"""Returns the x-center of the axin given."""
		return numpy.mean(self.xloc(index)).tolist()

	def ycenter(self):
		"""Returns the y-center of the axis."""
		return numpy.mean(self.yloc()).tolist()