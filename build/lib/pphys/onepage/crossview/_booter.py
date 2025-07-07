from itertools import chain

from ._layout import Layout

class Booter(Layout):
	"""A subclass of Layout that manages a list of axin."""

	def __init__(self,*args,**kwargs):
		"""Initializes the Booter class by calling the Layout constructor"""
		super().__init__(*args,**kwargs)

		self.axin = []

	def __getitem__(self,key):
		"""Allows indexed access to elements in the `axin` list."""
		return self.axin[key]

	def __iter__(self):
		"""Allows iteration over the `axin` list."""
		yield from self.axin

	def xlocs(self):
		"""Generates a list of x-axis locations based on number of axin."""
		xaxis = list(chain.from_iterable([self.xloc(index) for index in range(self.nums)]))

		if xaxis: # Ensure xaxis is not empty before modifying elements
			xaxis[ 0] = 0.
			xaxis[-1] = 1.

		return xaxis
	
	def ylocs(self,tops):
		"""Generates a list of y-axis locations for the given tops."""
		yaxis = []

		for axin,depth in zip(self.axin,tops):

			ymax,ymin = axin.get_ylim()

			# if depth>ymax and depth<ymin:
			# 	continue

			top = 1-self.ypad*3/4.-self.ylen*(depth-ymin)/(ymax-ymin)

			yaxis.extend([top.tolist()]*2)

		return yaxis

	def __call__(self,axis):
		"""Initializes the main axis and creates inset axes (axin)."""
		self.axis = axis
		
		self.axin = [
			self._get_inset(index) for index in range(self.nums)
			]

		return self

	def _get_inset(self,index):
	    """Creates and configures an inset axis."""
	    axin = self.axis.inset_axes(self.bounds(index))

	    axin.yaxis.set_inverted(True)
	    axin.xaxis.set_label_position('top')
	    axin.xaxis.set_ticks_position('top')

	    return axin

	def set_zorder(self):
		"""Sets the z-order of the main axis to 1 and all axin to -1."""
		self.axis.set_zorder(1)

		for axin in self:
			axin.set_zorder(0)

