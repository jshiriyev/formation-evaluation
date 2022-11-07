import matplotlib.pyplot as plt

import dirsetup

from pphys import colors

cols = colors()

fig = plt.figure(figsize=(8,5))

axis = fig.add_subplot(111)

fig.subplots_adjust(left=0,right=1,top=1,bottom=0,hspace=0,wspace=0)

cols.view(axis)

plt.show()