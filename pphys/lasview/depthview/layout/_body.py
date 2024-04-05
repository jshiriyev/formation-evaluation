from ._axis import Axis

class Body(Box):

	def __init__(self,xaxis:Axis,yaxis:Axis):

		super().__init__(xaxis,yaxis)

class Depth(Body):

	def __init__(self,*args,**kwargs):

		super().__init__(*args,**kwargs)
	
	def boot(self,axis):

		axis = super().boot(axis)

		axis.tick_params(
		    axis="y",which="both",direction="in",right=True,pad=-40)

		for ytick in self.ticks:

			axis.annotate(
				f"{ytick:4.0f}",
				xy=((self.xmin+self.xmax)/2,ytick),
				horizontalalignment='center',
				verticalalignment='center',
				backgroundcolor='white',
				)

		return axis