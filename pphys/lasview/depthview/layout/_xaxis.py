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
	def xlim(self):

		if self.scale == "linear":
			return (self.skip.xmin,self.skip.xmax+self.cycle*10)
		elif self.scale == "log":
			return (1+self.skip.xmin,(1+self.skip.xmax)*10**self.cycle)

		raise ValueError(f"{scale} has not been defined! options: {{linear,log}}")

    def boot(self,axis):
        """It staticly sets x-axis of the given axis. Required keywords in xaxis:
        
        limit:  defines the xlim
        scale:  linear or log
        subs:   sets the frequency of minor ticks
        """

        axis.set_xlim(self.xlim)

        axis.set_xscale(self.scale)

        if self.scale=="linear":
            axis.xaxis.set_minor_locator(ticker.MultipleLocator(self.subs))
            axis.xaxis.set_major_locator(ticker.MultipleLocator(10))
        elif self.scale=="log":
            axis.xaxis.set_minor_locator(ticker.LogLocator(base=10,subs=self.subs,numticks=12))
            axis.xaxis.set_major_locator(ticker.LogLocator(base=10,numticks=12))

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        axis.tick_params(axis="x",which="minor",bottom=False)

        axis.grid(axis="x",which='minor',color='k',alpha=0.4)
        axis.grid(axis="x",which='major',color='k',alpha=0.9)

	@staticmethod
    def set_linxaxis(curve,xaxis):

        amin,amax = xaxis["limit"]

        vmin,vmax = curve.limit

        if vmin>vmax:
            vmin,vmax = vmax,vmin
            reverse = True
        else:
            reverse = False

        # print(f"{amin=},",f"{amax=}")
        # print(f"given_{vmin=},",f"given_{vmax=}")

        delta_axis = numpy.abs(amax-amin)
        delta_vals = numpy.abs(vmax-vmin)

        # print(f"{delta_vals=}")

        # delta_powr = -numpy.floor(numpy.log10(delta_vals))

        # print(f"{delta_powr=}")

        # vmin = numpy.floor(vmin*10**delta_powr)/10**delta_powr

        # vmax_temp = numpy.ceil(vmax*10**delta_powr)/10**delta_powr

        # print(f"{vmin=},",f"{vmax_temp=}")

        if curve.multp is None:

            # multp_temp = (vmax_temp-vmin)/(delta_axis)
            multp_temp = (vmax-vmin)/(delta_axis)
            multp_powr = -numpy.log10(multp_temp)
            # multp_powr = -numpy.floor(numpy.log10(multp_temp))

            # print(f"{multp_temp=},")

            # curve.multp = numpy.ceil(multp_temp*10**multp_powr)/10**multp_powr
            curve.multp = multp_temp

            # print(f"{curve.multp=},")
        
        axis_vals = amin+(curve.data-vmin)/curve.multp

        vmax = delta_axis*curve.multp+vmin
        
        # print(f"normalized_{vmin=},",f"normalized_{vmax=}")

        if reverse:
            curve.xaxis = amax-axis_vals
        else:
            curve.xaxis = axis_vals

        if reverse:
            curve.limit = (vmax,vmin)
        else:
            curve.limit = (vmin,vmax)

    @staticmethod
    def set_logxaxis(curve,xaxis):

        vmin,_ = curve.limit

        if curve.multp is None:
            curve.multp = numpy.ceil(numpy.log10(1/vmin))

        axis_vals = curve.data*10**curve.multp

        vmin = min(xaxis["limit"])/10**curve.multp
        vmax = max(xaxis["limit"])/10**curve.multp

        curve.xaxis = axis_vals
        curve.limit = (vmin,vmax)

if __name__ == "__main__":

	xaxis = XAxis(subs=2,scale="log",skip=(1,3))

	print(xaxis.skip.xmax)

	print(xaxis.limit)


