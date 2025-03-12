import matplotlib.pyplot as plt

import numpy as np

from _section import CrossSection

depth1 = np.linspace(1000,3000,100)
depth2 = np.linspace(800,2800,100)
depth3 = np.linspace(800,2800,100)

xvalues1 = np.random.rand(100)*100
xvalues2 = np.random.rand(100)*80
xvalues3 = np.random.rand(100)*120

fig,(axis0,axis1,axis2) = plt.subplots(ncols=3,figsize=[12,12],width_ratios=[2,42,2],gridspec_kw=dict(wspace=0.,))

cs = CrossSection(**{
	"Bal X"  : (1500.,1000.,1250.),
	"Fasila" : (2000.,2000.,1500.),
	"NKP"    : (2750.,2500.,2250.),
	})

cs.set_axis(axis0)
cs.set_axis(axis1)
cs.set_axis(axis2)

cs = cs(axis1,3,xpad=0.1,ypad=0.1)

cs.main[0].plot(xvalues1,depth1)
cs.main[1].plot(xvalues2,depth2)
cs.main[2].plot(xvalues3,depth3)

cs.main[0].set_xlim((-20,120))
cs.main[1].set_xlim((-40,140))
cs.main[2].set_xlim((-60,160))

cs.main[0].set_xlabel("GR [API]")
cs.main[1].set_xlabel("GR [API]")
cs.main[2].set_xlabel("GR [API]")

cs.add_topline(0,side=axis2,color='k')
cs.add_topline(1,side=axis2,color='k')
cs.add_topline(2,side=axis2,color='k')

cs.add_formation(0,side=axis2,alpha=0.2,color='red')
cs.add_formation(1,side=axis2,alpha=0.2,color='purple')

cs.main.set_zorder()

plt.tight_layout()

plt.show()