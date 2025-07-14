import numpy as np

class Unary:
	"""Contains static methods for defining axis limits."""

	@staticmethod
	def power(x:float):
		"""
		Returns the tenth power that brings float point next to the first
		significant digit.

		"""
		return -int(np.floor(np.log10(abs(x))))

	@staticmethod
	def ceil(x:float,power:int=None):
		"""
		Returns the ceil value for the first significant digit by default.
		
		If the power is specified, it is used as a factor before ceiling.

		"""
		if power is None:
			power = Unary.power(x)

		return (np.ceil(x*10**power)/10**power).tolist()

	@staticmethod
	def floor(x:float,power:int=None):
		"""
		Returns the floor value for the first significant digit by default.
		
		If the power is specified, it is used as a factor before flooring.

		"""
		if power is None:
			power = Unary.power(x)

		return (np.floor(x*10**power)/10**power).tolist()

	@staticmethod
	def round(x:float,power:int=None):
		"""
		Returns the rounded value to the first significant digit.

		"""
		if power is None:
			power = Unary.power(x)

		return (np.round(x*10**power)/10**power).tolist()

if __name__ == "__main__":

	print(Unary.power(0.000532423))
	print(Unary.ceil(0.000532423))
	print(Unary.floor(0.000532423))
	print(Unary.round(0.000532423))

	print(Unary.ceil(0.000532423,-2))
	print(Unary.floor(0.000532423,-2))
	print(Unary.round(0.000532423,-2))
