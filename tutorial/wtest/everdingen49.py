import numpy

import matplotlib.pyplot as plt

from borepy.wtest import agarwal1970
from borepy.wtest import everdingen1949

tD1 = numpy.logspace(2,7,2000)

pwD = agarwal1970.pressure(tD1,1000,0)

tD = numpy.logspace(5,7,2000)

# pwD_infinite = everdingen1949.pressure(tD)

pwD_80 = everdingen1949.pressure_bounded(tD=tD,R=80,numterms=10)
pwD_100 = everdingen1949.pressure_bounded(tD=tD,R=100,numterms=10)
pwD_200 = everdingen1949.pressure_bounded(tD=tD,R=200,numterms=10)
pwD_300 = everdingen1949.pressure_bounded(tD=tD,R=300,numterms=10)
pwD_400 = everdingen1949.pressure_bounded(tD=tD,R=400,numterms=10)
pwD_500 = everdingen1949.pressure_bounded(tD=tD,R=500,numterms=10)
pwD_600 = everdingen1949.pressure_bounded(tD=tD,R=600,numterms=10)
pwD_800 = everdingen1949.pressure_bounded(tD=tD,R=800,numterms=10)
pwD_1500 = everdingen1949.pressure_bounded(tD=tD,R=1500,numterms=10)

plt.loglog(tD1,pwD,label="R infinite, CD = 1000")
# plt.loglog(tD1,pwD_infinite,label="R infinite")
plt.loglog(tD,pwD_1500,label="R = 1500")
plt.loglog(tD,pwD_800,label="R = 800")
plt.loglog(tD,pwD_600,label="R = 600")
plt.loglog(tD,pwD_500,label="R = 500")

plt.legend()

plt.grid()

plt.show()