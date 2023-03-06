import re

import numpy

from ._flatten import flatten

from ._floats import float2int

class ints(numpy.ndarray):
    """It is a flat subclass of numpy.ndarray that includes null entries.
    If null is not defined or is None, -99_999 is set as sentinel value."""

    def __new__(cls,variable,null=None):

        null = -99_999 if null is None else null

        iterable = ints._iterable(variable,null)

        obj = numpy.asarray(iterable,dtype='int32').view(cls)

        obj._null = int(null)

        return obj

    def __array_finalize__(self,obj):

        if obj is None: return

        self._null = getattr(obj,'_null',-99_999)

    def _resolved_dtypes_(self,ufunc,method,*args):

        dtypes = []

        reduction = False

        if method != '__call__':

            dtypes.append(None)

            reduction = True

        for index,arg in enumerate(args):

            if arg is None:
                dtypes.append(int)

            elif type(arg).__module__ == numpy.__name__:
                dtypes.append(arg.dtype)

            elif isinstance(arg,numpy.ndarray):
                dtypes.append(arg.dtype)

            elif isinstance(arg,str):
                dtypes.append(str)

            elif hasattr(arg,"__iter__"):
                values = numpy.array(arg)
                dtypes.append(values.dtype)

            else:
                dtypes.append(type(arg))

        for _ in range(len(dtypes),ufunc.nargs):

            dtypes.append(None)

        rdtypes = ufunc.resolve_dtypes(tuple(dtypes),reduction=reduction)

        return rdtypes

    def __array_ufunc__(self,ufunc,method,*args,out=None,**kwargs):

        classtype = [] # index of ints type inputs
        superargs = [] # positional arguments for parent class

        # dtypes = self._resolved_dtypes_(ufunc,method,*args)

        for index,arg in enumerate(args):

            if isinstance(arg,ints):
                classtype.append(index)

                sarg = arg.view(numpy.ndarray).copy()

                if ufunc in comparison_operators:
                    superargs.append(sarg.astype(float))
                elif method=="accumulate":
                    sarg[arg.isnull] = ufunc.identity
                    superargs.append(sarg)
                elif method in ('reduce','reduceat'):
                    superargs.append(sarg[arg.isvalid])
                else:
                    superargs.append(arg.view(numpy.ndarray))
            else:

                superargs.append(numpy.array(arg).flatten())

        if out is not None:
            outputs = []
            
            for output in out:
                if isinstance(output,ints):
                    outputs.append(output.view(numpy.ndarray))
                else:
                    outputs.append(output)

            kwargs['out'] = tuple(outputs)

        if ufunc not in comparison_operators:

            valids = numpy.not_equal(superargs[0],self.null)

            for index,superarg in enumerate(superargs[1:],start=1):

                if index in classtype:

                    try:
                        null = args[index].null
                    except AttributeError:
                        null = self.null

                    rights = numpy.not_equal(superarg,null)
                
                    valids = numpy.logical_and(valids,rights)

        temp = super().__array_ufunc__(ufunc,method,*superargs,**kwargs)

        if not hasattr(temp,"__len__"):
            pass
        elif temp.size == 0:
            temp = ints(temp,null=self.null)
        elif isinstance(temp[0].tolist(),bool):
            pass
        elif isinstance(temp[0].tolist(),int):
            temp[~valids] = self.null
            temp = ints(temp,null=self.null)
        elif isinstance(temp[0].tolist(),float):
            temp[~valids] = numpy.nan

        return temp

    def __repr__(self):

        parent = super().__repr__()

        child = parent.replace(str(self.null),'null')

        return re.sub(r"\s+"," ",child)

    def __str__(self):

        parent = super().__str__()

        child = parent.replace(str(self.null),'null')

        return re.sub(r"\s+"," ",child)

    def __setitem__(self,key,value):

        vals = ints(value,null=self.null)

        super().__setitem__(key,vals)

    def __getitem__(self,key):

        vals = super().__getitem__(key)

        if isinstance(key,int):
            return ints(vals,null=self.null)
        else:
            return vals

    def astype(self,dtype):

        if dtype is int:
            return self

        isnull = self.isnull

        variable = self.view(numpy.ndarray)

        variable = variable.astype(dtype)

        if dtype is bool:
            variable[isnull] = False
        elif dtype is float:
            variable[isnull] = numpy.nan

        return variable

    def mean(self):
        """Returns sample mean."""

        variable = self.view(numpy.ndarray).copy()

        variable = variable[self.isvalid]

        return numpy.mean(variable)

    def var(self):
        """Returns sample variance."""

        variable = self.view(numpy.ndarray).copy()

        variable = variable[self.isvalid]

        N = variable.size

        S = numpy.sum(variable)

        return numpy.sum((variable-S/N)**2)/(N-1)

    def argmin(self):

        variable = self.view(numpy.ndarray).copy()

        variable[self.isnull] = variable.max()+1

        return numpy.argmin(variable)

    def argmax(self):

        variable = self.view(numpy.ndarray).copy()

        variable[self.isnull] = variable.min()-1

        return numpy.argmax(variable)

    def ceil(self,digit_count=1):
        """Return the ceil round for the given digit count."""
        tens = 10**digit_count

        variable = self.view(numpy.ndarray)

        variable[self.isvalid] = (variable[self.isvalid]//tens+1)*tens

        return ints(variable,self.null)

    def floor(self,digit_count=1):
        """Return the floor round for the given digit count."""

        tens = 10**digit_count

        variable = self.view(numpy.ndarray)

        variable[self.isvalid] = (variable[self.isvalid]//tens)*tens

        return ints(variable,self.null)

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
        """It returns wether given array is sorted or not, excluding null entries."""

        variable = self.view(numpy.ndarray)

        variable = variable[self.isvalid]

        return numpy.all(variable[:-1]<=variable[1:])

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
            else: # execute code when there is no error.
                value = float2int(value,null)
            
            iterable.append(value)

        return iterable

    @staticmethod
    def _arange(start=None,stop=None,step=None,size=None):

        if start is None:
            start = 0

        if stop is None:
            stop = start+size if step is None else start+step*size

        if step is None:
            step = 1 if size is None else stop/(size-1)

        array = numpy.arange(start=start,stop=stop+step/2,step=step)
        array = array.astype('int32')

        array_min = array.min()

        null = -99_999

        while null>array_min:
            null = null*10-9

        return ints(array,null=null)

    @staticmethod
    def _repeat(variable,size:int):
        """Returns numpy array with specified size."""

        variable = ints(flatten(variable))

        if variable.size==0:
            return variable

        times = int(numpy.ceil(size/variable.size))

        return numpy.tile(variable,times)[:size]

comparison_operators = (
    numpy.equal,
    numpy.not_equal,
    numpy.greater,
    numpy.less,
    numpy.greater_equal,
    numpy.less_equal
)