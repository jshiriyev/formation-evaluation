import numpy as np

from borepy.scomp.optimize import root

def objective1(x):
    return x**3-x-2

def objective2(x):
    return x**2-4*np.sin(x)

def objective3(x):
    return x**2-4*x+4

sol1 = root.bisection(objective1,1,2,tol=1e-5)

print(sol1.info)
print(sol1.value)
print(sol1.minima,end="\n\n")

sol2 = root.bisection(objective2,1,3,tol=1e-7)

print(sol2.info)
print(sol2.value)
print(sol2.minima,end="\n\n")

sol3 = root.bisection(objective3,1,3,tol=1e-7)

print(sol3.info)
print(sol3.value)
print(sol3.minima)