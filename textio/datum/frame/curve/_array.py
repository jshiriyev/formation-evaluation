import datetime

from dateutil import parser

from .special import ints
from .special import floats
from .special import strs
from .special import dates
from .special import datetimes

from ._flatten import flatten

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

def get_valid_value(values):

    for value in values:
        if value is not None:
            return value

def get_python_type(value):

    for attempt in (float,parser.parse):

        try:
            conv_value = attempt(value)
        except:
            continue

        return type(conv_value)

    return str