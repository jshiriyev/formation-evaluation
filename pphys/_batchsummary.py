import lasio

from matplotlib import gridspec
from matplotlib import pyplot

import numpy

from borepy.textio._browser import Browser

class WellSummary(Browser):

	def __init__(self,filepaths,zones=None):

		super().__init__()

		filepaths = [self.get_abspath(path) for path in filepaths]

		self.lasfiles = [lasio.read(path) for path in filepaths]

		self.filepaths = [path.split("\\")[-1] for path in filepaths]

		self.axes = []

		self.zones = zones

	def save(self,filepath=None,fstring=None):

		self.figure = pyplot.figure()

		ncols = len(self.lasfiles)
		nrows = 2

		self.gspecs = gridspec.GridSpec(
			nrows=nrows,ncols=ncols,
			figure=self.figure,
			height_ratios=[25,1])

		if fstring is None:
			fstring = "{}"

		self.figure.set_figwidth(4*ncols)
		self.figure.set_figheight(26)

		for index,lasfile in enumerate(self.lasfiles):

			axis_table = self.figure.add_subplot(self.gspecs[0,index])

			self._table(lasfile,axis_table,fstring)

			axis_title = self.figure.add_subplot(self.gspecs[1,index])

			self._caption(self.filepaths[index],axis_title)

		self.gspecs.tight_layout(self.figure)

		self.gspecs.update(wspace=2,hspace=1)

		self.figure.suptitle(f"Well-{self._name()} Log Summary")

		if filepath is None:
			self.figure.savefig(f"Well-{self._name()}_Log_Summary.png")
		else:
			self.figure.savefig(filepath)

	def _name(self):

		return self.lasfiles[0].well['WELL'].value

	def _table(self,lasfile,axis,fstring=None):

		tops,bottoms = [],[]

		for curve in lasfile.curves:

			top,bottom = self._edge_nans(curve.data)

			tops.append(fstring.format(lasfile[0][top]))

			bottoms.append(fstring.format(lasfile[0][bottom]))

		cellText = numpy.array([tops,bottoms]).T

		# self.figure.set_figheight(len(tops))

		ccolors = pyplot.cm.BuPu(numpy.full(2,0.1))

		pyplot.box(on=None)

		axis.get_xaxis().set_visible(False)
		axis.get_yaxis().set_visible(False)

		axis.axis('tight')
		axis.axis('off')

		axis_table = axis.table(
			cellText=cellText,cellLoc="center",
			rowLabels=lasfile.keys(),rowLoc="right",
			colLabels=("Top","Bottom"),colLoc="center",
			colWidths=(1,1),colColours=ccolors,
			loc="center")

		axis_table.scale(1,1)

	def _caption(self,filename,axis):

		axis.set_xlim((0,1))
		axis.set_ylim((0,1))

		axis.get_xaxis().set_visible(False)
		axis.get_yaxis().set_visible(False)

		pyplot.box(on=None)

		axis.text(0.5,0.5,filename,
        	horizontalalignment='center',
        	verticalalignment='center',
        	transform=axis.transAxes)

	def _edge_nans(self,array):

		isnotnan = ~numpy.isnan(array)

		Tindex = numpy.argmax(isnotnan)

		Bindex = array.size-numpy.argmax(numpy.flip(isnotnan))-1

		return Tindex,Bindex
