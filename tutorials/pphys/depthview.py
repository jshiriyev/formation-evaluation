import numpy

import dirsetup

from matplotlib import pyplot

from pphys import depthview

dv = depthview("lasfile.las")

dv.set_curve(0,'VSH',vmin=0,vmax=1,width=0.5,color='red')
dv.set_curve(2,'PHIE',vmin=0,vmax=0.6)
dv.set_curve(2,'PHIT',vmin=0,vmax=0.6,style="dashed")
dv.set_curve(3,'RL4')
dv.set_curve(3,'RL8',style="dashed")

dv.set_xaxis(0,cycles=3,subs=2)
dv.set_xaxis(2,cycles=2,subs=2)
dv.set_xaxis(3,cycles=3,subskip=0,scale='log')

"""
~ASCII       VSH     PHIE     PHIT       RL       SP    NGL (23.     LL   GR (23.0    SW      RL4      RL8     GR (17.0  NGL       VHD    BVW      CBW
 4010.00    0.183    0.219    0.285    7.013  -38.383    0.668    3.004    4.094    0.879    5.858    8.091    2.851    0.658    0.026    0.192    0.073 
"""

dv.view(4000)

# print(dv.lasfile.curve)

# print(dv.lasfile.well['STOP'].value)

# ls = loadlas("lasfile.las")

# # print(ls.homedir)
# # print(ls.filedir)
# # print(ls.well)

# frame = ls.depths(3782,3848)

# depths = frame['DEPT']