import numpy

import dirsetup

from pphys import depthview

dv = depthview("lasfile.las")

dv.set_xaxis(0,subs=2)
dv.set_xaxis(2,subs=2)

dv.set_curve(0,'VSH',vmin=0,vmax=1)
dv.set_curve(2,'PHIE',vmin=0,vmax=0.5)
dv.set_curve(2,'PHIT',vmin=0,vmax=0.5)
dv.set_curve(3,'RL4')
dv.set_curve(3,'RL8')


"""
~ASCII       VSH     PHIE     PHIT       RL       SP    NGL (23.     LL   GR (23.0    SW      RL4      RL8     GR (17.0  NGL       VHD    BVW      CBW
 4010.00    0.183    0.219    0.285    7.013  -38.383    0.668    3.004    4.094    0.879    5.858    8.091    2.851    0.658    0.026    0.192    0.073 
"""


dv.view(4000)

print(dv.lasfile.curve)

print(dv.lasfile.well['STOP'].value)

# ls = loadlas("lasfile.las")

# # print(ls.homedir)
# # print(ls.filedir)
# # print(ls.well)

# frame = ls.depths(3782,3848)

# depths = frame['DEPT']

# dv = depthview()

# dv.set_axes(naxes=4,ncurves_max=3,label_loc="top")
# # dv.set_ycycles(7,1)

# dv.set_xcycles(0,cycles=2,subskip=2,scale='linear')
# # dv.set_xcycles(3,cycles=5,subskip=0,scale='log')
# # dv.set_ycycles(7,4)

# dv.add_depth(depths)

# class curve():

#     def __init__(self,
#         datacolumn,
#         linecolor="k",
#         linestyle="solid",
#         linewidth=0.75,
#         fill=False,
#         fillhatch='..',
#         fillfacecolor='gold'):

#         self.vals = datacolumn.vals
#         self.head = datacolumn.head
#         self.unit = datacolumn.unit
#         self.info = datacolumn.info
        
#         self.linecolor = linecolor
#         self.linestyle = linestyle
#         self.linewidth = linewidth

#         self.fill = fill
#         self.fillhatch = fillhatch
#         self.fillfacecolor = fillfacecolor

# dv.add_curve(0,curve(frame['VSH']))
# dv.add_curve(2,curve(frame['PHIE']))
# dv.add_curve(2,curve(frame['PHIT'],linestyle="dashed"),vmin=0)
# dv.add_curve(2,curve(frame['NGL230986'],linestyle="dotted"))
# dv.add_curve(3,curve(frame['bvw']))
# dv.add_curve(3,curve(frame['CBW'],linestyle="dashed"))
# dv.add_curve(4,curve(frame['RL4']))
# dv.add_curve(4,curve(frame['RL8'],linestyle="dashed"))

# dv.show() #"sample.pdf"