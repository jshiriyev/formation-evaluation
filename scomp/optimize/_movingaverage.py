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