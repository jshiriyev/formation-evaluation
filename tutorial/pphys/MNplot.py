import matplotlib.pyplot as plt

import numpy

import _setup

from pphys import mnplot

plot = mnplot()

fig = plt.figure()

ax = fig.add_subplot(111)

ax = plot.lithonodes(ax)

ax,nodes = plot.ternary(ax,lith1="SS1",lith2="LS1",lith3="DOL2",num=5)

print(nodes)

plt.show()