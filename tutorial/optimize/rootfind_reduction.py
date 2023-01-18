if __name__ == "__main__":
    import setup

from optimize.root_find import bisection

def func(x):
    return x**3-x-2

bisection(func,1,2,tol=1e-5)
