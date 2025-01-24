import numpy

class Unary:

	@staticmethod
	def power(x:float):
		"""
		Returns the tenth power that brings float point next to the first
		significant digit.
		"""
		return -int(numpy.floor(numpy.log10(abs(x))))

	@staticmethod
	def ceil(x:float,power:int=None):
		"""
		Returns the ceil value for the first significant digit by default.
		
		If the power is specified, it is used as a factor before ceiling.
		"""
		if power is None:
			power = Curve.upower(x)

		return (numpy.ceil(x*10**power)/10**power).tolist()

	@staticmethod
	def floor(x:float,power:int=None):
		"""
		Returns the floor value for the first significant digit by default.
		
		If the power is specified, it is used as a factor before flooring.
		"""
		if power is None:
			power = Curve.upower(x)

		return (numpy.floor(x*10**power)/10**power).tolist()

	@staticmethod
	def round(x:float,power:int=None):
		"""Returns the rounded value for the first significant digit."""
		
		if power is None:
			power = Curve.upower(x)

		return (numpy.round(x*10**power)/10**power).tolist()