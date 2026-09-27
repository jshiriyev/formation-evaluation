import matplotlib.pyplot as plt

from matplotlib import colors as mcolors

from matplotlib.patches import Polygon

import numpy as np

from scipy.ndimage import gaussian_filter

from _weaver import Weaver

print(plt.colormaps())

N = 40

np.random.seed(42)

x = np.random.rand(N+1)
y = np.arange(N+1)

smooth_x = gaussian_filter(x,sigma=1.5)

# z = plt.get_cmap('Reds')(smooth_x)

# print([c for c in dir(plt.cm)])

# z = z[:,:,np.newaxis].transpose((0,2,1))

fig = plt.figure()

ax = fig.subplots()

Weaver.fill_colormap(ax,y,smooth_x,1,colormap='Accent')

# im = ax.imshow(z,aspect='auto',extent=[0,1,0,40],origin='lower')

# # # # plt.scatter(x,y,c='k')
# # # # plt.plot(x,y,c='b')
# ax.plot(smooth_x,y,c='r')

# xy = np.column_stack([smooth_x,y])

# # xy = np.vstack([[0,0],xy,[0,40],[0,0]])
# xy = np.vstack([[1,0],xy,[1,40],[1,0]])

# clip = Polygon(xy,facecolor='none',edgecolor='none',closed=True)

# ax.add_patch(clip)

# im.set_clip_path(clip)

ax.set_xlim([0,1])
ax.set_ylim([40,0])

plt.show()

