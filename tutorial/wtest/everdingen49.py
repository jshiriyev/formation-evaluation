import numpy

import matplotlib.pyplot as plt

from borepy.wtest import agarwal1970
from borepy.wtest import everdingen1949

from borepy.scomp.finite import derive

tD = numpy.logspace(2,7,2000)

pwD = agarwal1970.pressure(tD,1000,0)
pwDD = derive(pwD,tD)*1000

# pwD_infinite = everdingen1949.pressure(tD)

pwD_80 = everdingen1949.pressure_bounded(tD=tD,R=80,numterms=10)
pwDD_80 = derive(pwD_80,tD)*1000

pwD_100 = everdingen1949.pressure_bounded(tD=tD,R=100,numterms=10)
pwDD_100 = derive(pwD_100,tD)*1000

pwD_200 = everdingen1949.pressure_bounded(tD=tD,R=200,numterms=10)
pwDD_200 = derive(pwD_200,tD)*1000

pwD_300 = everdingen1949.pressure_bounded(tD=tD,R=300,numterms=10)
pwDD_300 = derive(pwD_300,tD)*1000

pwD_400 = everdingen1949.pressure_bounded(tD=tD,R=400,numterms=10)
pwDD_400 = derive(pwD_400,tD)*1000

pwD_500 = everdingen1949.pressure_bounded(tD=tD,R=500,numterms=10)
pwDD_500 = derive(pwD_500,tD)*1000

pwD_600 = everdingen1949.pressure_bounded(tD=tD,R=600,numterms=10)
pwDD_600 = derive(pwD_600,tD)*1000

pwD_800 = everdingen1949.pressure_bounded(tD=tD,R=800,numterms=10)
pwDD_800 = derive(pwD_800,tD)*1000

pwD_1500 = everdingen1949.pressure_bounded(tD=tD,R=1500,numterms=10)
pwDD_1500 = derive(pwD_1500,tD)*1000

line1 = plt.loglog(tD,pwD,label="R -> inf, CD = 1000")[0]
plt.loglog(tD,pwDD,color=line1.get_color())

# plt.loglog(tD,pwD_infinite,label="R infinite")
line2 = plt.loglog(tD,pwD_1500,label="R = 1500, CD = 0")[0]
plt.loglog(tD,pwDD_1500,color=line2.get_color())

line3 = plt.loglog(tD,pwD_800,label="R = 800, CD = 0")[0]
plt.loglog(tD,pwDD_800,color=line3.get_color())

line4 = plt.loglog(tD,pwD_600,label="R = 600, CD = 0")[0]
plt.loglog(tD,pwDD_600,color=line4.get_color())

line5 = plt.loglog(tD,pwD_500,label="R = 500, CD = 0")[0]
plt.loglog(tD,pwDD_500,color=line5.get_color())

plt.legend()

plt.grid()

plt.tight_layout()

plt.show()