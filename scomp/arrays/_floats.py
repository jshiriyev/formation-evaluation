import numpy

class floats(numpy.ndarray): # HOW TO BEHAVE LIKE NUMPY ARRAY WHILE CORRECTLY FUNCTIONING WITH DIFFERET NAN

    def __init__(self,vals,none=None):

        if none is None:
            self._none = float('nan')
        elif isinstance(none,float):
            self._none = none
        else:
            raise TypeError("none must be float type!")

        self._setvals(vals)

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

    def _iterable(self,vals):

        _vals = []

        for _val in flatten(vals):

            try:
                val = float(_val)
            except ValueError:
                val = self._none

            _vals.append(val)

        self._vals = _vals

    def _arange(*args,size=None,dtype=None):

        if len(args)==0:
            return
        elif len(args)==1:
            _array = array1d(args[0],size)

        if dtype is None:
            return _array
        else:
            return _array.astype(dtype)