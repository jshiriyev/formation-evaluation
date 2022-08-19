import tkinter

import numpy

import setup

from dataview import DepthView

root = tkinter.Tk()

las = DepthView(root)

Y = numpy.arange(5000)*0.1
X = numpy.random.random(5000)/5

las.set_axes(2)
las.set_subaxes(0,3)
las.set_subaxes(1,3)
# las.set_subaxes(2,3)
las.set_lines(0,0,xvals=X,yvals=Y)
# las.set_lines(1,0,xvals=X,yvals=Y)
# las.set_lines(1,1,xvals=numpy.random.random(500),yvals=Y)

las.set_image()

# root.geometry("750x270")

tkinter.mainloop()
	
