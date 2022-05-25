import tkinter as tk

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

class LogView():

	def __init__(self,root):

		self.frame = tk.Frame(root)
		self.frame.pack(side=tk.TOP,fill=tk.BOTH,expand=1)

		self.figure = plt.figure(figsize=(4,64))

		axes_num = 1

		self.grids = gridspec.GridSpec(1,axes_num)
		self.grids.update(wspace=0)

		axis0 = plt.subplot(self.grids[0])

		axis0.set_xticks([])

		axis0.grid(True,which="both",axis='y')

		axis = axis0.twiny()



		xaxis = np.random.random(500)
		xaxis[-10:] = 0.5
		yaxis = np.arange(500)

		xticks = self.get_xticks(xaxis)
		yticks = self.get_yticks(yaxis)

		axis.plot(xaxis,yaxis)
		##axis.figure.set_size_inches(4,400)

		axis.set_xlim([xticks.min(),xticks.max()])
		axis.set_xticks(xticks)

		axis.set_ylim([yticks.max(),yticks.min()])
		axis.set_yticks(yticks)

		axis.grid(True,which="major",axis='x')
		axis.grid(True,which="both",axis='y')

		axis.yaxis.set_minor_locator(AutoMinorLocator(10))

		# if axdict["ptype"][indexJ] is None:
		axis.xaxis.set_major_formatter(ScalarFormatter())
		# elif axdict["ptype"][indexJ]=="log":
		# 	self.axes[indexI].subax[indexJ].xaxis.set_major_formatter(LogFormatter())

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






		self.canvas = tk.Canvas(self.frame)
		self.canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

		scrollbar = tk.Scrollbar(self.frame) #,orient=tk.VERTICAL
		scrollbar.pack(side=tk.LEFT,fill=tk.Y)

		self.canvas.config(yscrollcommand=scrollbar.set)
		scrollbar.config(command=self.canvas.yview)

		self.canvas.bind_all("<MouseWheel>",self._on_mousewheel)

		figagg = FigureCanvasTkAgg(self.figure,self.canvas)
		canagg = figagg.get_tk_widget()

		##figagg.get_tk_widget().config(width=400,height=1600)
		##figagg.get_tk_widget().config(bg="blue",scrollregion=(0,0,400,1600))
		##figagg.get_tk_widget().config(yscrollcommand=scrollbar.set)
		##figagg.get_tk_widget().pack(side=tk.LEFT,fill=tk.BOTH,expand=tk.Y)

		canwin = self.canvas.create_window(0,0,window=canagg,anchor=tk.constants.NW)

		wi,hi = [i*self.figure.dpi for i in self.figure.get_size_inches()]

		canagg.config(width=wi,height=hi)

		self.canvas.itemconfigure(canwin,width=wi,height=hi)
		self.canvas.config(scrollregion=self.canvas.bbox(tk.constants.ALL),width=400,height=400)

		self.figure.canvas.draw()

		self.figure.set_tight_layout(True)

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

	tk.mainloop()