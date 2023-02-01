def newton(obj_func,obj_func_der,x_0,*args):
    x_old = x_0
    tol = 1
    while tol>1e-10:
        x_new = x_old-obj_func(x_old,*args)/obj_func_der(x_old,*args)
        tol = abs(x_new-x_old)
        x_old = x_new
##        print(tol)
    return x_new