import numpy as np

import matplotlib.pyplot as plt

if __name__ == "__main__":
    import setup

from numerics.integrate import trapezoid as mytrapezoid
from numerics.integrate import simpson as mysimpson

from scipy.integrate import quad
from scipy.integrate import trapezoid
from scipy.integrate import simps

## Exercise 1

def integrand(x):
    return 1/(1+x**2)

x = np.linspace(1,2,100)

y = integrand(x)

Iq = quad(integrand,1,2)
It = trapezoid(y,x)
Is = simps(y,x)

Itm = mytrapezoid(integrand,bounds=(1,2))
Ism = mysimpson(integrand,bounds=(1,2))

Iactual = np.arctan(2)-np.arctan(1)

## Exercise 2

##x = np.array([0,1.1,2.5,3.1,4.3,5.6,5.9,7.2,7.8,7.9,8.3,8.9,9.3,9.6,10.])
##y = np.array([0.5,0.691,0.845,0.880,0.896,0.846,0.826,0.714,0.652,0.642,0.598,0.533,0.489,0.457,0.414])
##
##It = trapezoid(y,x)
##Is = simps(y,x)

print("Scipy Quad gives {}".format(Iq))
print("SciPy Trapezoid gives {} and myTrapezoid gives {}".format(It,Itm))
print("SciPy Simpson gives {} and mySimpson gives {}".format(Is,Ism))
print("True result is {}".format(Iactual))
