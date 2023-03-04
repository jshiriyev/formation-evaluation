class secant():

    def __init__(self,func,x0,x1,tol=1e-5,args=None):

        self.x0 = x0
        self.x1 = x1

        self.tol = tol

        self.calls = 0

        if args is None:
            args = []

        self._iterate(func,args)

    def _iterate(self,func,args):

        x0,x1 = self.x0,self.x1

        y0 = func(x0,*args)

        self.calls += 1

        # print(f"{self.calls:2} {x0:8.6f},{y0:8.6f}")

        y1 = func(x1,*args)

        self.calls += 1

        d1 = (y1-y0)/(x1-x0)

        while abs(y1/d1)>self.tol:

            # print(f"{self.calls:2} {x1:8.6f},{y1:8.6f},{y1/d1:8.6f}")

            x2 = x1-y1/d1

            y2 = func(x2,*args)

            self.calls += 1

            x0,y0 = x1,y1
            x1,y1 = x2,y2

            d1 = (y1-y0)/(x1-x0)

        self.value = x1

        self.minima = y1

if __name__ == "__main__":

    import numpy as np

    def f1(x):
        return x**2-4*np.sin(x)

    sol1 = secant(f1,1,3,tol=1e-8)