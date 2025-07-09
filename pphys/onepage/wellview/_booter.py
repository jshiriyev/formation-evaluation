from matplotlib import gridspec
from matplotlib import pyplot as plt
from matplotlib import ticker

from ._layout import Layout

class Boot(Layout):

	def __init__(self,*args,**kwargs):
		"""Initializes the Boot class by calling the Layout constructor"""
		super().__init__(*args,**kwargs)

	def __call__(self,figure):

		nrows = 1 if self.label.spot is None else 2

		self.gspec = gridspec.GridSpec(
			nrows = nrows, ncols = self.ntrail,
			figure = figure,
			width_ratios = self.widths,
			height_ratios = self.heights,
			wspace = 0, hspace = 0,
			)
		
		for index,xaxis in enumerate(self._xaxes):

			if self.label.spot is None:
				body_axis = figure.add_subplot(self.gspec[index])
			elif self.label.spot == "top":
				head_axis = figure.add_subplot(self.gspec[0,index])
				body_axis = figure.add_subplot(self.gspec[1,index])
			elif self.label.spot == "bottom":
				head_axis = figure.add_subplot(self.gspec[1,index])
				body_axis = figure.add_subplot(self.gspec[0,index])

			if self.label.spot is not None:
				self.head(head_axis,xaxis)

			if index in self.depth.spot:
				self.body_depth(body_axis,xaxis)
			else:
				self.body_curve(body_axis,xaxis)

		return figure.get_axes()

	def head(self,axis,xaxis):

		axis.set_xlim(xaxis.limit)

		plt.setp(axis.get_xticklabels(),visible=False)
		plt.setp(axis.get_xticklines(),visible=False)

		axis.set_ylim(self.label.limit)

		plt.setp(axis.get_yticklabels(),visible=False)
		plt.setp(axis.get_yticklines(),visible=False)

		return axis

	def body_depth(self,axis,xaxis):

		axis.set_xlim(xaxis.limit)

		plt.setp(axis.get_xticklabels(),visible=False)
		plt.setp(axis.get_xticklines(),visible=False)

		axis.set_ylim(self.depth.limit)

		plt.setp(axis.get_yticklabels(),visible=False)

		axis.yaxis.set_minor_locator(
			ticker.MultipleLocator(self.depth.minor))

		axis.yaxis.set_major_locator(
			ticker.MultipleLocator(self.depth.major))

		axis.tick_params(
			axis="y",which="both",direction="in",right=True,pad=-40)

		return axis

	def body_curve(self,axis,xaxis):

		axis.set_xlim(xaxis.limit)

		axis.set_xscale(xaxis.scale)

		plt.setp(axis.get_xticklabels(),visible=False)
		plt.setp(axis.get_xticklines(),visible=False)

		axis.set_ylim(self.depth.limit)
		
		plt.setp(axis.get_yticklabels(),visible=False)
		plt.setp(axis.get_yticklines(),visible=False)

		if xaxis.scale=="linear":

			axis.xaxis.set_minor_locator(
				ticker.MultipleLocator(xaxis.minor))

			axis.xaxis.set_major_locator(
				ticker.MultipleLocator(xaxis.major))

		elif xaxis.scale=="log":

			axis.xaxis.set_minor_locator(
				ticker.LogLocator(base=10,subs=xaxis.minor,numticks=12))

			axis.xaxis.set_major_locator(
				ticker.LogLocator(base=10,numticks=12))

		axis.yaxis.set_minor_locator(
			ticker.MultipleLocator(self.depth.minor))

		axis.yaxis.set_major_locator(
			ticker.MultipleLocator(self.depth.major))

		axis.tick_params(axis="x",which="minor",bottom=False)
		axis.tick_params(axis="y",which="minor",left=False)

		axis.grid(axis="x",which='minor',color='lightgray',alpha=0.4,zorder=-1)
		axis.grid(axis="x",which='major',color='lightgray',alpha=0.9,zorder=-1)

		axis.grid(axis="y",which='minor',color='lightgray',alpha=0.4,zorder=-1)
		axis.grid(axis="y",which='major',color='lightgray',alpha=0.9,zorder=-1)

		return axis

