from dataclasses import dataclass

@dataclass
class Skip:
	lower : int
	upper : int

class Axis():

	def __init__(self,*,major=2,minor=None,scale='linear',skip:tuple=None):
		"""
		It initializes axis of box in track plot:

		major 	: sets the number of major units in the axis
		minor 	: sets the frequency of minor ticks

        scale   : axis scale: linear or logarithmic
		skip 	: how many minor units to skip from lower and
				  upper side, tuple of two integers
		"""

		self._major = major
		self._minor = range(1,10) if minor is None else minor

        self._scale = scale

		skip = (0,0) if skip is None else skip

		self._skip = Skip(*skip)

	@property
	def major(self):
		return self._major

	@property
	def minor(self):
		return self._minor

    @property
    def scale(self):
        return self._scale

	@property
	def skip(self):
		return self._skip
	
	@property
	def limits(self):

		if self.scale == "linear":
			return (0+self.skip.lower,self.major*10+self.skip.upper)

		if self.scale == "log":
			return (1+self.skip.lower,(1+self.skip.upper)*10**self.major)

		raise ValueError(f"{self.scale} has not been defined! options: {{linear,log}}")

    def __call__(self,curve):

        amin,amax = self.limits

        vmin,vmax,reverse = self.get_limits(curve.limit)

        delta_axis = numpy.abs(amax-amin)
        delta_vals = numpy.abs(vmax-vmin)

        # delta_powr = -numpy.floor(numpy.log10(delta_vals))

        # vmin = numpy.floor(vmin*10**delta_powr)/10**delta_powr

        # vmax_temp = numpy.ceil(vmax*10**delta_powr)/10**delta_powr

        if curve.multp is None:

            # multp_temp = (vmax_temp-vmin)/(delta_axis)
            multp_temp = (vmax-vmin)/(delta_axis)
            multp_powr = -numpy.log10(multp_temp)
            # multp_powr = -numpy.floor(numpy.log10(multp_temp))

            # curve.multp = numpy.ceil(multp_temp*10**multp_powr)/10**multp_powr
            curve.multp = multp_temp
        
        axis_vals = amin+(curve.data-vmin)/curve.multp

        vmax = delta_axis*curve.multp+vmin

        # def set_logxaxis(self,curve):

        vmin,_ = curve.limit

        if curve.multp is None:
            curve.multp = numpy.ceil(numpy.log10(1/vmin))

        axis_vals = curve.data*10**curve.multp

        vmin = min(self.limits)/10**curve.multp
        vmax = max(self.limits)/10**curve.multp

        if reverse:
            return amax-axis_vals,(vmax,vmin)

        return axis_vals,(vmin,vmax)

    @staticmethod
    def get_limits(limits:tuple):
        """Returns Min, Max, and Reverse Flag based on axis limits."""
        return min(limits),max(limits),True if limits[0]>limits[-1] else False

    @staticmethod
    def get_length(limits:tuple):
        """Returns the length based on axis limits."""
        return max(limits)-min(limits)

if __name__ == "__main__":

	xaxis = XAxis(subs=2,scale="log",skip=(1,3))

	print(xaxis.skip.xmax)

	print(xaxis.limit)


