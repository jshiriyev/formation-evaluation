# DO NOT TOUCH PTYPE, IT'S WORKING PERFECTLY FINE!

import numpy

from dateutil import parser

from ._flatten import flatten

def ptype(vals,flat:bool=True):
    """Returns python type (float, datetime.datetime, or str) of the first
    None entry in the vals. By default, the function assumes that vals is flat.
    If it is not, toggle the flat. If all of them are None, default return is float."""

    if not flat:
        vals = flatten(vals)

    if isinstance(vals,numpy.ndarray):
        vals = vals.tolist()

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

if __name__ == "__main__":

    a = ptype([1,2,3,4])

    print(a)

    b = ptype([1,2,"c",4])

    print(b)

    c = ptype(["d",2,3,4])

    print(c)