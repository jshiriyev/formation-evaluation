import numpy as np

from borepy.wtest import pressure

k = 200

phi = 0.15

mu = 1.5

ct = 25e-6

h = 30

rw = 0.25

fvf = 1.2

rate = 800

time = np.logspace(-5,1.2)

P = pressure(k,phi,mu,ct,h,rw,rate,time,fvf=fvf)

P.set_boundary(area=40)

P.view()
