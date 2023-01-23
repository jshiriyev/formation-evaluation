import matplotlib.pyplot as plt

import numpy

import _setup

from mesh import rectangle

rect = rectangle(5,3)

rect.set_grid((5,3))

print(rect.grid.volume)

rect.plot()

# plt.plot(*rect.vertices[rect.indices].T)

# plt.show()