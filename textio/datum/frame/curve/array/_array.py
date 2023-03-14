import datetime

from dateutil import parser

import numpy

from .special._ints import ints
from .special._floats import floats
from .special._strs import strs
from .special._dates import dates
from .special._datetimes import datetimes

def array(values,pytype=None,**kwargs):

    values = flatten(values)

    if pytype is None:
        vvalue = get_valid_value(values)
        pytype = get_python_type(vvalue) #float, datetime, or str

    if pytype is int:
        return ints(values,**kwargs)
    elif pytype is float:
        return floats(values,**kwargs)
    elif pytype is str:
        return strs(values,**kwargs)
    elif pytype is datetime.date:
        return dates(values,**kwargs)
    elif pytype is datetime.datetime:
        return datetimes(values,**kwargs)

def flatten(vals,_list=None):
    """Returns a flat list."""

    _list = [] if _list is None else _list

    if type(vals).__module__ == numpy.__name__:
        flatten(vals.tolist(),_list)
    elif isinstance(vals,str):
        _list.append(vals)
    elif hasattr(vals,"__iter__"):
        [flatten(val,_list) for val in list(vals)]
    else:
        _list.append(vals)

    return _list

def get_valid_value(values):

    for value in values:
        if value is not None:
            return value

    return float("nan")

def get_python_type(value):

    for attempt in (float,parser.parse):

        try:
            conv_value = attempt(value)
        except:
            continue

        return type(conv_value)

    return str