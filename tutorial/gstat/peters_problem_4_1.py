import numpy as np

import _setup

from borepy.scomp import gstats

data = np.loadtxt("peters_table_4_14.txt",skiprows=2)

layer = data[:,0].astype("int16")
height = data[:,1]
perm = data[:,2]
phi = data[:,3]
sw = data[:,4]

dp = gstats.dykstraparson(perm,thickness=height)

print("DP",dp.coeff)
dp.view()

lor = gstats.lorenz(perm,phi,thickness=height)

print("Lorenz",lor.coeff)
lor.view()