import datetime

from dateutil import parser

import numpy

from .special._ints import ints
from .special._floats import floats
from .special._strs import strs
from .special._dates import dates
from .special._datetimes import datetimes

class array:

    ints = ints
    floats = floats
    strs = strs
    dates = dates
    datetimes = datetimes

    @staticmethod
    def flat(vals,ptype=None,**kwargs):

        vals = array.flatten(vals)

        if ptype is None:
            ptype = array.ptype(vals) #float, datetime, or str

        if ptype is int:
            return array.ints(vals,**kwargs)
        elif ptype is float:
            return array.floats(vals,**kwargs)
        elif ptype is str:
            return array.strs(vals,**kwargs)
        elif ptype is datetime.date:
            return array.dates(vals,**kwargs)
        elif ptype is datetime.datetime:
            return array.datetimes(vals,**kwargs)

    @staticmethod
    def flatten(vals,_list=None):
        """Returns a flat list."""

        _list = [] if _list is None else _list

        if type(vals).__module__ == numpy.__name__:
            array.flatten(vals.tolist(),_list)
        elif isinstance(vals,str):
            _list.append(vals)
        elif hasattr(vals,"__iter__"):
            [array.flatten(val,_list) for val in list(vals)]
        else:
            _list.append(vals)

        return _list

    @staticmethod
    def ptype(vals):

        for value in vals:
            if value is not None:
                break
        else:
            return float

        for attempt in (float,parser.parse):

            try:
                value_converted = attempt(value)
            except:
                continue

            return type(value_converted)

        return str

    @staticmethod
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

    @staticmethod
    def repeat(vals,times=None,size=None,null=None,ptype=None):
        """Returns numpy array with specified size.

        vals    : flat list, list
        size    : size of flat list to be created, integer
        """

        vals = array.flat(vals,ptype=ptype)

        if vals.size==0:
            return vals

        if times is None:
            times = int(numpy.ceil(size/vals.size))

        if size is None:
            return numpy.tile(vals,times)
        else:
            return numpy.tile(vals,times)[:size]

def iterator(*args,size=None):

    arrs = [array1d(arg) for arg in args]

    if size is None:
        size = len(max(arrs,key=len))

    for index,_array in enumerate(arrs):
        repeat_count = int(numpy.ceil(size/_array.size))
        arrs[index] = numpy.tile(_array,repeat_count)[:size]

    return zip(*arrs)