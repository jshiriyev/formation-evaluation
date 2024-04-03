class Page():

	def __init__(self,height,width):

		self.height,self.width = height,width

	@property
	def portrait(self):
		return (self.height,self.width)
	

	@property
	def landscape(self):
		return (self.width,self.height)
	