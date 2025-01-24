import numpy

from scipy.sparse import csr_matrix as csr

def derive(yvals,xvals=None):

	yvals = numpy.array(yvals).flatten()

	if xvals is not None:
		xvals = numpy.array(xvals).flatten()

	size = yvals.size

	diagonal = numpy.arange(size)

	ones = numpy.ones(size)

	shape = (size,size)

	difference = csr(shape)

	lwing = diagonal-1
	rwing = diagonal+1

	lwing[0],rwing[-1] = 0,size-1

	difference += csr((ones,(diagonal,rwing)),shape=shape)
	difference -= csr((ones,(diagonal,lwing)),shape=shape)

	if xvals is None:
		return difference*yvals

	return (difference*yvals)/(difference*xvals)