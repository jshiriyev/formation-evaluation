import io

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

class LogView():

	def __init__(self,root):

		self.root = root

		self.root.title("RockPy")

		self.root.iconbitmap('rockpy.ico')

		self.framelist = tk.Frame(root,width=31*8)
		self.framelist.pack(side=tk.LEFT,fill=tk.Y,expand=0)

		self.listbox = tk.Listbox(self.framelist,width=31)
		self.listbox.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

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

	def set_figure(self,numaxes=1,width=3,height=32,dpi=100.):

		self.figure = plt.figure(dpi=dpi)

		self.figure.set_figwidth(width*numaxes)
		self.figure.set_figheight(height)

		self.grids = gridspec.GridSpec(1,numaxes)
		self.grids.update(wspace=0)

		self.axes = []

		for idaxis,grid in enumerate(self.grids):

			axes = []

			axis = plt.subplot(grid)

			axis.set_xticks([])
			axis.set_yticks((0,1))

			axis.set_ylim((1,0))

			axis.spines["top"].set_visible(False)

			axis.grid(True,which="both",axis='y')

			plt.setp(axis.get_yticklines(),visible=False)
			# axis.tick_params(axis='y',which='major',length=0)

			if idaxis>0:
				plt.setp(axis.get_yticklabels(),visible=False)

			axes.append(axis)

			axsub = axis.twiny()

			axsub.set_xticks((0,1))

			axsub.set_ylim(axis.get_ylim())

			axsub.spines["left"].set_visible(False)
			axsub.spines["right"].set_visible(False)
			axsub.spines["bottom"].set_visible(False)

			plt.setp(axsub.xaxis.get_majorticklabels()[0],ha="left")
			plt.setp(axsub.xaxis.get_majorticklabels()[-1],ha="right")
			
			axes.append(axsub)

			self.axes.append(axes)

	def set_axis(self,idaxis=0,numsubaxis=2):

		if numsubaxis<2:
			return

		axis = self.axes[idaxis][0]

		colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

		for idline in range(1,numsubaxis+1):

			axsub = axis.twiny()

			if idline<numsubaxis:
				axsub.set_xticks((0,1))
				axsub.set_ylim(axis.get_ylim())

			spinepos = 1+0.4*idline/self.figure.get_figheight()

			axsub.spines["top"].set_position(("axes",spinepos))

			if idline<numsubaxis:
				axsub.spines["top"].set_color(colors[idline-1])

			if idline==numsubaxis:
				axsub.spines["top"].set_visible(False)

			axsub.spines["left"].set_visible(False)
			axsub.spines["right"].set_visible(False)
			axsub.spines["bottom"].set_visible(False)

			if idline==numsubaxis:
				plt.setp(axsub.get_xticklines(),visible=False)
				plt.setp(axsub.get_xticklabels(),color=self.figure.get_facecolor())

			if idline<numsubaxis:
				axsub.tick_params(axis='x',color=colors[idline-1],labelcolor=colors[idline-1])

				plt.setp(axsub.xaxis.get_majorticklabels()[0],ha="left")
				plt.setp(axsub.xaxis.get_majorticklabels()[-1],ha="right")

			if idline<numsubaxis:
				self.axes[idaxis].append(axsub)

	def set_subaxis(self,idaxis,idline,xvals,yvals):

		axis = self.axes[idaxis][idline]

		colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
		# colors = ("black","crimson","blue","sienna")

		zmult = int((500-0)/20.)

		spinepos = [1+x/zmult for x in (0,0.1,0.2,0.3)]

		axis.plot(xvals,yvals,color=colors[idline])

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

		if idline==0:
			axis.grid(True,which="major",axis='x')
		else:
			axis.spines["top"].set_position(("axes",spinepos[idline]))
			axis.spines["top"].set_color(colors[idline])
			axis.tick_params(axis='x',color=colors[idline],labelcolor=colors[idline])

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

	def set_image(self):

		self.figure.set_tight_layout(True)

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

	Y = np.arange(500)
	X = np.random.random(500)

	las.set_figure(2)
	las.set_axis(0,2)
	# las.set_axis(1,4)
	# las.set_subaxis(0,0,xvals=X,yvals=Y)
	# las.set_subaxis(1,0,xvals=X,yvals=Y)
	# las.set_subaxis(1,1,xvals=np.random.random(500),yvals=Y)

	las.set_image()

	# root.geometry("750x270")

	tk.mainloop()