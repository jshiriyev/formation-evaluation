import numpy as np

import matplotlib.pyplot as plt

if __name__ == "__main__":
    import dirsetup

from optimize.univariate import golden

def objective1(x):
    return (x-2)**2+2

def objective2(x):
    F = 10+0.2*x**(2.3)
    G = 10+80*np.exp(-0.3*x)
    return F+G

def objective3(x):
    return x*(x-2)*(x-3)*(x-6)+15

def objective4(x):
    return (x**2)/(1-x)

xL = -3
xU = 3

gs = golden(objective1,(xL,xU),ratio=0.51,nitermax=10000,tol=1e-5)

x = np.linspace(xL,xU,200)

plt.plot(x,objective1(x))
plt.scatter(gs.minsol,gs.minval)

plt.xlabel('x-axis')
plt.ylabel('objective function')

plt.show()
