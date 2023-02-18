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