import re

import numpy

class floats(numpy.ndarray):
    """It is a flat subclass of numpy.ndarray that includes null entries.
    If null is not defined or is None, float("nan") is set as sentinel value."""

    def __new__(cls,vals,null=None,unit=None):

        null = numpy.nan if null is None else float(null)

        vals = floats.adopt(vals,null)

        item = numpy.asarray(vals,dtype='float64').view(cls)

        item._null = null

        item._unit = unit

        return item

    def __array_finalize__(self,item):

        if item is None: return

        self._null = getattr(item,'_null',numpy.nan)
        self._unit = getattr(item,'_unit',None)

    def __repr__(self):

        parent = super().__repr__()

        child = parent.replace('nan','null')

        return re.sub(r"\s+"," ",child)

    def __str__(self):

        parent = super().__str__()

        child = parent.replace('nan','null')

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

    @staticmethod
    def adopt(vals,null):
        """
        vals    : flat list
        null    : null float
        """

        null = float(null)

        for index,value in enumerate(vals):

            if isinstance(value,float):
                continue
                
            try:
                value = float(value)
            except TypeError:
                value = float("nan")
            except ValueError:
                value = float("nan")

            vals[index] = value

        return vals

    @staticmethod
    def arange(*args,**kwargs):

        size = kwargs.get("size")

        if size is None:
            vals = numpy.arange(*args,*kwargs)
        else:
            vals = numpy.linspace(*args,*kwargs)

        return floats(vals)

if __name__ == "__main__":

    array = floats([1,2,3,4,None,7],null=-99.999)

    print(array)
    print(array+1)

    print(array.valids())

    print(array.min())
    print(array.max())

    print(array.normalize())