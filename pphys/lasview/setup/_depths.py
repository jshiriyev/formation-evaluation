from matplotlib import ticker

class Depths():

	def __init__(self,top,bottom,base=10.,subs=1,subskip=None,subskip_top=0,subskip_bottom=0):
		"""
		It sets the depth interval for which log data will be shown:

		top             : top of interval
		bottom          : bottom of interval
		base            : major grid intervals on the plot

		subs            : minor grid intervals on the plot
		subskip         : number of minors to skip at the top and bottom
		subskip_top     : number of minors to skip at the top
		subskip_bottom  : number of minors to skip at the bottom
		"""

		self._top 		= numpy.floor(top/base)*base
		self._bottom 	= self._top+numpy.ceil((bottom-top)/base)*base
		self._base 		= base

		if subskip is not None:
			subskip_bottom,subskip_top = subskip,subskip

		self._top 		+= subs*subskip_top
		self._bottom 	+= subs*subskip_bottom

	@property
	def top(self):
		return self._top

	@property
	def bottom(self):
		return self._bottom

	@property
	def base(self):
		return self._base

	@property
	def subs(self):
		return self._subs

	@property
	def height(self):
		return self._bottom-self._top
	
	@property
	def limit(self):
		return (self._bottom,self._top)
	
	@property
	def ticks(self):
		return ticker.MultipleLocator(self._base).tick_values(self._top,self._bottom)
	
	