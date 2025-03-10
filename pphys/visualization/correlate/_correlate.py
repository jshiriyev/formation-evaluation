import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import numpy as np

depth1 = np.linspace(1000,3000,100)
depth2 = np.linspace(800,2800,100)

xvalues1 = np.random.rand(100)*100
xvalues2 = np.random.rand(100)*80

fig,ax = plt.subplots(figsize=[10,12])

axin1 = ax.inset_axes([0.1,0.1,0.35,0.8])
axin2 = ax.inset_axes([0.6,0.1,0.35,0.8])

axin1.plot(xvalues1,depth1)
axin2.plot(xvalues2,depth2)

axin1.yaxis.set_inverted(True)
axin2.yaxis.set_inverted(True)

axin1.set_xlim((-20,120))
axin2.set_xlim((-40,140))

# ax.set_xticks([])
# ax.set_yticks([])

# ax.hlines(0.5,-0.2,1.2)

ax.fill_between([0.,0.45,0.6,1.],[0.5,0.5,0.45,0.45],y2=[0.7,0.7,0.8,0.8],alpha=0.2,color='red')

ax.set_xlim([0.,1.])
ax.set_ylim([0.,1.])

ax.set_zorder(1)

axin1.set_zorder(-1)
axin2.set_zorder(-1)

plt.tight_layout()

plt.show()