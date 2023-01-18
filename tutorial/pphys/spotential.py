import numpy

import _setup

from wlogs import spotential

## Exercise 1

sp1 = spotential(None,numpy.array([0,11000]))

sp1.set_temps(tempgrad=1,tempsurf=70)

Rw = sp1.get_formwaterres(SSP=-120,resmf=0.0676,resmf_temp=90,depth=11000)

print(sp1.get_temp(11000),Rw)

## Exercise 2

sp2 = spotential(None,numpy.array([0,4800]))

sp2.set_temps(tempmax=120,tempsurf=67)

RwA = sp2.get_formwaterres(SSP=-99,resmf=1.47,resmf_temp=74,depth=4555)
RwB = sp2.get_formwaterres(SSP=-103,resmf=1.47,resmf_temp=74,depth=4642)

print(sp2.get_temp(4555),RwA)
print(sp2.get_temp(4642),RwB)