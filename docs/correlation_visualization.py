from matplotlib.gridspec import GridSpec

import matplotlib.pyplot as plt

import numpy as np

from pphys.visualization import Formation, Correlation

depth1 = np.linspace(1000,3000,100)
depth2 = np.linspace(800,2800,100)
depth3 = np.linspace(800,2800,100)
depth4 = np.linspace(1000,3400,100)
depth5 = np.linspace(600,2800,100)

xvalues01 = np.random.rand(100)*100
xvalues02 = np.random.rand(100)*80
xvalues03 = np.random.rand(100)*120
xvalues04 = np.random.rand(100)*60+60
xvalues05 = np.random.rand(100)*100
xvalues06 = np.random.rand(100)*80
xvalues07 = np.random.rand(100)*120
xvalues08 = np.random.rand(100)*60+60
xvalues09 = np.random.rand(100)*100
xvalues10 = np.random.rand(100)*80

tops = Formation(**{
	"Bal X"  : (1500.,1000.,1250.,1275,1225),
	"Fasila" : (2000.,2000.,1500.,1475,1525),
	"NKP"    : (2750.,2500.,2250.,2225,2275),
	})

corr = Correlation(tops,figsize=(16,12))

corr.set(width_ratios=[2,42,2],height_ratios=[4,42],wspace=0.,hspace=0.)

corr = corr(5,xpad=0.05,ypad=0.1)

corr.add_curve(0,xvalues01,depth1,0.958,key="GR [API]",color="red")
corr.add_curve(0,xvalues02,depth1,0.978,key="Resistivity",color='#1f77b4')
corr.add_curve(1,xvalues03,depth2,0.958,key="GR [API]",color="red")
corr.add_curve(1,xvalues04,depth2,0.978,key="Resistivity",color="#1f77b4")
corr.add_curve(2,xvalues05,depth3,0.958,key="GR [API]",color="red")
corr.add_curve(2,xvalues06,depth3,0.978,key="Resistivity",color="#1f77b4")
corr.add_curve(3,xvalues07,depth4,0.958,key="GR [API]",color="red")
corr.add_curve(3,xvalues08,depth4,0.978,key="Resistivity",color="#1f77b4")
corr.add_curve(4,xvalues09,depth5,0.958,key="GR [API]",color="red")
corr.add_curve(4,xvalues10,depth5,0.978,key="Resistivity",color="#1f77b4")

corr.scene[0].set_xlim((-20,120))
corr.scene[1].set_xlim((-40,140))
corr.scene[2].set_xlim((-60,160))
corr.scene[3].set_xlim((-60,160))
corr.scene[4].set_xlim((-60,160))

corr.scene[0].fill_betweenx(depth1,xvalues01,50,where=xvalues01<50,interpolate=True,hatch='...',facecolor="#F4A460")

corr.add_top("Bal X",color='k',alpha=0.05)
corr.add_top("Fasila",color='k',alpha=0.05)
corr.add_top("NKP",color='k',alpha=0.05)

corr.add_formation("Bal X",alpha=0.05,color='#1f77b4')
corr.add_formation("Fasila",alpha=0.05,color='purple')

corr.scene.set_zorder()

corr.west.annotate("TVD",xy=(0.5,0.5),ha='center',va='center',fontweight='bold')

corr.head.annotate("GUN-031",xy=(corr.well(0),0.5),ha='center',va='center',)
corr.head.annotate("GUN-313",xy=(corr.well(1),0.5),ha='center',va='center',)
corr.head.annotate("GUN-601",xy=(corr.well(2),0.5),ha='center',va='center',)
corr.head.annotate("GUN-755",xy=(corr.well(3),0.5),ha='center',va='center',)
corr.head.annotate("GUN-999",xy=(corr.well(4),0.5),ha='center',va='center',)

corr.east.annotate("Lithology",xy=(0.5,0.5),ha='center',va='center',fontweight='bold',rotation=-90)

corr.add_distance(0)
corr.add_distance(1)
corr.add_distance(2)
corr.add_distance(3)

plt.tight_layout()

plt.show()