from borepy.scomp.optimize import bisection

def func(x):
    return x**3-x-2

bisection(func,1,2,tol=1e-5)

print(func(1.52138138))
