import types

import numpy as np

if __name__ == "__main__":
    import setup

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

def simpson(f,x=None,bounds=(0,1),Nsample=100):

    if x is None:
        xbnds = np.linspace(*bounds,Nsample)
    else:
        xbnds = x

    xmids = (xbnds[1:]+xbnds[:-1])/2

    if isinstance(f,types.FunctionType):
        ybnds = f(xbnds)
        ymids = f(xmids)
    else:
        ybnds = f
        ymids = (f[1:]+f[:-1])/2

    xdiff = (xbnds[1:]-xbnds[:-1])

    I1 = ybnds[:-1]*xdiff/6
    I2 = ymids*4*xdiff/6
    I3 = ybnds[1:]*xdiff/6

    Inum = np.sum(I1)+np.sum(I2)+np.sum(I3)

    return Inum

    

    
