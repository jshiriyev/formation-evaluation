import tkinter as tk

from tkinter import ttk

from matplotlib import gridspec
from matplotlib import pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import LogFormatter
from matplotlib.ticker import LogFormatterExponent
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.ticker import NullLocator
from matplotlib.ticker import ScalarFormatter

import numpy as np

from PIL import ImageTk, Image

class LogView():

	lineColors = (
		"black",
		"crimson",
		"blue",
		"sienna",
		)

	spinerelpos = (0,0.1,0.2,0.3)

	def __init__(self,root):

		self.root = root

		self.root.title("RockPy")

		self.frame = tk.Frame(root)
		self.frame.pack(side=tk.TOP,fill=tk.BOTH,expand=1)

		self.canvas = tk.Canvas(self.frame)
		self.canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

		self.scrollbar = tk.Scrollbar(self.frame) #,orient=tk.VERTICAL
		self.scrollbar.pack(side=tk.LEFT,fill=tk.Y)

		self.canvas.config(yscrollcommand=self.scrollbar.set)
		self.scrollbar.config(command=self.canvas.yview)

		self.canvas.bind_all("<MouseWheel>",self._on_mousewheel)

	def set_image(self):

		img = ImageTk.PhotoImage(Image.open("FS.png"))

		label = tk.Label(master=self.canvas,image=img)
		label.image = img

		# self.canvas.config(scrollregion=self.canvas.bbox(tk.constants.ALL),width=300,height=300)

		label.pack(side=tk.LEFT)

		self.canvas.config(scrollregion=self.canvas.bbox(tk.constants.ALL),width=300,height=300)

	def set_figure(self,numaxes=1,winch=3,hinch=128,dpi=100.):

		zmult = int((500-0)/20.)

		self.spinepos = [1+x/zmult for x in self.spinerelpos]

		self.figure = plt.figure(figsize=(winch*numaxes,hinch),dpi=dpi)

		self.grids = gridspec.GridSpec(1,numaxes)
		self.grids.update(wspace=0)

		self.figcanvas = FigureCanvasTkAgg(self.figure,self.canvas)

		canwin = self.canvas.create_window(0,0,window=self.figcanvas.get_tk_widget(),anchor=tk.constants.NW)

		self.figcanvas.get_tk_widget().config(width=winch*numaxes*dpi,height=hinch*dpi)

		self.canvas.itemconfigure(canwin,width=winch*numaxes*dpi,height=hinch*dpi)
		self.canvas.config(scrollregion=self.canvas.bbox(tk.constants.ALL),width=winch*dpi,height=winch*dpi)

		self.figure.canvas.draw()

		self.figure.set_tight_layout(True)

	def set_axes(self,numsubaxes=None):

		if numsubaxes is None:
			numsubaxes = (1,)*len(self.grids)

		self.axes = []

		for idaxis,(numsubaxis,grid) in enumerate(zip(numsubaxes,self.grids)):

			axisM = plt.subplot(grid)

			axisM.set_xticks([])

			axisM.grid(True,which="both",axis='y')

			for tic in axisM.yaxis.get_major_ticks():
				if idaxis>0:
					tic.label1.set_visible(False)
				tic.tick1line.set_visible(False)

			axisS = [axisM.twiny() for _ in range(numsubaxis)]

			for axis in axisS:
				axis.set_xticks([0,1])
				plt.setp(axis.xaxis.get_majorticklabels()[0],ha="left")
				plt.setp(axis.xaxis.get_majorticklabels()[-1],ha="right")

			self.axes.append(axisS)

	def set_axis(self,idaxis,idline,xvals,yvals):

		axis = self.axes[idaxis][idline]

		axis.plot(xvals,yvals,color=self.lineColors[idline])

		xticks = self.get_xticks(xvals)
		yticks = self.get_yticks(yvals)

		axis.set_xlim([xticks.min(),xticks.max()])
		axis.set_xticks(xticks)

		axis.set_ylim([yticks.max(),yticks.min()])
		axis.set_yticks(yticks)

		axis.grid(True,which="both",axis='y')

		axis.yaxis.set_minor_locator(AutoMinorLocator(10))

		if idaxis>0:
			for tic in axis.yaxis.get_minor_ticks():
				tic.tick1line.set_visible(False)

		if idline==0:
			axis.grid(True,which="major",axis='x')
		else:
			axis.spines["top"].set_position(("axes",self.spinepos[idline]))
			axis.spines["top"].set_color(self.lineColors[idline])
			axis.tick_params(axis='x',color=self.lineColors[idline],labelcolor=self.lineColors[idline])

		axis.xaxis.set_major_formatter(ScalarFormatter())
		# axis.xaxis.set_major_formatter(LogFormatter())

		majorTicksX = axis.xaxis.get_major_ticks()

		for tic in majorTicksX:
			tic.label2.set_visible(False)
			tic.tick2line.set_visible(False)

		majorTicksX[0].label2.set_visible(True)
		majorTicksX[0].tick2line.set_visible(True)

		majorTicksX[-1].label2.set_visible(True)
		majorTicksX[-1].tick2line.set_visible(True)

		plt.setp(axis.xaxis.get_majorticklabels()[0],ha="left")
		plt.setp(axis.xaxis.get_majorticklabels()[-1],ha="right")

	def get_xticks(self,xvals,xmin=None,xmax=None,xscale="normal",xdelta=None,xdelta_count=11):

		xvals_min = np.nanmin(xvals)

		if xvals_min is np.nan:
			xvals_min = 0.

		xvals_max = np.nanmax(xvals)

		if xvals_max is np.nan:
			xvals_max= 1.

		xrange_given = xvals_max-xvals_min

		if xdelta is None:
			xdelta = xrange_given/(xdelta_count-1)

		beforeDot,afterDot = format(xdelta,'f').split('.')

		nondim_xunit_sizes = np.array([1,2,4,5,10])

		if xdelta>1:

		    xdelta_temp = xdelta/10**(len(beforeDot)-1)
		    xdelta_temp = nondim_xunit_sizes[(np.abs(nondim_xunit_sizes-xdelta_temp)).argmin()]

		    xdelta = xdelta_temp*10**(len(beforeDot)-1)

		else:

		    zeroCountAfterDot = len(afterDot)-len(afterDot.lstrip('0'))

		    xdelta_temp = xdelta*10**(zeroCountAfterDot+1)
		    xdelta_temp = nondim_xunit_sizes[(np.abs(nondim_xunit_sizes-xdelta_temp)).argmin()]

		    xdelta = xdelta_temp/10**(zeroCountAfterDot+1)

		if xscale=="normal":

			if xmin is None:
				xmin = (np.floor(xvals_min/xdelta)-1).astype(float)*xdelta

			if xmax is None:
				xmax = (np.ceil(xvals_max/xdelta)+1).astype(float)*xdelta

			xticks = np.arange(xmin,xmax+xdelta/2,xdelta)

		elif xscale=="log":

			if xmin is None:
				xmin = xvals_min if xvals_min>0 else 0.001

			if xmax is None:
				xmax = xvals_max if xvals_max>0 else 0.1

			xmin_power = np.floor(np.log10(xmin))
			xmax_power = np.ceil(np.log10(xmax))

			xticks = 10**np.arange(xmin_power,xmax_power+1/2)

		return xticks

	def get_yticks(self,yvals=None,top=None,bottom=None):

		if top is None:
			top = yvals.min()

		if bottom is None:
			bottom = yvals.max()

		ymin = np.floor(top/20)*20

		ymax = np.ceil(bottom/20)*20

		yticks = np.arange(ymin,ymax+5,10)

		return yticks

	def _on_mousewheel(self,event):

		self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

if __name__ == "__main__":

	root = tk.Tk()

	las = LogView(root)

	las.set_image()

	# # Y = np.arange(500)
	# # X = np.random.random(500)

	# # las.set_figure(3)
	# # las.set_axes((1,2,1))
	# # las.set_axis(0,0,xvals=X,yvals=Y)
	# # las.set_axis(1,0,xvals=X,yvals=Y)
	# # las.set_axis(1,1,xvals=np.random.random(500),yvals=Y)

	# root.geometry("750x270")

	tk.mainloop()