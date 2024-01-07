# DO NOT TOUCH ZIPPING, IT'S WORKING PERFECTLY FINE!

import math

import numpy

from ._flatten import flatten

times = lambda _list,maxsize: math.ceil(maxsize/len(_list))

def zip_cycle(*args,size=None,flat=True):
	"""Make an iterator that aggregates elements from each of the
	iterables by cycling shorter ones. The size indicates, the number
	of times iteration continues. If the size is not specified,
	iteration continues until the longest iterable is exhausted.
	If the args are not flat, it will be flattened to flat lists."""

	if not flat:
		args = [flatten(arg) for arg in args]

	args = [arg.tolist() if isinstance(arg,numpy.ndarray) else arg for arg in args]

	if size is None:
		size = len(max(args,key=len))

	args = [(arg*times(arg,size))[:size] for arg in args]

	return zip(*args)

if __name__ == "__main__":

	a = [1,2,3,4]
	b = [1,2]

	print("---------")

	for A,B in zip_cycle(a,b):
		print(A,B)
	
	print("---------")

	for A,B in zip_cycle(a,b,size=7):
		print(A,B)