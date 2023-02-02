import numpy

from ._ints import ints
from ._floats import floats
from ._strs import strs
from ._dates import dates
from ._datetimes import datetimes

def arange(*args,**kwargs):
    """Generating column by defining dtype and sending the keywords for array creating methods."""
    """It is a special function that takes input and returns linearly spaced data for
    ints, floats, string, datetime"""

    #start stop size

    if len(args)==0:
        pass
    elif len(args)==1:
        kwargs['stop'], = args
    elif len(args)==2:
        kwargs['start'],kwargs['stop'] = args
    elif len(args)==3:
        kwargs['start'],kwargs['stop'],kwargs['size'] = args
    elif len(args)==4:
        kwargs['start'],kwargs['stop'],kwargs['size'],kwargs['dtype'] = args
    else:
        raise TypeError("Arguments are too many!")

    dtype = kwargs.get('dtype')

    if dtype is None:
        dtype = _key2column.get_dtype(args)
    elif isinstance(dtype,str):
        dtype = numpy.dtype(dtype)

    if dtype.type is numpy.dtype('int').type:    
        _array = arrinteger(*args,**kwargs)
    elif dtype.type is numpy.dtype('float').type:
        _array = arrfloat(*args,**kwargs)
    elif dtype.type is numpy.dtype('str').type:
        _array = arrstring(*args,**kwargs)
    elif dtype.type is numpy.dtype('datetime64').type:
        _array = arrdatetime(*args,**kwargs)
    else:
        raise ValueError(f"dtype.type is not int, float, str or datetime64, given {dtype.type=}")

    return _array

def repeat(times,size=None):

    pass

def iterator(*args,size=None):

    arrs = [array1d(arg) for arg in args]

    if size is None:
        size = len(max(arrs,key=len))

    for index,_array in enumerate(arrs):
        repeat_count = int(numpy.ceil(size/_array.size))
        arrs[index] = numpy.tile(_array,repeat_count)[:size]

    return zip(*arrs)

if __name__ == "__main__":

    pass