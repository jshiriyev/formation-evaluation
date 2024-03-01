import matplotlib.pyplot as plt

import numpy as np

import lasio as ls

from _depthview import DepthView

lasfile = ls.read('_testing.las')

# print(ls.LASFile)
# print(ls.SectionItems)
# print(ls.HeaderItem)
# print(ls.CurveItem,end="\n\n")

# print(type(lasfile.version))
# print(type(lasfile.well))
# print(type(lasfile.params))
# print(type(lasfile.curves),end="\n\n")

# print(lasfile.curves)


# # print(plt.rcParams.keys())

plt.rcParams['hatch.color'] = 'white'

moduleUranium = {}

moduleUranium['fillcolor'] = "silver"
moduleUranium['hatch'] = ".."
moduleUranium['detail'] = 'Area Fill 1'

dv = DepthView(lasfile)

dv.set_depths(lasfile.index[0],lasfile.index[-1])

dv.set_curve(0,'GR-TOT',vmin=0,vmax=100)
dv.set_curve(0,'GR-KT',vmin=0,vmax=100,style='--')
dv.set_module(0,moduleUranium,left=0,right=1,row=2)

dv.set_curve(2,'DEL-T',vmin=140,vmax=40)
# dv.set_curve(2,'TNHP',vmin=45,vmax=-15,style='--')
# dv.set_module(2,moduleSS,left=1,right=0,row=3)

dv.set_curve(3,'DEN',vmin=1.95,vmax=2.95)
dv.set_curve(3,'NEU',vmin=0.45,vmax=-0.15,style='--')

# dv.set_axes(nrows=4)

dv.set_xaxis(0,subs=2)
dv.set_xaxis(2,cycles=2,subs=2)
dv.set_xaxis(3,cycles=4,subs=2)
# dv.set_xaxis(4,scale='log')
# dv.set_xaxis(5,cycles=1,subs=2)
# dv.set_xaxis(6,cycles=1,subs=1)
# dv.set_xaxis(7,cycles=4,scale='log')

dv.view(1285,height=55)