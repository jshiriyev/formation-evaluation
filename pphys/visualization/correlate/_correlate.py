import matplotlib.pyplot as plt

import numpy as np

# from _layout import Layout,
from _booter import Booter

main = Booter(3,xpad=0.1,ypad=0.1)

depth1 = np.linspace(1000,3000,100)
depth2 = np.linspace(800,2800,100)
depth3 = np.linspace(800,2800,100)

xvalues1 = np.random.rand(100)*100
xvalues2 = np.random.rand(100)*80
xvalues3 = np.random.rand(100)*120

fig,(depth,master,lithology) = plt.subplots(ncols=3,figsize=[12,12],width_ratios=[2,42,2],gridspec_kw=dict(wspace=0.,))

depth.set_xlim((0,1))
depth.set_ylim((0,1))
depth.set_xticks([])
depth.set_yticks([])

lithology.set_xlim((0,1))
lithology.set_ylim((0,1))
# lithology.yaxis.set_label_position('right')
# lithology.yaxis.set_ticks_position('right')
lithology.set_xticks([])
lithology.set_yticks([])

axin1 = main.get(master,0)
axin2 = main.get(master,1)
axin3 = main.get(master,2)

axin1.plot(xvalues1,depth1)
axin2.plot(xvalues2,depth2)
axin3.plot(xvalues3,depth3)

axin1.set_xlim((-20,120))
axin2.set_xlim((-40,140))
axin3.set_xlim((-60,160))

axin1.set_xlabel("GR [API]")
axin2.set_xlabel("GR [API]")
axin3.set_xlabel("GR [API]")

x1,y1 = main.tops((axin1,axin2,axin3),(1500.,1000.,1250.))
x2,y2 = main.tops((axin1,axin2,axin3),(2000.,2000.,1500.))
x3,y3 = main.tops((axin1,axin2,axin3),(2750.,2500.,2250.))

master.fill_between(x1,y1=y1,y2=y2,alpha=0.2,color='red')
lithology.fill_between([0,1],y1=y1[-2:],y2=y2[-2:],alpha=0.2,color='red')
lithology.text(0.5,(y1[-1]+y2[-1])/2,"BAL X",va="center",ha="center",rotation=-90,fontsize="large",fontweight="bold")

master.fill_between(x2,y1=y2,y2=y3,alpha=0.2,color='purple')
lithology.fill_between([0,1],y1=y2[-2:],y2=y3[-2:],alpha=0.2,color='purple')
lithology.text(0.5,(y2[-1]+y3[-1])/2,"Fasila",va="center",ha="center",rotation=-90,fontsize="large",fontweight="bold")

master.set_xlim([0.,1.])
master.set_ylim([0.,1.])

master.set_xticks([])
master.set_yticks([])

master.set_zorder(1)

axin1.set_zorder(-1)
axin2.set_zorder(-1)
axin3.set_zorder(-1)

plt.tight_layout()

plt.show()