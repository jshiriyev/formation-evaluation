import os
import sys

import numpy

class neuralnetwork():
    
    def __init__(self,observed_points,observed_values):

        super(neuralnetwork,self).__init__(observed_points,observed_values)
        
        numpy.random.seed(1)
        
        self.weights = 2*numpy.random.random((3,1))-1

    def sigmoid(self,x):
        
        phi = 1/(1+numpy.exp(-x))
        
        return phi
    
    def sigmoid_derivative(self,x):
        
        phi_derivative = x*(1-x)
        
        return phi_derivative

    def train(self,iterationNumber):
        
        for iteration in range(iterationNumber):
            
            output = self.estimate(self.xobs)
            
            error = self.yobs-output
            
            adjustment = error*self.sigmoid_derivative(output)
            
            self.weights += numpy.dot(self.xobs.T,adjustment)
            
    def estimate(self,estimated_points):

        self.xest = estimated_points
        
        temp = numpy.dot(self.xest,self.weights)
        
        yest = self.sigmoid(temp)
        
        return yest

if __name__ == "__main__":
    
    xobs = numpy.array([[0,0,1],
                     [1,1,1],
                     [1,0,1],
                     [0,1,1]])
    
    yobs = numpy.array([[0,1,1,0]]).T

    NN = neuralnetwork(xobs,yobs)
    
##    print(NN.weights)
    
    NN.train(20000)
    
##    print(NN.weights)
    
    xest = numpy.array([[1,0,0]])
    yest = NN.estimate(xest)

    print("The trained input is:")
    print(xobs)
    print("The trained output is:")
    print(yobs)
    print("The questioned input is:")
    print(xest)
    print("The Answer is:")
    print(yest)

#     t = numpy.linspace(0,10,21)
#     y = numpy.sin(t)

# ##    t = numpy.linspace(1,9,9)
# ##    y = numpy.array([1,2,3,4,5,6,7,8,9])

#     T = moving_average(y,t)

#     T.fit(3)
#     T.forecast(40)
    
#     plt.scatter(T.time,T.prop)
#     plt.scatter(10+numpy.linspace(1,20,40),T.est)
#     plt.show()
