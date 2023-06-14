class newton():

    def __init__(self,func,der1,initial,tol=1e-5,args=None):

        self.initial = initial

        self.tol = tol

        self.calls = 0

        if args is None:
            args = []

        self._iterate(func,der1,args)

    def _iterate(self,func,der1,args):

        initial = self.initial

        d0 = func(initial,*args)
        d1 = der1(initial,*args)

        self.calls += 1

        while abs(d0/d1)>self.tol:

            print(f"{self.calls:2} {initial:8.6f},{d0:8.6f},{d1:8.6f},{d0/d1:8.6f}")

            initial -= d0/d1

            d0 = func(initial,*args)
            d1 = der1(initial,*args)

            self.calls += 1

        self.info = f"Converged after {self.calls} calls."

        self.value = initial

        self.minima = d0

if __name__ == "__main__":

    import numpy as np

    def f1(x):
        return x**2-4*np.sin(x)

    def f2(x):
        return 2*x-4*np.cos(x)

    sol1 = newton(f1,f2,3,tol=1e-8)

    def t1(x):
        return x**2-2*x+1

    def t2(x):
        return 2*x-2

    sol2 = newton(t1,t2,3,tol=1e-5)

    print(sol2.info)