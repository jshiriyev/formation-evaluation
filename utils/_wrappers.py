def trim(function):

    def wrap(*args,lower=0,upper=1,**kwargs):
        values = function(*args,**kwargs)

        if upper is not None:
            values[values>upper] = upper

        if lower is not None:
            values[values<lower] = lower

        return values

    return wrap