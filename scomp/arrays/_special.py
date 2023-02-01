import numpy

from ._ints import ints
from ._floats import floats
from ._strs import strs
from ._dates import dates
from ._datetimes import datetimes

def Special(vals):

    if vals is None:
        _array = numpy.array([numpy.nan])
    elif type(vals).__module__=="numpy":
        _array = vals.flatten()
    elif isinstance(vals,str):
        _array = numpy.array([vals])
    elif isinstance(vals,datetime.datetime):
        _array = numpy.array([vals]).astype('datetime64[s]')
    elif isinstance(vals,datetime.date):
        _array = numpy.array([vals]).astype('datetime64[D]')
    elif hasattr(vals,"__iter__"):
        _array = [flatten(val) for val in list(vals)]
        if len(_array) == 0:
            _array = numpy.array(_array)
        else:
            _array = numpy.concatenate(_array)
    else:
        _array = numpy.array([vals])

        # # arg in vals, the first one
        # if arg is None:
        #     return
        # elif isinstance(arg,int):
        #     return numpy.dtype(type(arg))
        # elif isinstance(arg,float):
        #     return numpy.dtype(type(arg))
        # elif isinstance(arg,str):
        #     arg = _key2column.todatetime(arg)
        #     if arg is None:
        #         return numpy.str_(arg).dtype
        #     else:
        #         return numpy.dtype('datetime64[s]')
        # elif isinstance(arg,datetime.datetime):
        #     return numpy.dtype('datetime64[s]')
        # elif isinstance(arg,datetime.date):
        #     return numpy.dtype('datetime64[D]')
        # elif isinstance(arg,numpy.datetime64):
        #     return arg.dtype
        # else:
        #     return

    return _array

