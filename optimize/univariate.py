if __name__ == "__main__":
    import setup

class golden():

    def __init__(self,func,xlim,ratio=None,nitermax=100,tol=1e-5):

        self.xlim = xlim

        self.ratio = 2/(1+5**(1/2)) if ratio is None else ratio

        self.nitermax = nitermax

        self.tol = tol

        self._iterate(func)

    def _iterate(self,func):

        x_lower,x_upper = self.xlim

        for i in range(self.nitermax):
            x1 = (1-self.ratio)*x_lower+self.ratio*x_upper
            x2 = (1-self.ratio)*x_upper+self.ratio*x_lower

            f1 = func(x1)
            f2 = func(x2)

            if f1<f2:
                x_lower = x2
            else:
                x_upper = x1

            if abs(x_upper-x_lower)<self.tol:
                break
        else:
            raise("Maximum number of iterations reached")

        self.niter = i+1

        self.minsol = (x_lower+x_upper)/2

        self.minval = func(self.minsol)

if __name__ == "__main__":

    import matplotlib.pyplot as plt
    import numpy as np

    def objective(x):
        return (x-2)**2+2

    x = np.linspace(0,10,100)
    o = objective(x)

    gs = golden(objective,(0,10))

    print(gs.niter)

    plt.plot(x,o)
    plt.scatter(gs.minsol,gs.minval)
    plt.show()
