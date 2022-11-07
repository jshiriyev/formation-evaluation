import matplotlib.pyplot as plt

import numpy

import dirsetup

from pphys import denneu

plot = denneu()

fig = plt.figure(figsize=(7,8))

ax = fig.add_subplot(111)

ax = plot.lithonodes(ax)
ax = plot.litholines(ax)

# fig.tight_layout()

plt.show()