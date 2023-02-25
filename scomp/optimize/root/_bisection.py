class bisection():

    def __init__(self,func,lower,upper,tol=1e-5,args=None):

        self.lower = lower
        self.upper = upper

        self.tol = tol

        if args is None:
            args = []

        self._iterate(func,args)

    def _iterate(self,func,args):

        lower,upper = float(self.lower),float(self.upper)

        flower = func(lower,*args)
        fupper = func(upper,*args)

        self.calls = 2

        while (upper-lower)>self.tol:

            middle = (lower+upper)/2

            fmiddle = func(middle,*args)

            # print(f"{self.calls:2} {lower:8.6f},{flower:8.6f},{upper:8.6f},{fupper:8.6f}")

            self.calls += 1

            if fmiddle*flower<0:
                upper,fupper = middle,fmiddle
            elif fmiddle*fupper<0:
                lower,flower = middle,fmiddle
            else:
                self.info = "Either there is no root or even number of roots."
                middle,fmiddle = float('nan'),float('nan')
                break
        else:

            self.info = f"Found a root after {self.calls} iterations."

        self.value = middle

        self.minima = fmiddle
