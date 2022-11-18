import numpy as np

import matplotlib.pyplot as plt

from scipy.optimize import minimize

def objective(variables):
   x,y = variables
   return (x-y)**2+1/3*(x+y-10)**2

x = np.linspace(0,8)
y = np.linspace(0,8)

S = minimize(objective,(0,0),method="Powell")

print(S)

fig = plt.figure()

ax = fig.add_subplot(111, projection='3d')

X,Y = np.meshgrid(x,y)

ax.plot_surface(X,Y,objective((X,Y)))

ax.set_xlabel('x-axis')
ax.set_ylabel('y-axis')

plt.show()
