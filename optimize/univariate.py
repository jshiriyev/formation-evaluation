if __name__ == "__main__":
    import setup

def golden(obj_func,xL,xU,r=None,Nmax=50,tol=1e-3):

    if r is None:
        r = (5**(1/2)-1)/2
    
    for i in range(Nmax):

        x1 = xL+r*(xU-xL)
        x2 = xU-r*(xU-xL)

        f1 = obj_func(x1)
        f2 = obj_func(x2)

        if f1<f2:
            xL = x2
        else:
            xU = x1

        if abs(xL-xU)<tol:
            xOPT = (x1+x2)/2
            break

    try:
        print("Converged result is: %.8f" %xOPT)
        print("Number of iterations is: %d" %(i+1))
    except:
        print("Convergence could not be obtained with %d iterations" %(Nmax))