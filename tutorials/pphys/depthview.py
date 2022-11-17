import numpy

import dirsetup

from pphys import loadlas

from pphys import depthview

ls = loadlas("lasfile.las")

# print(ls.homedir)
# print(ls.filedir)
# print(ls.well)

frame = ls.depths(3782,3848)

depths = frame['DEPT']

dv = depthview()

dv.set_axes(naxes=4,ncurves_max=3,label_loc="top")
# dv.set_ycycles(7,1)

dv.set_xcycles(0,cycles=2,subskip=0,scale='linear')
# dv.set_xcycles(3,cycles=5,subskip=0,scale='log')
# dv.set_ycycles(7,4)

dv.add_depth(depths)

class curve():

    def __init__(self,
        datacolumn,
        linecolor="k",
        linestyle="solid",
        linewidth=0.75,
        fill=False,
        fillhatch='..',
        fillfacecolor='gold'):

        self.vals = datacolumn.vals
        self.head = datacolumn.head
        self.unit = datacolumn.unit
        self.info = datacolumn.info
        
        self.linecolor = linecolor
        self.linestyle = linestyle
        self.linewidth = linewidth

        self.fill = fill
        self.fillhatch = fillhatch
        self.fillfacecolor = fillfacecolor

dv.add_curve(0,curve(frame['VSH']))
dv.add_curve(2,curve(frame['PHIE']))
dv.add_curve(2,curve(frame['PHIT'],linestyle="dashed"))
dv.add_curve(2,curve(frame['NGL230986'],linestyle="dotted"))
dv.add_curve(3,curve(frame['bvw']))
dv.add_curve(3,curve(frame['CBW'],linestyle="dashed"))
dv.add_curve(4,curve(frame['RL4']))
dv.add_curve(4,curve(frame['RL8'],linestyle="dashed"))

dv.show() #"sample.pdf"