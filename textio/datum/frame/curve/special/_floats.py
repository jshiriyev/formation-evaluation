import re

import numpy

class floats(numpy.ndarray):

    def __new__(cls,values,null=None,unit=None):

        null = numpy.nan if null is None else float(null)

        values = iterable(values)

        obj = numpy.asarray(values,dtype='float64').view(cls)

        obj._null = null

        obj._unit = unit

        return obj

    def __array_finalize__(self,obj):

        if obj is None: return

        self._null = getattr(obj,'_null',numpy.nan)
        self._unit = getattr(obj,'_unit',None)

    def __repr__(self):

        parent = super().__repr__()

        child = parent.replace('nan',str(self.null))

        return re.sub(r"\s+"," ",child)

    def __str__(self):

        parent = super().__str__()

        child = parent.replace('nan',str(self.null))

        return re.sub(r"\s+"," ",child)

    def normalize(self,vmin=None,vmax=None):
        """It returns normalized values (in between 0 and 1) of float arrays.
        If vmin is provided, everything below 0 will be reported as zero.
        If vmax is provided, everything above 1 will be reported as one."""

        vals = self.copy()

        if vmin is None:
            vmin = vals.min()

        if vmax is None:
            vmax = vals.max()

        vals = (vals-vmin)/(vmax-vmin)

        vals[vals<=0] = 0
        vals[vals>=1] = 1

        return vals

    def valids(self):

        vals = self.copy()

        return vals[self.isvalid]

    def min(self):

        return numpy.nanmin(self.view(numpy.ndarray))

    def max(self):

        return numpy.nanmax(self.view(numpy.ndarray))

    @property
    def null(self):

        return self._null

    @property
    def unit(self):

        return self._unit

    @property
    def isvalid(self):
        """It return boolean array True for float and False for null."""
        return ~numpy.isnan(self.view(numpy.ndarray))
    
    @property
    def isnull(self):
        """It return numpy bool array, True for null and False for float."""
        return numpy.isnan(self.view(numpy.ndarray))

def iterable(values):

    vals = []

    for value in values:

        try:
            value = float(value)
        except TypeError:
            value = numpy.nan
        except ValueError:
            value = numpy.nan

        vals.append(value)

    return vals

def arange(*args,size=None,dtype=None):

    if len(args)==0:
        return
    elif len(args)==1:
        _array = array1d(args[0],size)

    if dtype is None:
        return _array
    else:
        return _array.astype(dtype)

def toint(value,default=None):
    """Returns integer converted from float value.
    If there is a ValueError it returns default value."""

    try:
        value = int(value)
    except ValueError:
        value = default

    return value

if __name__ == "__main__":

    array = floats([1,2,3,4,None,7],null=-99.999)

    print(array)
    print(array+1)

    print(array.valids())

    print(array.min())
    print(array.max())

    print(array.normalize())