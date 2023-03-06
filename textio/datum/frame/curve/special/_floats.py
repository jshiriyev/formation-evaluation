import numpy

from ._flatten import flatten

class floats(numpy.ndarray): # HOW TO BEHAVE LIKE NUMPY ARRAY WHILE CORRECTLY FUNCTIONING WITH DIFFERET NAN

    def __new__(cls,variable,null=None,unit=None):

        null = numpy.nan if null is None else null

        iterable = floats._iterable(variable,null)

        obj = numpy.asarray(iterable,dtype='float64').view(cls)

        obj._null = str(null)

        obj._unit = unit

        return obj

    def __array_finalize__(self,obj):

        if obj is None: return

        self._null = getattr(obj,'_null',numpy.nan)
        self._unit = getattr(obj,'_unit',None)

    def normalize(self,vmin=None,vmax=None):
        """It returns normalized values (in between 0 and 1) of float arrays.
        If vmin is provided, everything below 0 will be reported as zero.
        If vmax is provided, everything above 1 will be reported as one."""

        datacolumn = copy.deepcopy(self)

        if vmin is None:
            vmin = datacolumn.min()

        if vmax is None:
            vmax = datacolumn.max()

        datacolumn.vals = (datacolumn.vals-vmin)/(vmax-vmin)

        datacolumn.vals[datacolumn.vals<=0] = 0
        datacolumn.vals[datacolumn.vals>=1] = 1

        datacolumn._valsunit()

        return datacolumn

    @property
    def isnone(self):
        """It return boolean array by comparing the values of vals to none types defined by column."""

        if self.vals.dtype.type is numpy.object_:

            bool_arr = numpy.full(self.vals.shape,False,dtype=bool)

            for index,val in enumerate(self.vals):
                if val is None:
                    bool_arr[index] = True
                elif isinstance(val,int):
                    if val==self.nones.int:
                        bool_arr[index] = True
                elif isinstance(val,float):
                    if numpy.isnan(val):
                        bool_arr[index] = True
                    elif not numpy.isnan(self.nones.float):
                        if val==self.nones.float:
                            bool_arr[index] = True
                elif isinstance(val,str):
                    if val==self.nones.str:
                        bool_arr[index] = True
                elif isinstance(val,numpy.datetime64):
                    if numpy.isnat(val):
                        bool_arr[index] = True
                    elif not numpy.isnat(self.nones.datetime64):
                        if val==self.nones.datetime64:
                            bool_arr[index] = True

    @staticmethod
    def _iterable(variable,null):

        null = float(null)

        iterable = []

        for value in flatten(variable):

            try:
                value = float(value)
            except TypeError:
                value = null
            except ValueError:
                value = null

            iterable.append(value)

        return iterable

    def _arange(*args,size=None,dtype=None):

        if len(args)==0:
            return
        elif len(args)==1:
            _array = array1d(args[0],size)

        if dtype is None:
            return _array
        else:
            return _array.astype(dtype)

def float2int(value,default=None):
    """Returns integer converted from float value.
    If there is a ValueError it returns default value."""

    try:
        value = int(value)
    except ValueError:
        value = default

    return value