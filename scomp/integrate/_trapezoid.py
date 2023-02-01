import types

import numpy as np

def trapezoid(f,x=None,bounds=(0,1),Nsample=100):

    if x is None:
        x = np.linspace(*bounds,Nsample)

    if isinstance(f,types.FunctionType):
        y = f(x)
    else:
        y = f

    xdiff = (x[1:]-x[:-1])
    ymids = (y[1:]+y[:-1])/2

    Inum = np.sum(ymids*xdiff)

    return Inum
    

    
