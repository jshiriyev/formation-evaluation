from dataclasses import dataclass

import numpy

@dataclass
class Time():
	"""
	delta   : first time step defined in days
	total   : total simulation time defined in days
	"""

	delta  	: float
	total 	: float

	def times(self):
		"""Returns linearly spaced time data."""


		# if scale == "linear":
		# 	self.time = numpy.linspace(self.twell,self.tp,size)
		# elif scale == "log":
		# 	self.time = numpy.logspace(*numpy.log10([self.twell,self.tp]),size)


		return numpy.arange(
			self.total+self.delta/2,step=self.delta)

	def steps(self):
		"""Returns the time steps in the given time array."""
		return self.times[1:]-self.times[:-1]