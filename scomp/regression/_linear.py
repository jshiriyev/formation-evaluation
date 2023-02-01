class _linear(item):

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