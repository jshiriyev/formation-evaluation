class golden():
    """It is the implementation of golden section search technique."""

    def __init__(self,func,lower,upper,tol=1e-5):

        self.lower = lower
        self.upper = upper

        self.tol = tol

        self._ratio = (5**(1/2)-1)/2

        self._iterate(func)

    def _iterate(self,func):

        lower,upper = self.lower,self.upper

        x1 = (1-self.ratio)*upper+self.ratio*lower
        x2 = (1-self.ratio)*lower+self.ratio*upper

        f1 = func(x1)
        f2 = func(x2)

        self.calls = 2

        while (upper-lower)>self.tol:

            if f1>f2:
                lower = x1
                x1 = x2
                f1 = f2
                x2 = (1-self.ratio)*lower+self.ratio*upper
                f2 = func(x2)
            else:
                upper = x2
                x2 = x1
                f2 = f1
                x1 = (1-self.ratio)*upper+self.ratio*lower
                f1 = func(x1)

            self.calls += 1

        self.solution = (lower+upper)/2

        self.minima = func(self.solution)

    @property
    def ratio(self):

        return self._ratio

if __name__ == "__main__":

    import matplotlib.pyplot as plt

    import numpy as np

    # def objective(x):
    #     return (x-2)**2+2

    def objective(x):
        return 0.5-x*np.exp(-x**2)

    x = np.linspace(0,4,100)

    o = objective(x)

    gs = golden(objective,0,4,tol=4e-2)

    print(gs.calls,gs.solution,gs.minima)

    plt.plot(x,o)
    plt.scatter(gs.solution,gs.minima)
    plt.show()
