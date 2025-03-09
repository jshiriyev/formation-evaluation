class Casing():

	def __init__(self,depth,outdiam=None):

		self._depth = depth

		self._outdiam = outdiam

	@property
	def depth(self):
		return self._depth

	@property
	def outdiam(self):
		return self._outdiam
	
	