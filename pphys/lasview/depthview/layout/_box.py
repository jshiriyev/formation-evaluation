from ._axis import Axis

class Box():

	def __init__(self,xaxis:Axis,yaxis:Axis):

		self._xaxis = xaxis
		self._yaxis = yaxis

	@property
	def xaxis(self):
		return self._xaxis

	@property
	def yaxis(self):
		return self._yaxis

	def boot(self,axis):

		axis.set_xlim(self.xaxis.limits)
		axis.set_ylim(self.yaxis.limits)

		axis.set_xscale(self.xaxis.scale)

		pyplot.setp(axis.get_yticklabels(),visible=False)
        pyplot.setp(axis.get_yticklines(),visible=False)

        if self.scale=="linear":

            axis.xaxis.set_minor_locator(
            	ticker.MultipleLocator(self.minor))

            axis.xaxis.set_major_locator(
            	ticker.MultipleLocator(10))

        elif self.scale=="log":

            axis.xaxis.set_minor_locator(
            	ticker.LogLocator(base=10,subs=self.minor,numticks=12))

            axis.xaxis.set_major_locator(
            	ticker.LogLocator(base=10,numticks=12))

        axis.yaxis.set_minor_locator(
        	ticker.MultipleLocator(self.yaxis.minor))

        axis.yaxis.set_major_locator(
        	ticker.MultipleLocator(self.yaxis.major*10))

        axis.tick_params(axis="x",which="minor",bottom=False)
        axis.tick_params(axis="y",which="minor",left=False)

        axis.grid(axis="x",which='minor',color='k',alpha=0.4)
        axis.grid(axis="x",which='major',color='k',alpha=0.9)

        axis.grid(axis="y",which='minor',color='k',alpha=0.4)
        axis.grid(axis="y",which='major',color='k',alpha=0.9)

        return axis

    @property
    def ticks(self):
        return ticker.MultipleLocator(self.base).tick_values(*self.yaxis.limits)