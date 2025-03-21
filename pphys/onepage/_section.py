from matplotlib import pyplot

from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator

from .section._booter import Booter

from ._weaver import Weaver

class Correlation():

	def __init__(self,*args,**kwargs):

		self._wells = list(args)
		self.figure = pyplot.figure(**kwargs)

	@property
	def wells(self):
		return self._wells

	def __getitem__(self,key):
		return self._wells[key]

	def __iter__(self):
		yield from self._wells

	def set(self,depth:dict=None,**kwargs):

		gs = GridSpec(2,3,figure=self.figure,**kwargs)

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
		self.set_depth_axis(self.depth_axis,**(depth or {}))

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
	def set_depth_axis(axis,maxnlocator:dict=None,tick_params:dict=None):
		"""Configures the depth axis to have no ticks and be within (0,1)."""
		axis.set_xlim((0,1))
		axis.set_ylim((0,1))

		axis.set_xticks([])

		maxnlocator = (maxnlocator or {})
		tick_params = (tick_params or {})

		if not maxnlocator.get('nbins'):
			maxnlocator['nbins'] = 10

		if not maxnlocator.get('prune'):
			maxnlocator['prune'] = 'both'

		axis.yaxis.set_major_locator(MaxNLocator(**maxnlocator))

		if not tick_params.get('direction'):
			tick_params['direction'] = 'in'

		if not tick_params.get('right'):
			tick_params['right'] = True

		axis.yaxis.set_tick_params(**tick_params)
	
	def __call__(self,*args,**kwargs):
		"""Initializes the main scene of Correlation instance."""
		self.scene = Booter(*args,**kwargs)
		
		self.scene(self.scene_axis)

		return self

	def add_curve(self,index,xvals,depth,ylabel,key=None,**kwargs):

		self.scene[index].plot(xvals,depth,**kwargs)

		self.scene.axis.plot(self.scene.xloc(index),[ylabel,]*2,**kwargs)

		x = self.scene.xcenter(index)

		self.scene.axis.text(x,ylabel,key,zorder=2,ha='center',va='center',
			bbox=dict(facecolor="white", edgecolor="none",pad=1))

	def add_gradient(self,index,xvals,depth,ylabel,key=None,xmin=None,xmax=None,left=False,**kwargs):

		Weaver.fill_gradient(self.scene[index],xvals,depth,**kwargs)

		self.scene.axis.plot(self.scene.xloc(index),[ylabel,]*2,**kwargs)

		x = self.scene.xcenter(index)

		self.scene.axis.text(x,ylabel,key,zorder=2,ha='center',va='center',
			bbox=dict(facecolor="white", edgecolor="none",pad=1))

	def tops(self,key:str):
		"""Returns well tops for the given key as a list."""
		return [w.zones[key] for w in self._wells]

	def add_top(self,key,**kwargs):
		"""Adds the formation top line to the main view."""
		xlocs = self.scene.xlocs()
		ylocs = self.scene.ylocs(self.tops(key))

		self.scene.axis.plot(xlocs,ylocs,**kwargs)

		if self.litho_axis is None:
			return

		self.litho_axis.plot([0,1],ylocs[-2:],**kwargs)

	def add_formation(self,key,**kwargs):
		"""Adds the formation fill to the main view."""
		xlocs = self.scene.xlocs()

		ytops,ybots = zip(*(w.zones.limit(key) for w in self._wells))

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

		x0 = self.scene.xcenter(index)
		x1 = self.scene.xcenter(index+1)

		self.head.annotate(
		    "", xy=(x0,0.25),xytext=(x1,0.25),
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
	