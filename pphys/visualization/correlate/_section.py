from _booter import Booter

class CrossSection():

	def __init__(self,**kwargs):

		self._keys,self._tops = [],[]

		for name,tops in kwargs.items():
			self._keys.append(name)
			self._tops.append(tops)

	def set_axis(self,axis):

		axis.set_xlim((0,1))
		axis.set_ylim((0,1))

		axis.set_xticks([])
		axis.set_yticks([])

	def __call__(self,axis,*args,**kwargs):

		self.main = Booter(*args,**kwargs)
		self.main = self.main(axis)

		return self

	@property
	def xnodes(self):
		return self.main.get_xtopline()

	def add_topline(self,index,side=None,**kwargs):

		ytops = self.main.get_ytopline(self._tops[index])

		self.main.axis.plot(self.xnodes,ytops,**kwargs)

		if side is None:
			return

		side.plot([0,1],ytops[-2:],**kwargs)

	def add_formation(self,index,side=None,**kwargs):

		ytops = self.main.get_ytopline(self._tops[index+0])
		ybots = self.main.get_ytopline(self._tops[index+1])

		self.main.axis.fill_between(self.xnodes,y1=ytops,y2=ybots,**kwargs)

		if side is None:
			return

		side.fill_between([0,1],y1=ytops[-2:],y2=ybots[-2:],**kwargs)

		ytext = (ytops[-1]+ybots[-1])/2

		side.text(0.5,ytext,self._keys[index],
			va="center",ha="center",rotation=-90,
			fontsize="large",fontweight="bold"
			)