from _layout import Layout

class Booter(Layout):

	def __init__(self,*args,**kwargs):

		super().__init__(*args,**kwargs)

		self.axin = None

	@property
	def axin(self):
		return self._axin

	@axin.setter
	def axin(self,value):
		self._axin = []

	def __getitem__(self,key):
		return self._axin[key]

	def __call__(self,axis):

		self.axis = axis
		self.axin = None
		
		for index in range(self.nums):

			axin = self._axis.inset_axes(super().get(index))

			axin.yaxis.set_inverted(True)

			axin.xaxis.set_label_position('top')
			axin.xaxis.set_ticks_position('top')

			self.axin.append(axin)

		return self

	@property
	def axis(self):
		return self._axis

	@axis.setter
	def axis(self,value):
		self._axis = value

	def get_xtopline(self):

		xaxis = []

		for index,_ in enumerate(self._axin):

			xaxis.append((index+0)/self.nums+self.xpad*3/4.)
			xaxis.append((index+1)/self.nums-self.xpad*1/4.)

		xaxis[ 0] = 0.
		xaxis[-1] = 1.

		return xaxis
	
	def get_ytopline(self,tops):

		yaxis = []

		for axin,depth in zip(self._axin,tops):

			ymax,ymin = axin.get_ylim()

			top = self.ylen*(ymin-depth)/(ymax-ymin)+(1-self.ypad*3/4.)

			yaxis.append(top.tolist())
			yaxis.append(top.tolist())

		return yaxis

	def set_zorder(self):

		self.axis.set_zorder(1)

		for index in range(self.nums):
			self[index].set_zorder(-1)