from matplotlib import pyplot as plt

import numpy as np

from borepy.scomp.regression import LinearMultiple

data = np.loadtxt("table_12_1.txt",skiprows=3)

y = data[:,0]
x1 = data[:,1]
x2 = data[:,2]
x3 = data[:,3]

mlr = LinearMultiple(y,x1,x2,x3)

mlr.train()

print(mlr.bs)