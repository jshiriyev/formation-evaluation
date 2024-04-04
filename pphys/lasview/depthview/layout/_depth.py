from dataclasses import dataclass

from matplotlib import pyplot
from matplotlib import ticker

@dataclass
class Skip:
	ymin : int
	ymax : int

class Depth():

	def __init__(self,ymin:float,ymax:float,xmin:float=0,xmax:float=1,cycle:int=1,subs:int=1,skip:tuple=None):
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

		self._xmin  = xmin
		self._xmax  = xmax

		self._cycle = cycle

		self._subs  = subs

		if skip is None:
			skip = (0,0)

		self._skip  = Skip(*skip)

		self._ymin 	+= self.subs*self.skip.ymin
		self._ymax 	+= self.subs*self.skip.ymax

	@property
	def ylim(self):
		return (self._ymin,self._ymax)
	
	@property
	def ymin(self):
		return numpy.floor(self._ymin/self.base)*self.base

	@property
	def ymax(self):
		return self._ymin+numpy.ceil((self._ymax-self._ymin)/self.base)*self.base

	@property
	def xlim(self):
		return (self._xmin,self._xmax)
	
	@property
	def xmin(self):
		return self._xmin

	@property
	def xmax(self):
		return self._xmax

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

	def boot(self,axis):

		axis.set_ylim(self.ylim)

        pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        axis.yaxis.set_minor_locator(ticker.MultipleLocator(self.subs))
        axis.yaxis.set_major_locator(ticker.MultipleLocator(self.base))

        return axis

    def set_depth_body(self,axis):

		axis = self.boot(axis)

		axis.set_xlim(self.xlim)

		axis.tick_params(
			axis="y",which="both",direction="in",right=True,pad=-40)

		pyplot.setp(axis.get_yticklabels(),visible=False)

		for ytick in self.ticks:

			axis.annotate(
				f"{ytick:4.0f}",
				xy=((self.xmin+self.xmax)/2,ytick),
				horizontalalignment='center',
				verticalalignment='center',
				backgroundcolor='white',
				)

		return axis

    def set_curve_body(self,axis):
        """It staticly sets y-axis of the given axis. Required keywords in yaxis:
        
        limit:  defines the ylim
        base:   sets the frequency of major ticks
        subs:   sets the frequency of minor ticks
        """

        axis = self.boot(axis)

        axis.tick_params(axis="y",which="minor",left=False)

        axis.grid(axis="y",which='minor',color='k',alpha=0.4)
        axis.grid(axis="y",which='major',color='k',alpha=0.9)

        return axis

if __name__ == "__main__":

	pass
	