def trim(function):

    def wrap(*args,lower=0,upper=1,**kwargs):
        values = function(*args,**kwargs)

        if upper is not None:
            values[values>upper] = upper

        if lower is not None:
            values[values<lower] = lower

        return values

    return wrap

if __name__ == "__main__":

    import numpy as np

    @trim
    def saturation(res):
        return res/100

    res = np.linspace(0,130)

    print(res/100)

    sat = saturation(res,lower=0.1,upper=0.7)

    print(sat)