from dataclasses import dataclass

@dataclass
class Skip:
	xmin : int
	xmax : int

class XAxis():

	def __init__(self,*,cycle=2,scale='linear',subs=None,skip:tuple=None):
		"""
		It initializes x-axis of column in log plot:

		cycle 	: number of major cycles in the column
		scale 	: scale of lines, linear or logarithmic

		subs 	: sets the frequency of minor ticks
		skip 	: how many sub units to skip from minimum and
				  maximum side, tuple of two integers
		"""

		self._cycle = cycle
		self._scale = scale

		self._subs = subs

		if skip is None:
			skip = (0,0)

		self._skip = Skip(*skip)

	@property
	def cycle(self):
		return self._cycle

	@property
	def scale(self):
		return self._scale

	@property
	def subs(self):

		if self.scale == "linear":
			return 1 if self._subs is None else self._subs		
		elif self.scale == "log":
			return range(1,10) if self._subs is None else self._subs

		raise ValueError(f"{scale} has not been defined! options: {{linear,log}}")

	@property
	def skip(self):
		return self._skip
	
	@property
	def limit(self):

		if self.scale == "linear":
			return (self.skip.xmin,self.skip.xmax+self.cycle*10)
		elif self.scale == "log":
			return (1+self.skip.xmin,(1+self.skip.xmax)*10**self.cycle)

		raise ValueError(f"{scale} has not been defined! options: {{linear,log}}")

if __name__ == "__main__":

	xaxis = XAxis(subs=2,scale="log",skip=(1,3))

	print(xaxis.skip.xmax)

	print(xaxis.limit)


