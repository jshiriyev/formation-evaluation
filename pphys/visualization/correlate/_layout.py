class Layout():

	def __init__(self,nums,xpad=0.1,ypad=0.1):

		self.nums = nums

		self.xpad = xpad
		self.ypad = ypad

		self.xlen = None
		self.ylen = None

	@property
	def nums(self):
		return self._nums

	@nums.setter
	def nums(self,value):
		self._nums = value

	@property
	def xpad(self):
		return self._xpad

	@xpad.setter
	def xpad(self,value):
		self._xpad = value

	@property
	def ypad(self):
		return self._ypad

	@ypad.setter
	def ypad(self,value):
		self._ypad = value

	@property
	def xlen(self):
		return self._xlen

	@xlen.setter
	def xlen(self,value):
		self._xlen = (1./self.nums-self.xpad)

	@property
	def ylen(self):
		return self._ylen

	@ylen.setter
	def ylen(self,value):
		self._ylen = (1.-self.ypad)
	
	def get(self,index):
		return [self.xpad*3/4.+index/self.nums,self.ypad*1/4,self.xlen,self.ylen]

	def tops(self,axes,depths):

		xaxis,yaxis = [],[]

		for index,(axis,depth) in enumerate(zip(axes,depths)):

			xaxis.append((index+0)/self.nums+self.xpad*3/4.)
			xaxis.append((index+1)/self.nums-self.xpad*1/4.)

			ymax,ymin = axis.get_ylim()

			top = self.ylen*(ymin-depth)/(ymax-ymin)+(1-self.ypad*3/4.)

			yaxis.append(top.tolist())
			yaxis.append(top.tolist())

		xaxis[ 0] = 0.
		xaxis[-1] = 1.

		return xaxis,yaxis