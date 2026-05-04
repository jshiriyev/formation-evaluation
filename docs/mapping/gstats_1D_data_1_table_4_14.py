import numpy as np

import matplotlib.pyplot as plt

from borepy.gmodel.gstats import dykstraparson
from borepy.gmodel.gstats import lorenz

data = np.loadtxt("peters_table_4_14.txt",skiprows=2)

layer = data[:,0].astype("int16")
height = data[:,1]
perm = data[:,2]
phi = data[:,3]
sw = data[:,4]

# dp = dykstraparson(perm,thickness=height)

# print("DP",dp.coeff)
# dp.view()

# lor = lorenz(perm,phi,thickness=height)

# print("Lorenz",lor.coeff)
# lor.view()

D = np.cumsum(height)-height/2
print(D)
logperm = np.log(perm)

N = height.size

C = int(N*(N-1)/2)

H = np.zeros((C,))
B = np.zeros((C,))

k = 0

for i in range(N):

	for j in range(i+1,N):
		
		H[k] = abs(D[j]-D[i])
		B[k] = ((logperm[j]-logperm[i])**2)/2

		k += 1

laglen = 10
lagtol = 5

x = np.zeros(14)
y = np.zeros(14)

for i in range(1,15):

	dmid = i*laglen-lagtol

	dmin,dmax = dmid-lagtol,dmid+lagtol

	cond = np.logical_and(H>dmin,H<dmax)

	comb = B[cond]

	Nh = comb.size

	x[i-1] = dmid
	y[i-1] = np.sum(comb)/Nh

plt.scatter(x,y)

plt.show()