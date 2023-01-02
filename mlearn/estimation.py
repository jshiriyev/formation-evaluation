import os
import sys

import numpy as np

class item():

    def __init__(self,observed_points,observed_values):

        self.xobs = observed_points
        self.yobs = observed_values
    
class interpolate():

    def __init__(self,X,Y,x):
        """1D"""

        """
        X are the locations where Y values are given
        x are the locations where we want to calculate y
        based on the interpolation of Y values
        """

        pass

    def smooth(self):

        pass

    def fit(self):
        
        xadded = X[x.max()<X]
        
        x = np.append(x,xadded)
        
        N = x.size
        L = X.size

        d1 = np.array(list(range(N)))
        d2 = np.array(list(range(N,N+L)))
        
        row = np.concatenate(((d1[0],d1[-1]),d1[:-1],d1[1:],d1[1:-1]))
        col = np.concatenate(((d1[0],d1[-1]),d1[1:],d1[:-1],d1[1:-1]))

        Mone = np.ones(2)*(-1)
        Pone = np.ones(2*(N-1))
        Mtwo = np.ones((N-2))*(-2)

        data = np.concatenate((Mone,Pone,Mtwo))

        G = sps.csr_matrix((data,(row,col)),shape=(N,N))
        d = sps.csr_matrix((Y,(d2,np.zeros(L))),shape=(N+L,1))

        x = x.reshape((1,-1))
        X = X.reshape((-1,1))
        
        Glow = np.zeros((L,N))

        dmat = np.abs(x-X)              # distance matrix for the given x and X vectors
        
        colID = dmat.argsort()[:,:2]    # column indices of two minimum row values in dmat
        rowID = np.tile(np.arange(L).reshape((-1,1)),2)
                                        # row indices of two minimum row values in dmat
        
        dmin = dmat[rowID,colID]        # two minimum distance values of each row in dmat

        Glow[rowID,colID] = 1-dmin/np.sum(dmin,axis=1,keepdims=True)

        G = sps.vstack([G,sps.csr_matrix(Glow)])

        A = G.transpose()*G
        b = G.transpose()*d

        y = sps.linalg.spsolve(A,b)

        if xadded.size:
            return y[:-xadded.size]
        else:
            return y

    def fit_matlab(self):
        """MATLAB interpolation"""
        
        fid=fopen('Data_all.bin');
        allData=fread(fid,'float');

        fid=fopen('Data_in.bin');
        d=fread(fid,'float');

        L=length(allData);
        idx=(1:L)

        nonZero=allData(d~=0);
        nonZeroID=idx(d~=0);

        l=length(nonZero);

        %% Generation of the G matrix and d vector

        epslon=1;

        G=spalloc(L,L,(L-2)*(L-1));
        G=G+sparse(2:L-1,2:L-1,-2*epslon,L,L);
        G=G+sparse(1:L-1,2:L,epslon,L,L);
        G=G+sparse(2:L,1:L-1,epslon,L,L);
        G=G+sparse(1,1,-epslon,L,L);
        G=G+sparse(L,L,-epslon,L,L);

        G=[sparse(1:l,nonZeroID,1); G];
        d=[nonZero; spalloc(L,1,0)];

        m=(G'*G)\(G'*d);

        %% Plot of the Results

        figure(1)
        spy(G)
        title('Structure of the G matrix');
        ylabel('Dimensions of G is 125x100');

        figure(2)
        scatter(nonZeroID,nonZero,'r'); hold on
        plot(idx,allData,'b',idx,m,'m')
        title('Interpolation');
        legend('Dumped Data','Full Data','Interpolation',3);
        grid on

class moving_average():

    def __init__(self,prop,time):

        self.prop = prop
        self.time = time

    def fit(self,k=2):

        self.k = k

        N = self.prop.size

        G = np.empty((N-self.k,self.k))

        for i in range(self.k):
            G[:,i] = self.prop[i:-self.k+i]

        d = self.prop[self.k:]
        
        A = np.dot(G.transpose(),G)
        b = np.dot(G.transpose(),d)

        x = np.linalg.solve(A,b)

        self.constants = x

    def forecast(self,r):

        ynew = np.empty(self.k+r)
        ynew[:self.k] = self.prop[-self.k:]

        for i in range(r):
            ynew[self.k+i] = np.dot(ynew[i:self.k+i],self.constants)

        self.est = ynew[self.k:]

class regression(item):

    def __init__(self,observed_points,observed_values):

        super(regression,self).__init__(observed_points,observed_values)

    def linear_train(self):

        N = self.xobs.shape[0]

        O = np.ones((N,1))
        X = self.xvalues.reshape(N,-1)
        Y = self.yvalues.reshape(N,-1)

        G = np.concatenate((O,X),axis=1)

        A = np.dot(G.transpose(),G)
        b = np.dot(G.transpose(),Y)

        x = np.linalg.solve(A,b)

        self.slope = x[0]
        self.yintercept = x[1]

    def ridge(self):
        
        pass

    def estimate(self,estimated_points):
        
        self.Xest = estimated_points

        Yest = self.intercept+self.slope*self.Xest

        return Yest

class kneighbor(item):

    def __init__(self,observed_points,observed_values):

        super(kneighbor,self).__init__(observed_points,observed_values)

    def eucledian_distance(self,estimated_points):

        self.xest = estimated_points

        #xobs = np.array([[1,2],[3,4],[5,6],[6,9],[11,15],[7,0]])
        #xest = np.array([[4,7],[8,2]])

        mobs = xtrained.reshape(self.xobs.shape[0],1,-1)
        mest = xguessed.reshape(1,self.xest.shape[0],-1)

        self.distance = np.sqrt(((mobs-mest)**2).sum(2))

    def estimate(self,k):

        idx = np.argpartition(self.distance,k,axis=0)

        #ytrained = np.array([['A'],['A'],['B'],['B'],['A'],['B']])

        yest = np.array([self.yobs[idx[:,i],0][:k] for i in range(idx.shape[1])]).T
    
        return yest

class neuralnetwork(item):
    
    def __init__(self,observed_points,observed_values):

        super(neuralnetwork,self).__init__(observed_points,observed_values)
        
        np.random.seed(1)
        
        self.weights = 2*np.random.random((3,1))-1

    def sigmoid(self,x):
        
        phi = 1/(1+np.exp(-x))
        
        return phi
    
    def sigmoid_derivative(self,x):
        
        phi_derivative = x*(1-x)
        
        return phi_derivative

    def train(self,iterationNumber):
        
        for iteration in range(iterationNumber):
            
            output = self.estimate(self.xobs)
            
            error = self.yobs-output
            
            adjustment = error*self.sigmoid_derivative(output)
            
            self.weights += np.dot(self.xobs.T,adjustment)
            
    def estimate(self,estimated_points):

        self.xest = estimated_points
        
        temp = np.dot(self.xest,self.weights)
        
        yest = self.sigmoid(temp)
        
        return yest

if __name__ == "__main__":
    
    xobs = np.array([[0,0,1],
                     [1,1,1],
                     [1,0,1],
                     [0,1,1]])
    
    yobs = np.array([[0,1,1,0]]).T

    NN = neuralnetwork(xobs,yobs)
    
##    print(NN.weights)
    
    NN.train(20000)
    
##    print(NN.weights)
    
    xest = np.array([[1,0,0]])
    yest = NN.estimate(xest)

    print("The trained input is:")
    print(xobs)
    print("The trained output is:")
    print(yobs)
    print("The questioned input is:")
    print(xest)
    print("The Answer is:")
    print(yest)

#     t = np.linspace(0,10,21)
#     y = np.sin(t)

# ##    t = np.linspace(1,9,9)
# ##    y = np.array([1,2,3,4,5,6,7,8,9])

#     T = moving_average(y,t)

#     T.fit(3)
#     T.forecast(40)
    
#     plt.scatter(T.time,T.prop)
#     plt.scatter(10+np.linspace(1,20,40),T.est)
#     plt.show()
