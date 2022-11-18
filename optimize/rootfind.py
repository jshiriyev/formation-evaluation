if __name__ == "__main__":
    import setup

def secant(obj_func,x_0,x_1,*args):
    x0 = x_0
    x1 = x_1
    tol = 1
    while tol>1e-10:
        y0 = obj_func(x0,*args)
        y1 = obj_func(x1,*args)
        x2 = x1-y1*(x1-x0)/(y1-y0)
        tol = abs(x2-x1)
        x0 = x1
        x1 = x2
##        print(tol)
    return x2

def newton(obj_func,obj_func_der,x_0,*args):
    x_old = x_0
    tol = 1
    while tol>1e-10:
        x_new = x_old-obj_func(x_old,*args)/obj_func_der(x_old,*args)
        tol = abs(x_new-x_old)
        x_old = x_new
##        print(tol)
    return x_new

def bisection(obj_func,xL,xU,*args,Nmax=50,tol=1e-3):

    fL = obj_func(xL,*args)
    fU = obj_func(xU,*args)

    if fL*fU>0:
        print("Interval boundaries has not been selected correctly")
        return

    for i in range(Nmax):

        x = (xL+xU)/2

        f = obj_func(x,*args)

        if abs(f)<tol or xU-xL<tol:
            xOPT = x
            break

        if f*fL<0:
            xU = x
        elif f*fU<0:
            xL = x

    try:
        print("Converged result is: %.8f" %xOPT)
        print("Number of iterations is: %d" %(i+1))
    except:
        print("Convergence could not be obtained with %d iterations" %(Nmax))