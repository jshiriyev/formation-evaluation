import numpy

import matplotlib.pyplot as plt

from borepy.wtest import agarwal1970
from borepy.wtest import everdingen1949
from borepy.wtest import finite

from borepy.scomp.finite import derive

tD = numpy.logspace(2,7,2000)
CD = 1000

pwD = agarwal1970.pressure(tD,CD,0)
# pwDD = derive(pwD,tD)*tD

pwD_800 = everdingen1949.pressure_bounded(tD=tD,R=800,numterms=10)

sol = finite(R=800,deltat=100,nsteps=10000,ngrids2=200)

# print(sol.nodes)
# print(sol.radii)
# print(sol.deltar)
# print(sol.skin)

# for key,value in sol.transvec.items():
# 	print(key,value)

line1 = plt.loglog(tD/CD,pwD,label="R -> inf, CD = 1000")[0]
# plt.loglog(tD/CD,pwDD,color=line1.get_color())

line2 = plt.scatter(sol.times/CD,sol.pressure(CD),s=1)

line3 = plt.loglog(tD/CD,pwD_800,label="R = 800, CD = 0")[0]
# plt.loglog(tD/CD,pwDD_800,color=line3.get_color())

plt.xlabel("${t_D/C_D}$")

plt.ylabel("${p_D}$     ${(t_D/C_D)p_D'}$")

plt.legend()

plt.grid()

plt.tight_layout()

plt.show()
