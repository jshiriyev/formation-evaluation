from matplotlib import gridspec
from matplotlib import pyplot as plt
from matplotlib import ticker

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ._layout import Layout

class Builder(Layout):

	def __init__(self,**kwargs):
		"""
		Builder class that extends the Layout class to configure and manage 
		plotting layouts.

		This class can be used as a wrapper to bootstrap and manage visual layouts
		using matplotlib.

		Parameters:
		**kwargs: Arbitrary keyword arguments passed to the Layout constructor.

		"""
		super().__init__(**kwargs)

	def __call__(self,figure:Figure):
		"""
		Build the full layout by populating a matplotlib figure with subplots
		based on internal layout settings (x-axes, labels, depths).

		"""
		nrows = 1 if self.label.spot is None else 2

		self.gspec = gridspec.GridSpec(
			nrows = nrows,
			ncols = self.ntrail,
			figure = figure,
			width_ratios = self.widths,
			height_ratios = self.heights,
			wspace = 0,
			hspace = 0,
			)
		
		# Iterate over each trail/xaxis pair to create subplots
		for index,xaxis in enumerate(self.xaxes):

			# Create subplot(s) based on label position
			if self.label.spot is None:
				body_axis = figure.add_subplot(self.gspec[index])
			elif self.label.spot == "top":
				head_axis = figure.add_subplot(self.gspec[0,index])
				body_axis = figure.add_subplot(self.gspec[1,index])
			elif self.label.spot == "bottom":
				head_axis = figure.add_subplot(self.gspec[1,index])
				body_axis = figure.add_subplot(self.gspec[0,index])
			else:
				raise ValueError(f"Invalid label.spot: {self.label.spot}")

			# Draw head if applicable
			if self.label.spot is not None:
				self.head(head_axis,xaxis)

			# Draw body, enabling depth on specified trails
			self.body_x(body_axis,xaxis,depth=index in self.depth.spot)
			self.body_y(body_axis,xaxis,depth=index in self.depth.spot)

		return figure.get_axes()

	def head(self,axis:Axes,xaxis):
		"""Configure the head (label row) axis for a given x-axis layout."""

		# Set horizontal range (x-axis)
		axis.set_xlim(xaxis.limit)

		plt.setp(axis.get_xticklabels(),visible=False)
		plt.setp(axis.get_xticklines(),visible=False)

		# Set vertical range (y-axis) based on label limits
		axis.set_ylim(self.label.limit)

		plt.setp(axis.get_yticklabels(),visible=False)
		plt.setp(axis.get_yticklines(),visible=False)

		return axis

	def body_x(self,axis:Axes,xaxis,depth:bool=False):
		"""Configure the body (curve row) x-axis for a given x-axis layout.
		
		This includes setting limits, tick locators (major/minor), and grid lines
		based on the axis scale ('linear' or 'log10').

		"""
		# Set x-axis range and scale
		axis.set_xlim(xaxis.limit)
		axis.set_xscale("log" if xaxis.scale=="log10" else xaxis.scale)

		# Hide tick labels and tick lines by default
		plt.setp(axis.get_xticklabels(),visible=False)
		plt.setp(axis.get_xticklines(),visible=False)

		# Hide minor ticks visually
		axis.tick_params(axis="x",which="minor",bottom=False)

		# Skip further configuration if depth track
		if depth:
			return

		# Configure tick locators and grids based on scale
		if xaxis.scale=="linear":
			axis.xaxis.set_major_locator(ticker.MultipleLocator(xaxis.major))
			axis.xaxis.set_minor_locator(ticker.MultipleLocator(xaxis.minor))
		elif xaxis.scale=="log10":
			axis.xaxis.set_major_locator(ticker.LogLocator(base=10,numticks=12))
			axis.xaxis.set_minor_locator(
				ticker.LogLocator(base=10,subs=xaxis.minor,numticks=12))
		else:
			raise ValueError(f"Unsupported x-axis scale: {xaxis.scale}")

		# Add gridlines for both major and minor ticks
		axis.grid(axis="x",which='minor',color='lightgray',alpha=0.4,zorder=-1)
		axis.grid(axis="x",which='major',color='lightgray',alpha=0.9,zorder=-1)

		return axis

	def body_y(self,axis:Axes,xaxis,depth:bool=False):
		"""Configure the y-axis of the body (curve row) using depth settings.
		
		This includes setting y-limits, tick locators, and optionally displaying
		ticks inward for depth tracks.

		"""
		# Set vertical axis range using depth limits
		axis.set_ylim(self.depth.limit)
		
		# Hide y tick labels
		plt.setp(axis.get_yticklabels(),visible=False)

		# Set major and minor tick locators
		axis.yaxis.set_major_locator(ticker.MultipleLocator(self.depth.major))
		axis.yaxis.set_minor_locator(ticker.MultipleLocator(self.depth.minor))
		
		if depth:
			# For depth tracks (MD or TVD), show inward ticks on the right side
			axis.tick_params(
				axis="y",which="both",
				direction="in",right=True,
				pad=-40
				)
			return axis

		# Hide y tick lines
		plt.setp(axis.get_yticklines(),visible=False)

		# Hide minor ticks on the left
		axis.tick_params(axis="y",which="minor",left=False)

		# Add light gray grid lines for both major and minor ticks
		axis.grid(axis="y",which='minor',color='lightgray',alpha=0.4,zorder=-1)
		axis.grid(axis="y",which='major',color='lightgray',alpha=0.9,zorder=-1)

		return axis

