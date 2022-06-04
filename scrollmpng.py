import io

import logging

import os

import tkinter as tk

from matplotlib import gridspec
from matplotlib import pyplot as plt

# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import LogFormatter
from matplotlib.ticker import LogFormatterExponent
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.ticker import NullLocator
from matplotlib.ticker import ScalarFormatter

import numpy as np

from PIL import ImageTk, Image

if __name__ == "__main__":
    import setup

from textio import LogASCII

"""
1. DepthView should be a frame that can be added to any parent frame.
2. Axis and line numbers should not be predefined.
3. Adding axis should not affect previous axes.
4. Adding line should not affect previous lines.
5. DepthView should be added to graphics and inherit from the textio.
6. Depth axis must be unique!
7. x-axis grids must be the same for the axis on top of each other.
8. get_xticks() should be working perfectly for both normal and logarithmic scale
"""

class DepthView(LogASCII):

	def __init__(self,root,**kwargs):
		"""It initializes the DepthView with listbox and figure canvas."""

		super().__init__(**kwargs)

		self.root = root

		self.root.title("RockPy")

		icopath = os.path.join(os.path.dirname(__file__),"rockpy.ico")

		self.root.iconbitmap(icopath)

		# The main frame for the listbox

		self.framelist = tk.Frame(root,width=31*8)
		self.framelist.pack(side=tk.LEFT,fill=tk.Y,expand=0)

		self.listbox = tk.Listbox(self.framelist,width=31)
		self.listbox.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

		# The main frame for the plot canvas

		self.framefigs = tk.Frame(root)
		self.framefigs.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

		self.canvas = tk.Canvas(self.framefigs)

		self.canvas.grid(row=0,column=0,sticky=tk.NSEW)

		self.hscroll = tk.Scrollbar(self.framefigs,orient=tk.HORIZONTAL)
		self.vscroll = tk.Scrollbar(self.framefigs,orient=tk.VERTICAL)

		self.hscroll.grid(row=1,column=0,sticky=tk.EW)
		self.vscroll.grid(row=0,column=1,sticky=tk.NS)

		self.framefigs.rowconfigure(0,weight=1)
		self.framefigs.columnconfigure(0,weight=1)

		self.canvas.config(xscrollcommand=self.hscroll.set)
		self.canvas.config(yscrollcommand=self.vscroll.set)

		self.hscroll.config(command=self.canvas.xview)
		self.vscroll.config(command=self.canvas.yview)

		self.canvas.bind_all("<MouseWheel>",self._on_mousewheel)

		# The colors to be used for lines

		# self.colors = ("black","crimson","blue","sienna")
		self.colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
		self.colors.insert(0,"#000000")

	def set_axes(self,numaxes=1,subaxes=None,depth=None,inchdepth=15.,width=3.,height=32.,dpi=100.):
		"""Creates the figure and axes and their sub-axes and stores them in the self.axes."""

		# numaxes 	: integer
		# 			 Number of axes in the figure

		# subaxes 	: list or tuple of integers
		# 			 Number of subaxes in each axis

		# depth 	: float
		# 			 Depth of log in meters; every inch will represent inchdepth meter of formation
		# 			 Default value for inchdepth is 15 meters.

		# inchdepth	: float
		# 			 The depth (meters) to be shown in every inch of the figure

		# width 	: float
		# 			 Width of each axis in inches

		# height 	: float
		# 			 Height of figure in inches

		# dpi 		: integer
		# 			 Resolution of the figure, dots per inches

		self.figure = plt.figure(dpi=dpi)

		self.figure.set_figwidth(width*numaxes)

		if depth is None:
			self.figure.set_figheight(height)
		else:
			self.figure.set_figheight(depth/inchdepth)

		self.fgspec = gridspec.GridSpec(1,numaxes)

		self.axes = []

		if subaxes is None:
			subaxes = (1,)*numaxes
		elif not hasattr(subaxes,"__len__"):
			logging.warning(f"Expected subaxes is a list or tuple with the length equal to numaxes; input is {type(subaxes)}")
		elif len(subaxes)!=numaxes:
			logging.warning(f"The length of subaxes should be equal to numaxes; {len(subaxes)} not equal to {numaxes=}")

		for idaxis in range(numaxes):
			self.add_axis(idaxis,subaxes[idaxis])

	def add_axis(self,idaxis,numsubaxes=1):
		"""Adds main-axis and its subaxes to the list of self.axes."""

		subaxes = []

		subaxis_main = plt.subplot(self.fgspec[idaxis])

		subaxis_main.set_xticks([])
		subaxis_main.set_yticks((0,1))

		subaxis_main.set_ylim((1,0))

		subaxis_main.grid(True,which="both",axis='y')

		plt.setp(subaxis_main.get_yticklines(),visible=False)
		# subaxis_main.tick_params(axis='y',which='major',length=0)

		if idaxis>0:
			plt.setp(subaxis_main.get_yticklabels(),visible=False)

		subaxes.append(subaxis_main)

		self.axes.append(subaxes)

		self.set_subaxes(idaxis,numsubaxes)

	def set_subaxes(self,idaxis,numsubaxes):
		"""Creates subaxes and stores them in self.axes."""

		roofpos = 1+0.4*numsubaxes/self.figure.get_figheight()

		self.axes[idaxis][0].spines["top"].set_position(("axes",roofpos))

		for idline in range(numsubaxes):
			self.add_subaxis(idaxis,idline)

	def add_subaxis(self,idaxis,idline):
		"""Adds subaxis to the self.axes."""

		axsub = self.axes[idaxis][0].twiny()

		axsub.set_xticks((0,1))
		axsub.set_ylim(self.axes[0][0].get_ylim())

		spinepos = 1+0.4*idline/self.figure.get_figheight()

		axsub.spines["top"].set_position(("axes",spinepos))
		axsub.spines["top"].set_color(self.colors[idline])

		axsub.spines["left"].set_visible(False)
		axsub.spines["right"].set_visible(False)
		axsub.spines["bottom"].set_visible(False)

		axsub.tick_params(axis='x',labelcolor=self.colors[idline])

		plt.setp(axsub.xaxis.get_majorticklabels()[0],ha="left")
		plt.setp(axsub.xaxis.get_majorticklabels()[-1],ha="right")

		plt.setp(axsub.xaxis.get_majorticklines()[1],markersize=25)
		plt.setp(axsub.xaxis.get_majorticklines()[-1],markersize=25)

		# axsub.xaxis.get_majorticklines()[0].set_markersize(100)

		self.axes[idaxis].append(axsub)

	def set_lines(self,idaxis,idline,xvals,yvals):

		axis = self.axes[idaxis][idline]
		
		# zmult = int((500-0)/20.)

		# spinepos = [1+x/zmult for x in (0,0.1,0.2,0.3)]

		axis.plot(xvals,yvals,color=self.colors[idline])

		xticks = self.get_xticks(xvals)
		yticks = self.get_yticks(yvals)

		figheight_temp = (yticks.max()-yticks.min())/128

		if figheight_temp>self.figure.get_figheight():
			self.figure.set_figheight(figheight_temp)

		# figheight = max(self.figure.get_figheight(),figheight_temp)

		axis.set_xlim([xticks.min(),xticks.max()])
		axis.set_xticks(xticks)

		axis.set_ylim([yticks.max(),yticks.min()])
		axis.set_yticks(yticks)

		axis.grid(True,which="both",axis='y')

		axis.yaxis.set_minor_locator(AutoMinorLocator(10))

		if idaxis>0:
			for tic in axis.yaxis.get_minor_ticks():
				tic.tick1line.set_visible(False)

			# plt.setp(axis.yaxis.get_yticklabels(),visible=False)

		if idline==0:
			axis.grid(True,which="major",axis='x')
		else:
			axis.spines["top"].set_position(("axes",spinepos[idline]))
			axis.spines["top"].set_color(self.colors[idline])
			axis.tick_params(axis='x',color=self.colors[idline],labelcolor=self.colors[idline])

		axis.xaxis.set_major_formatter(ScalarFormatter())
		# axis.xaxis.set_major_formatter(LogFormatter())

		majorTicksX = axis.xaxis.get_major_ticks()

		for tic in majorTicksX:
			tic.label2.set_visible(False)
			tic.tick2line.set_visible(False)
		# plt.setp(majorTicksX,visible=False)

		majorTicksX[0].label2.set_visible(True)
		majorTicksX[0].tick2line.set_visible(True)

		majorTicksX[-1].label2.set_visible(True)
		majorTicksX[-1].tick2line.set_visible(True)

		plt.setp(axis.xaxis.get_majorticklabels()[0],ha="left")
		plt.setp(axis.xaxis.get_majorticklabels()[-1],ha="right")

	def set_image(self):
		"""Creates the image of figure in memory and displays it on canvas."""

		self.fgspec.tight_layout(self.figure,rect=[0,0,1.0,0.99])
		self.fgspec.update(wspace=0)

		buff = io.BytesIO()

		self.figure.savefig(buff,format='png')

		buff.seek(0)

		self.image = ImageTk.PhotoImage(Image.open(buff))

		self.canvas.create_image(0,0,anchor=tk.NW,image=self.image)

		self.canvas.config(scrollregion=self.canvas.bbox('all'))

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

	def get_yticks(self,yvals=None,top=None,bottom=None,endmultiple=20.,ydelta=10.):

		if yvals is None:
			yvals = np.array([0,1])

		if top is None:
			top = np.nanmin(yvals)

		if bottom is None:
			bottom = np.nanmax(yvals)

		if top>bottom:
			top,bottom = bottom,top

		ymin = np.floor(top/endmultiple)*endmultiple

		ymax = np.ceil(bottom/endmultiple)*endmultiple

		yticks = np.arange(ymin,ymax+ydelta/2,ydelta)

		return yticks

	def _on_mousewheel(self,event):
		"""Lets the scroll work everywhere on the window."""

		self.canvas.yview_scroll(int(-1*(event.delta/120)),"units")

if __name__ == "__main__":

	root = tk.Tk()

	las = DepthView(root)

	Y = np.arange(500)
	X = np.random.random(500)

	las.set_axes(3)
	las.set_subaxes(0,3)
	las.set_subaxes(1,3)
	# las.set_lines(0,0,xvals=X,yvals=Y)
	# las.set_lines(1,0,xvals=X,yvals=Y)
	# las.set_lines(1,1,xvals=np.random.random(500),yvals=Y)

	las.set_image()

	# root.geometry("750x270")

	tk.mainloop()