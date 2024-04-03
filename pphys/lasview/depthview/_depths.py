from dataclasses import dataclass

from matplotlib import ticker

@dataclass
class Skip:
	ymin : int
	ymax : int

class Depths():

	def __init__(self,ymin,ymax,cycle:int=1,subs:int=1,skip:tuple=None):
		"""
		It sets the depth interval for which log data will be shown:

		ymin    : ymin of depth interval
		ymax 	: ymax of depth interval

		cycle   : number of major grid intervals per 10 meter or feet

		subs    : minor grid intervals on the plot
		skip    : number of minors to skip at the ymin and ymax
		"""

		self._ymin 	= ymin
		self._ymax 	= ymax

		self._cycle = cycle

		self._subs  = subs

		if skip is None:
			skip = (0,0)

		self._skip  = Skip(*skip)

		self._ymin 	+= self.subs*self.skip.ymin
		self._ymax 	+= self.subs*self.skip.ymax

	@property
	def ymin(self):
		return numpy.floor(self._ymin/self.base)*self.base

	@property
	def ymax(self):
		return self._ymin+numpy.ceil((self._ymax-self._ymin)/self.base)*self.base

	@property
	def cycle(self):
		return self._cycle

	@property
	def base(self):
		return self._cycle*10.

	@property
	def subs(self):
		return self._subs

	@property
	def skip(self):
		return self._skip

	@property
	def height(self):
		return self._ymax-self._ymin
	
	@property
	def limit(self):
		return (self._ymax,self._ymin)
	
	@property
	def ticks(self):
		return ticker.MultipleLocator(self.base).tick_values(self.ymin,self.ymax)

if __name__ == "__main__":

	pass
	