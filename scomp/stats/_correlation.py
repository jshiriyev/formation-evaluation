import os
import sys

import matplotlib.pyplot as plt
import numpy as np

from scipy.stats import norm

class correlation():

    def coefficient(self):

        X = self.x
        Y = self.y

        N = X.shape[0]

        std_X = np.sqrt(1/(N-1)*np.sum((X-X.mean())**2))
        std_Y = np.sqrt(1/(N-1)*np.sum((Y-Y.mean())**2))
            
        cov_XY = 1/(N-1)*np.sum((X-X.mean())*(Y-Y.mean()))  
        rho_XY = cov_XY/(std_X*std_Y)
            
        return rho_XY

    def qqplot(self):

        ##A = np.random.normal(25,10,100)
        ##B = np.random.normal(25,5,100)

        percentile = np.linspace(0,100,101)

        fA = np.percentile(A,percentile)
        fB = np.percentile(B,percentile)

        zmin = np.min((fA.min(),fB.min()))
        zmax = np.max((fA.max(),fB.max()))

        plt.plot(np.array([zmin,zmax]),np.array([zmin,zmax]),'--',c='k')
        plt.scatter(fA,fB,c='r')

        plt.xlabel('A',fontsize=14)
        plt.ylabel('B',fontsize=14)

        ax = plt.gca()
        ax.set_aspect('equal')