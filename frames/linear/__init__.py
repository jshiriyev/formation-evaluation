import datetime

import numpy

from ._ints import ints
from ._floats import floats
from ._strs import strs
from ._dates import dates
from ._datetimes import datetimes

def array(vals,null=None,unit=None,ptype=None):

    vals = flatten(vals)

    if unit is not None:
        ptype = float
        
    if ptype is None:
        ptype = ptype(vals) #float, datetime, or str

    if ptype is int:
        return ints(vals,null=null)
    elif ptype is float:
        return floats(vals,null=null,unit=unit)
    elif ptype is str:
        return strs(vals,null=null)
    elif ptype is datetime.date:
        return dates(vals,null=null)
    elif ptype is datetime.datetime:
        return datetimes(vals,null=null)

def arange(*args,start=None,stop=None,step=None,size=None,ptype=None,**kwargs):
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