"""Matplotlib axes of a one-page log, built from its Layout."""

from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ._layout import Layout
from ._xaxis import XAxisDict


class Builder(Layout):
	"""Builds the axes of a one-page log from its Layout.

	Calling a Builder with a figure adds one body axis per trail (the
	track itself) and, unless the label spot is None, one head axis above or
	below it for the header rows. The Builder knows nothing about well data:
	WellView adds the curves.
	"""

	def __init__(self,**kwargs):
		"""Takes the Layout keywords."""
		super().__init__(**kwargs)

		self.heads:list[Axes] = []
		self.bodies:list[Axes] = []

	def __call__(self,figure:Figure) -> list[Axes]:
		"""Add the trails to figure and return their axes, head before body.

		The head and body axes are also kept in ``heads`` and ``bodies``,
		one per trail; ``heads`` is empty without a header.
		"""
		spot = self._label.spot

		self.gspec = figure.add_gridspec(
			nrows = 1 if spot is None else 2,
			ncols = self.ntrail,
			width_ratios = self.widths,
			height_ratios = self.height_ratios,
			wspace = 0,
			hspace = 0,
			)

		head_row,body_row = (0,1) if spot=="top" else (1,0)

		self.heads,self.bodies = [],[]

		for index,xaxis in enumerate(self._xaxes):

			if spot is not None:
				self.heads.append(self.head(figure.add_subplot(self.gspec[head_row,index]),xaxis))

			body = figure.add_subplot(self.gspec[body_row,index])

			self.body_x(body,xaxis)
			self.body_y(body,xaxis,depth=index in self._depth.spot)

			self.bodies.append(body)

		if not self.heads:
			return list(self.bodies)

		return [axis for pair in zip(self.heads,self.bodies,strict=True) for axis in pair]

	def head(self,axis:Axes,xaxis:XAxisDict) -> Axes:
		"""Configure the head (header rows) axis of a trail.

		It shares the trail's x range and scale, so header items can be placed
		at track values, and spans the label limit vertically. Rows count from
		the track outwards: upwards for a top header, downwards for a bottom one.
		"""
		axis.set_xscale("log" if xaxis.scale=="log10" else "linear")
		axis.set_xlim(xaxis.limit)

		lower,upper = self._label.limit
		axis.set_ylim((lower,upper) if self._label.spot=="top" else (upper,lower))

		axis.tick_params(which="both",bottom=False,left=False,labelbottom=False,labelleft=False)

		return axis

	def body_x(self,axis:Axes,xaxis:XAxisDict) -> Axes:
		"""Configure the x axis of a trail: range, scale and vertical grid lines."""
		axis.set_xscale("log" if xaxis.scale=="log10" else "linear")
		axis.set_xlim(xaxis.limit)

		if xaxis.scale=="log10":
			axis.xaxis.set_major_locator(ticker.LogLocator(base=10,numticks=12))
			axis.xaxis.set_minor_locator(ticker.LogLocator(base=10,subs=xaxis.minor,numticks=12))
		else:
			axis.xaxis.set_major_locator(ticker.MultipleLocator(xaxis.major))
			axis.xaxis.set_minor_locator(ticker.MultipleLocator(xaxis.minor))

		# The grid marks the values; the tick marks and labels stay hidden.
		axis.tick_params(axis="x",which="both",bottom=False,labelbottom=False)

		if xaxis.grid:
			axis.grid(axis="x",which='minor',color='lightgray',alpha=0.4)
			axis.grid(axis="x",which='major',color='lightgray',alpha=0.9)

		return axis

	def body_y(self,axis:Axes,xaxis:XAxisDict,depth:bool=False) -> Axes:
		"""Configure the y (depth) axis of a trail.

		Depth trails get inward depth ticks on both sides; the others get
		depth grid lines when both their own and the depth grid are on.
		"""
		axis.set_ylim(self._depth.limit)

		axis.yaxis.set_major_locator(ticker.MultipleLocator(self._depth.major))
		axis.yaxis.set_minor_locator(ticker.MultipleLocator(self._depth.minor))

		if depth:
			axis.tick_params(axis="y",which="both",direction="in",left=True,right=True,labelleft=False)
			return axis

		axis.tick_params(axis="y",which="both",left=False,labelleft=False)

		if xaxis.grid and self._depth.grid:
			axis.grid(axis="y",which='minor',color='lightgray',alpha=0.4)
			axis.grid(axis="y",which='major',color='lightgray',alpha=0.9)

		return axis
