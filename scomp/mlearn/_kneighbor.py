import os
import sys

import numpy

class kneighbor():

    def __init__(self,observed_points,observed_values):

        super(kneighbor,self).__init__(observed_points,observed_values)

    def eucledian_distance(self,estimated_points):

        self.xest = estimated_points

        #xobs = numpy.array([[1,2],[3,4],[5,6],[6,9],[11,15],[7,0]])
        #xest = numpy.array([[4,7],[8,2]])

        mobs = xtrained.reshape(self.xobs.shape[0],1,-1)
        mest = xguessed.reshape(1,self.xest.shape[0],-1)

        self.distance = numpy.sqrt(((mobs-mest)**2).sum(2))

    def estimate(self,k):

        idx = numpy.argpartition(self.distance,k,axis=0)

        #ytrained = numpy.array([['A'],['A'],['B'],['B'],['A'],['B']])

        yest = numpy.array([self.yobs[idx[:,i],0][:k] for i in range(idx.shape[1])]).T
    
        return yest