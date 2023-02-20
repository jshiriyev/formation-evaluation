from matplotlib import pyplot as plt

import numpy as np

from borepy.scomp.regression import Linear

data = np.loadtxt("table_1_probability_and_statistics.txt",skiprows=3)

x = data[:,0]
y = data[:,1]

linear = Linear(x,y)

linear.train()

print(linear.b0,linear.b1,linear.R2)

b0ci = linear.b0ci(0.05)
b1ci = linear.b1ci(0.05)

# print(b0ci)
# print(b1ci)

print(linear.b0test(0))

yest = linear.estimate([0,60])

plt.scatter(x,y)

plt.plot([0,60],yest,color="red")

plt.xlabel("x-values")
plt.ylabel("y-values")

plt.show()