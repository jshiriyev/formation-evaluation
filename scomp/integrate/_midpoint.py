import types

import numpy as np

def midpoint(f,x=None,bounds=(0,1),Nsample=100):

    if x is None:
        x = np.linspace(*bounds,Nsample)

    xmids = (xbnds[1:]+xbnds[:-1])/2

    if isinstance(f,types.FunctionType):
        ymids = f(xmids)
    else:
        ymids = (f[1:]+f[:-1])/2

    xdiff = (x[1:]-x[:-1])

    Inum = np.sum(ymids*xdiff)

    return Inum

    

    
