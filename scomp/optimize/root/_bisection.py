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