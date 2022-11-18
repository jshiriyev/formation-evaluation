import numpy as np

import time

from scipy import optimize

if __name__ == "__main__":
    import setup

from optimize.root import newton
from optimize.root import secant

def obj(phi,epd,Re):
    xx = np.power(phi,-0.5)
    return xx+2*np.log10(epd/3.7+2.51/Re*xx)

def obj_der(phi,epd,Re):
    xx = np.power(phi,-0.5)
    xy = np.power(phi,-1.5)
    return xy*(-1/2-2.51/np.log(10)/Re/(epd/3.7+2.51/Re*xx))

epd = 1e-4

Re = 100000

phi0 = 8/Re
phi1 = 16/Re

tic = time.perf_counter()
phiS = secant(obj,phi0,phi1,epd,Re)
toc = time.perf_counter()
print(f"home built secant method took \t {toc - tic:0.7f} seconds")

tic = time.perf_counter()
phiN = newton(obj,obj_der,phi0,epd,Re)
toc = time.perf_counter()
print(f"home built newton method took \t {toc - tic:0.7f} seconds")

tic = time.perf_counter()
phiM = optimize.newton(obj,phi0,args=(epd,Re))
toc = time.perf_counter()
print(f"scipy newton method took \t {toc - tic:0.7f} seconds\n")

print("home built secant method result is \t",phiS)
print("home built newton method result is \t",phiN)
print("scipy newton method result is \t\t",phiM)
##print(obj(0.01851386607747164,epd,Re))
##print(obj(0.01851386607747165,epd,Re))
