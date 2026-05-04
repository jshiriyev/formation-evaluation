import matplotlib.pyplot as plt

import numpy as np

import sys

sys.path.append(r'C:\\Users\\3876yl\\Documents\\gmodel')

from utils._spatial import Spatial

from gmodel.gstats._variogram import Variogram as var
from gmodel.gstats._variogram import Experimental
from gmodel.gstats._variogram import Theoretical

TOC = np.ndarray((8,8))

TOC[:,0] = np.array([15,13,11,10,17,16,15,11])
TOC[:,1] = np.array([17,14,10,13,13,15,14,17])
TOC[:,2] = np.array([18,16,10,16,14,18,20,18])
TOC[:,3] = np.array([19,18,15,15,18,23,22,20])
TOC[:,4] = np.array([21,15,20,18,20,20,18,13])
TOC[:,5] = np.array([22,17,18,19,18,25,20,19])
TOC[:,6] = np.array([23,20,17,20,14,23,21,17])
TOC[:,7] = np.array([26,22,19,14,16,19,16,14])

x = np.array([1,2,3,4,5,6,7,8])
y = np.array([1,2,3,4,5,6,7,8])

yaxis = np.repeat(y,8)
xaxis = np.tile(x,8)

data = Spatial(TOC.T.flatten(),xaxis,yaxis)

exp1 = Experimental(1,0.5,4,0,1,1)
exp2 = Experimental(1,0.5,4,90,1,1)
exp3 = Experimental(np.sqrt(2),np.sqrt(2)/2,np.sqrt(2)*4,45,5,0.1)
exp4 = Experimental(np.sqrt(2),np.sqrt(2)/2,np.sqrt(2)*4,135,5,0.1)

gamma1,bins1 = var.experimental(data,exp1)
gamma2,bins2 = var.experimental(data,exp2)
gamma3,bins3 = var.experimental(data,exp3)
gamma4,bins4 = var.experimental(data,exp4)

plt.plot(bins1,gamma1,label="E-W")
plt.scatter(bins1,gamma1)

plt.plot(bins2,gamma2,label="N-S")
plt.scatter(bins2,gamma2)

plt.plot(bins3,gamma3,label="NE-SW")
plt.scatter(bins3,gamma3)

plt.plot(bins4,gamma4,label="NW-SE")
plt.scatter(bins4,gamma4)

plt.xlabel("lag distance")
plt.ylabel("semi-variance")

plt.legend()

plt.show()
