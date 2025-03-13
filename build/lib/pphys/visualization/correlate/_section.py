from matplotlib import pyplot

from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator

from ._booter import Booter
from ._formation import Formation

class Correlation():

	def __init__(self,tops:Formation=None,figsize=None):

		self.tops = tops

		self.figure = pyplot.figure(figsize=figsize)

	def set(self,**kwargs):

		gs = GridSpec(2,3,figure = self.figure,**kwargs)

		self.west_axis = self.figure.add_subplot(gs[0,0])
		self.west_axis.spines['bottom'].set_visible(False)
		self.set_axis(self.west_axis)

		self.head_axis = self.figure.add_subplot(gs[0,1])
		self.head_axis.spines['right'].set_visible(False)
		self.head_axis.spines['bottom'].set_visible(False)
		self.set_axis(self.head_axis)

		self.east_axis = self.figure.add_subplot(gs[0,2])
		self.east_axis.spines['bottom'].set_visible(False)
		self.east_axis.spines['left'].set_visible(False)
		self.set_axis(self.east_axis)

		self.depth_axis = self.figure.add_subplot(gs[1,0])
		self.depth_axis.spines['top'].set_visible(False)
		self.set_depth(self.depth_axis)

		self.scene_axis = self.figure.add_subplot(gs[1,1])
		self.scene_axis.spines['top'].set_visible(False)
		self.scene_axis.spines['right'].set_visible(False)
		self.set_axis(self.scene_axis)

		self.litho_axis = self.figure.add_subplot(gs[1,2])
		self.litho_axis.spines['left'].set_visible(False)
		self.litho_axis.spines['top'].set_visible(False)
		self.set_axis(self.litho_axis)

	@staticmethod
	def set_axis(axis):
		"""Configures the given axis to have no ticks and be within (0,1)."""

		axis.set_xlim((0,1))
		axis.set_ylim((0,1))

		axis.set_xticks([])
		axis.set_yticks([])

	@staticmethod
	def set_depth(axis,nbins=10,pad=-33):
		"""Configures the depth axis to have no ticks and be within (0,1)."""

		axis.set_xlim((0,1))
		axis.set_ylim((0,1))

		axis.yaxis.set_major_locator(MaxNLocator(nbins,prune='both'))
		axis.tick_params(axis='y',direction='in',right=True,pad=pad)

		axis.set_xticks([])
	
	def __call__(self,*args,**kwargs):
		"""Initializes the main scene of Correlation instance."""
		self.scene = Booter(*args,**kwargs)
		self.scene(self.scene_axis)

		return self

	def well(self,index):
		"""Returns the x-center for the given index."""
		return self.scene.xcenter(index)

	def add_curve(self,index,xvals,depth,yvalue,key=None,**kwargs):

		self.scene[index].plot(xvals,depth,**kwargs)

		self.scene.axis.plot(self.scene.xloc(index),[yvalue,]*2,**kwargs)

		self.scene.axis.text(self.well(index),yvalue,key,zorder=2,ha='center',va='center',
			bbox=dict(facecolor="white", edgecolor="none",pad=1))

	def add_top(self,key,**kwargs):
		"""Adds the formation top line to the main view."""
		xlocs = self.scene.xlocs()
		ylocs = self.scene.ylocs(self.tops[key])

		self.scene.axis.plot(xlocs,ylocs,**kwargs)

		if self.litho_axis is None:
			return

		self.litho_axis.plot([0,1],ylocs[-2:],**kwargs)

	def add_formation(self,key,**kwargs):
		"""Adds the formation fill to the main view."""
		xlocs = self.scene.xlocs()

		ytops,ybots = self.tops.limit(key)

		ytops = self.scene.ylocs(ytops)
		ybots = self.scene.ylocs(ybots)

		self.scene.axis.fill_between(xlocs,y1=ytops,y2=ybots,**kwargs)

		if self.litho_axis is None:
			return

		self.litho_axis.fill_between([0,1],y1=ytops[-2:],y2=ybots[-2:],**kwargs)

		ytext = (ytops[-1]+ybots[-1])/2

		self.litho_axis.text(0.5,ytext,key,va="center",ha="center",
			rotation=-90,fontsize="large",fontweight="bold"
			)

	def add_distance(self,index,value:float=None):

		self.head.annotate(
		    "", xy=(self.well(index),0.25),xytext=(self.well(index+1),0.25),
		    arrowprops=dict(arrowstyle="<->", lw=2)
		)

	@property
	def west(self):
		return self.west_axis

	@property
	def head(self):
		return self.head_axis

	@property
	def east(self):
		return self.east_axis

	@property
	def depth(self):
		return self.depth_axis

	@property
	def litho(self):
		return self.litho_axis