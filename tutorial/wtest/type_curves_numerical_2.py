import numpy

import matplotlib.pyplot as plt

from borepy.wtest import agarwal
from borepy.wtest import everdingen
from borepy.wtest import finite

from borepy.scomp.finite import derive

sol = finite(1000,rskin=5,alpha=7,Nimpaired=4,Nunharmed=4)

print(sol.radii_grid)
print(sol.radii_node)

print(sol.alpha_grid)

print(sol.skin)

print(sol.size)

print(sol.nodealpha())

plt.vlines(sol.radii_node,-0.5,0.5)
plt.scatter(sol.radii_grid,numpy.zeros(sol.radii_grid.size))

plt.xscale("log")

plt.ylim((-10,10))

plt.show()
