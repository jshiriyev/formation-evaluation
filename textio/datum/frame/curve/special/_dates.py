import datetime

from dateutil import parser

import re

import numpy

class dates(numpy.ndarray):

	def __new__(cls,values,null=None):

		null = numpy.datetime64('NaT') if null is None else numpy.datetime64(null)

		values = iterable(values)

		obj = numpy.asarray(values,dtype='datetime64[D]').view(cls)

		obj._null = null

		return obj

	def __array_finalize__(self,obj):

		if obj is None: return

		self._null = getattr(obj,'_null',numpy.datetime64('NaT'))

	def __repr__(self):

		parent = super().__repr__()

		child = parent.replace('NaT',str(self.null))

		return re.sub(r"\s+"," ",child)

	def __str__(self):

		parent = super().__str__()

		child = parent.replace('NaT',str(self.null))

		return re.sub(r"\s+"," ",child)

	@property
	def null(self):

		return self._null

	@property
	def isvalid(self):
		"""It return boolean array True for float and False for null."""
		return ~numpy.isnan(self.view(numpy.ndarray))

	@property
	def isnull(self):
		"""It return numpy bool array, True for null and False for float."""
		return numpy.isnan(self.view(numpy.ndarray))

def iterable(values):

	vals = []

	for value in values:

		if isinstance(value,int):
			value = datetime.date.fromtimestamp(value)
		elif isinstance(value,float):
			value = datetime.date.fromtimestamp(value)
		elif isinstance(value,str):
			value = strtodate(value)
		elif isinstance(value,datetime.datetime):
			value = value.date()
		elif isinstance(value,datetime.date):
			value = value
		else:
			value = None

		vals.append(value)

	return vals

def strtodate(value):

	if value.lower() == "now" or value.lower() == "today":
		value = datetime.date.today()

	elif value.lower() == "yesterday":
		value = numpy.datetime64(datetime.date.today())
		value -= numpy.timedelta64(1,'D')
		value = value.tolist()

	elif value.lower() == "tomorrow":
		value = numpy.datetime64(datetime.date.today())
		value += numpy.timedelta64(1,'D')
		value = value.tolist()

	else:

		try:
			value = parser.parse(string)
		except parser.ParserError:
			value = None
		else:
			value = value.date()

	return value
