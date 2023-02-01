import numpy

from ._flatten import flatten

from ._floats import floats
from ._strs import strs

class ints(numpy.ndarray):
    """It is a flat subclass of numpy.ndarray that
    includes not-an-integer (null) entries."""

    def __new__(cls,variable,null=None):

        null = -99_999 if null is None else null

        iterable = ints._iterable(variable,null)

        obj = numpy.asarray(iterable,dtype='int32').view(cls)

        obj._null = int(null)

        return obj

    def __array_finalize__(self,obj):

        if obj is None: return

        self._null = getattr(obj,'_null',-99_999)

    def __array_ufunc__(self,ufunc,method,*args,out=None,**kwargs):

        sargs = [] # positional arguments of parent __array_ufunc__
        idcls = [] # index of ints (cls) type inputs

        for index,arg in enumerate(args):
            if isinstance(arg,ints):
                idcls.append(index)
                sargs.append(arg.view(numpy.ndarray))
            elif arg is None:
                idcls.append(index)
                sargs.append(ints(arg,null=self.null).view(numpy.ndarray))
            else:
                sargs.append(ints(arg,null=self.null).view(numpy.ndarray))

        if out:
            outputs = []
            for output in out:
                if isinstance(output,ints):
                    outputs.append(output.view(numpy.ndarray))
                else:
                    outputs.append(output)

            kwargs['out'] = tuple(outputs)

        valids = numpy.not_equal(sargs[0],self.null)

        for index,sarg in enumerate(sargs[1:],start=1):

            if index in idcls:

                try:
                    null = args[index].null
                except AttributeError:
                    null = self.null

                rights = numpy.not_equal(sargs[index],null)
            
                valids = numpy.logical_and(valids,rights)
            
        temp = super().__array_ufunc__(ufunc,method,*sargs,**kwargs)

        if temp.size == 0:
            temp = ints(temp,null=self.null)
        elif isinstance(temp[0].tolist(),int):
            temp[~valids] = self.null
            temp = ints(temp,null=self.null)
        elif isinstance(temp[0].tolist(),float):
            temp[~valids] = numpy.nan
        elif isinstance(temp[0].tolist(),bool):
            temp[~valids] = False

        return temp

    def __repr__(self):

        nprepr = super().__repr__()

        return nprepr.replace(str(self.null),'null')

    def __str__(self):

        npstr = super().__str__()
        
        return npstr.replace(str(self.null),'null')

    def astype(self):

        pass

    def shift(self,onluqlar):

        pass

    @property
    def null(self):

        return self._null

    @property
    def isvalid(self):
        """It return boolean array True for integer and False for null."""
        return numpy.not_equal(self.view(numpy.ndarray),self.null)
    
    @property
    def isnull(self):
        """It return numpy bool array, True for null and False for integer."""
        return numpy.equal(self.view(numpy.ndarray),self.null)

    @property
    def issorted(self):

        temp = self.view(numpy.ndarray).astype('float64')

        temp = temp[temp!=self.null]

        return numpy.all(temp[:-1]<=temp[1:])

    @staticmethod
    def _iterable(variable,null):

        null = int(null)

        iterable = []

        for value in flatten(variable):

            try:
                value = float(value)
            except TypeError:
                value = null
            except ValueError:
                value = null
            
            try:
                value = int(value)
            except ValueError:
                value = null

            if value == null:
                iterable.append(null)
            else:
                iterable.append(value)

        return iterable

    @staticmethod
    def _arange(start=None,stop=None,step=None,size=None):

        if len(args)==0:
            return
        elif len(args)==1:
            _array = array1d(args[0],size)

        if dtype is None:
            return _array
        else:
            return _array.astype(dtype)

    @staticmethod
    def _repeat(size,method=None):
        """returns numpy array with specified shape"""

        if self.size==0:
            return numpy_array

        repeat_count = int(numpy.ceil(size/numpy_array.size))

        numpy_array = numpy.tile(numpy_array,repeat_count)[:size]

        return numpy_array

    @staticmethod   
    def _astype(dtype):
        """returns numpy array with specified dtype"""

        if self.dtype.type is numpy.object_:

            numpy_array_temp = self.vals[self.vals!=None]

            if numpy_array_temp.size==0:
                dtype = numpy.dtype('float64')
            elif isinstance(numpy_array_temp[0],int):
                dtype = numpy.dtype('float64')
            elif isinstance(numpy_array_temp[0],str):
                dtype = numpy.dtype('str_')
            elif isinstance(numpy_array_temp[0],datetime.datetime):
                dtype = numpy.dtype('datetime64[s]')
            elif isinstance(numpy_array_temp[0],datetime.date):
                dtype = numpy.dtype('datetime64[D]')
            else:
                dtype = numpy.array([numpy_array_temp[0]]).dtype

        try:
            numpy_array = numpy_array.astype(dtype)
        except ValueError:
            numpy_array = numpy_array.astype('str_')

        return numpy_array