import numpy as np

A = np.random.randint(0,1000,1_000_000)
B = np.random.randint(0,1000,1_000_000)
C = np.random.randint(0,1000,1_000_000)

##A = np.random.rand(1_000_000)
##B = np.random.rand(1_000_000)
##C = np.random.rand(1_000_000)

## WRITING TEXT FILE

Z = np.empty((A.size,3))
Z[:,0] = A
Z[:,1] = B
Z[:,2] = C
np.savetxt("data.txt",Z.astype(int),fmt="%i",header="a b c")

## WRITING BINARY NPZ FILE
np.savez_compressed('data.npz', a=A, b=B, c=C)


## READING TEXT FILE
T = np.loadtxt("data.txt",dtype=int)

## READING BINARY NPZ FILE
B = np.load('data.npz')

for key in B.keys():
    print(key)
