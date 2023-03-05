import numpy

from .frame.curve.special._ints import ints
from .frame.curve.special._floats import floats
from .frame.curve.special._strs import strs
from .frame.curve.special._dates import dates
from .frame.curve.special._datetimes import datetimes

def iterator(*args,size=None):

    arrs = [array1d(arg) for arg in args]

    if size is None:
        size = len(max(arrs,key=len))

    for index,_array in enumerate(arrs):
        repeat_count = int(numpy.ceil(size/_array.size))
        arrs[index] = numpy.tile(_array,repeat_count)[:size]

    return zip(*arrs)