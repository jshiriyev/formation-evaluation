import datetime

from dateutil import parser

from .special import ints
from .special import floats
from .special import strs
from .special import dates
from .special import datetimes

from .special import flatten

def array(values):

    values = flatten(values)

    for value in values:
        if value is not None:
            break

    value_type = get_higher_type(value) #float, datetime, or str

    if value_type is float:
        _array = floats(values)
    elif value_type is str:
        _array = strs(values)
    elif value_type is datetime.datetime:
        _array = datetimes(values)

    return _array

def get_higher_type(value):

    for attempt in (float,parser.parse):

        try:
            conv_value = attempt(value)
        except:
            continue

        return type(conv_value)

    return str