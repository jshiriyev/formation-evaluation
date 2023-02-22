from matplotlib import pyplot as plt

import numpy as np

from borepy.scomp.regression import LinearSimple

data = np.loadtxt("table_11_1.txt",skiprows=3)

x = data[:,0]
y = data[:,1]

slr = LinearSimple(y,x)

slr.train()

print(f"{slr.b0} intercept")
print(f"{slr.b1} slope")
print(f"{slr.R2} R2")

print(f"{slr.beta0confint(0.05)} beta0 confidence interval")
print(f"{slr.beta1confint(0.05)} beta1 confidence interval")

beta00 = 0
beta10 = 0.9

print(f"{slr.beta0test(beta00)} test {beta00 = }")
print(f"{slr.beta1test(beta10)} test {beta10 = }")

xest = np.linspace(0,60,100)
yest = slr.estimate(xest)

ymeanl,ymeanu = slr.meanconfint(xest,0.05)

ypl,ypu = slr.predict(xest,0.05)

plt.scatter(x,y)

plt.plot(xest,yest,color="red")
plt.plot(xest,ymeanl,color='red',linestyle='--',linewidth=0.5)
plt.plot(xest,ymeanu,color='red',linestyle='--',linewidth=0.5)
plt.plot(xest,ypl,color='blue',linestyle='--',linewidth=0.5)
plt.plot(xest,ypu,color='blue',linestyle='--',linewidth=0.5)

plt.xlim((0,54))
plt.ylim((0,50))

plt.xlabel("x-values")
plt.ylabel("y-values")

plt.show()