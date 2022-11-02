import matplotlib.pyplot as plt

import dirsetup

from pphys import MNplot

plot = MNplot()

fig = plt.figure()

ax = fig.add_subplot(111)

plot.ternary(ax)

plt.show()