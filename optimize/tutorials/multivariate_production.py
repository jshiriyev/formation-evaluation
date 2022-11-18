import numpy as np

import matplotlib.pyplot as plt

from scipy.optimize import minimize
from scipy.optimize import Bounds
from scipy.optimize import LinearConstraint

def profit(production_rate,profit_per_product):

    return -np.sum(production_rate*profit_per_product)

profit_per_product = np.array([90,60,45])

lb = [0,0,0]
ub = [np.inf,np.inf,np.inf]

B = Bounds(lb,ub)

A = np.zeros((5,3))

A[0,:] = np.array([1.5 , 1.0 , 0.0 ])
A[1,:] = np.array([2.0 , 0.0 , 1.5 ])
A[2,:] = np.array([0.75, 3.0 , 0.0 ])
A[3,:] = np.array([1.25, 0.75, 1.0 ])
A[4,:] = np.array([1.0 , 0.0 , 2.0 ])

lb = [0, 0, 0, 0, 0]
ub = [450, 250, 800, 450, 600]

C = LinearConstraint(A,lb,ub)

H = lambda x,v: np.zeros((3,3))

T = minimize(profit,np.zeros(3),args=(profit_per_product,),
             method='trust-constr',constraints=C,bounds=B,hess=H)

print(T)
