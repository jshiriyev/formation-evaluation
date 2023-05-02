import numpy

import lasio

class allocate():

	def __init__(self,lasfile):

		self.lasfile = lasfile

	@staticmethod
	def production(prod:float,tops:tuple,perf:tuple):
		"""
		prod 	: floating value to be allocated along formations
		tops 	: tuple of (formation tops,), top to deeper
		perf 	: tuple of (perforation top, perforation bottom), top to deeper

		output	: tuple of production allocated along formations,
				  the length of tuple will be len(tops)-1
		"""

		heights = allocate.heights(tops,perf)

		perftop,perflow = perf

		pdepth = perflow-perftop

		shares = [prod*height/pdepth for height in heights]

		return tuple(shares)

	@staticmethod
	def heights(tops:tuple,perf:tuple):
		"""
		tops 	: tuple of (formation tops,), top to deeper
		perf 	: tuple of (perforation top, perforation bottom), top to deeper

		output 	: tuple of thicknesses distributed along perforation interval,
				  the length of tuple will be len(tops)-1

		"""

		shares = []

		perftop,perflow = perf

		for index in range(len(tops)-1):

			formtop,formlow = tops[index:index+2]

			top = perftop if formtop<perftop else formtop
			low = formlow if formlow<perflow else perflow

			interval = low-top

			interval = 0 if interval<0 else interval

			shares.append(interval)
		
		return shares

	@staticmethod
	def nets(subzone:tuple,lithid:int,lasfile,lithidhead:str):
		"""
		The method requires the use of las file where the lithology identifier curve is available.

		subzone : tuple of (top,bottom)
		lithid 	: lithology identifier
		output 	: thickness of lithology type in the subzone
		"""

		top,bottom = subzone

		indices = numpy.logical_and(lasfile[0]>top,lasfile[0]<bottom)

		curve = lasfile[lithidhead][indices]

		return numpy.sum(curve==lithid)*steps # shoul do better calculation than this for non uniform spacing