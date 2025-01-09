import numpy

import lasio

class Audit():

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

if __name__ == "__main__":

	pass