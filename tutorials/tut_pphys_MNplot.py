import matplotlib.pyplot as plt

import numpy

import dirsetup

from pphys import MNplot

plot = MNplot()

fig = plt.figure()

ax = fig.add_subplot(111)

ax = plot.lithNodes(ax)

ax,nodes = plot.ternary(ax,lith1="SS1",lith2="LS1",lith3="DOL2",num=5)

print(nodes)

plt.show()