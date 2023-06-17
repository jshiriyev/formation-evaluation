import numpy

import matplotlib.pyplot as plt

from borepy.wtest import agarwal1970
from borepy.wtest import everdingen1949
from borepy.wtest import finite

from borepy.scomp.finite import derive

tD = numpy.logspace(2,7,2000)
CD = 1000

pwD = agarwal1970.pressure(tD,CD,0)
pwDD = derive(pwD,tD)*tD

pwD_800 = everdingen1949.pressure_bounded(tD=tD,R=800,numterms=10)
pwDD_800 = derive(pwD_800,tD)*tD

sol = finite()

tD2 = numpy.logspace(0,7,2000)

pwD_800num = sol.pressure(tD2,CD,R=800)
pwDD_800num = derive(pwD_800num,tD2)*tD2

# print(sol.nodes)
# print(sol.radii)
# print(sol.deltar)
# print(sol.skin)

# for key,value in sol.transvec.items():
# 	print(key,value)

line1 = plt.loglog(tD/CD,pwD,label="R -> inf, CD = 1000")[0]
plt.loglog(tD/CD,pwDD,color=line1.get_color())

line2 = plt.loglog(tD2[500:]/CD,pwD_800num[500:],color='k',label="Finite Difference")[0]
plt.loglog(tD2[500:]/CD,pwDD_800num[500:],color=line2.get_color())

line3 = plt.loglog(tD/CD,pwD_800,label="R = 800, CD = 0")[0]
plt.loglog(tD/CD,pwDD_800,color=line3.get_color())

plt.xlabel("${t_D/C_D}$")

plt.ylabel("${p_D}$     ${(t_D/C_D)p_D'}$")

plt.legend()

plt.grid()

plt.tight_layout()

plt.show()
