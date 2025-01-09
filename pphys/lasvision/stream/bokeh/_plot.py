import lasio

from lasview.depthwise import Layout

class Plot():

	def __init__(self,lasfile:lasio.LASFile,layout:Layout):

		self._lasfile = lasfile

		self._layout = layout

	@property
	def lasfile(self):
		return self._lasfile

	@property
	def layout(self):
		return self._layout
	
	