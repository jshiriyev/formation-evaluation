import re

import numpy

class ints(numpy.ndarray):
    """It is a flat subclass of numpy.ndarray that includes null entries.
    If null is not defined or is None, -99_999 is set as sentinel value."""

    def __new__(cls,vals,null=None):
        """
        vals    : flat list
        null    : null integer, default is -99,999
        """

        null = -99_999 if null is None else null

        vals = ints.adopt(vals,null)

        item = numpy.asarray(vals,dtype='int32').view(cls)

        item._null = int(null)

        return item

    def __array_finalize__(self,item):

        if item is None: return

        self._null = getattr(item,'_null',-99_999)

    def __array_ufunc__(self,ufunc,method,*args,out=None,**kwargs):

        trialargs = [] # positional arguments for trial calculations
        superargs = [] # positional arguments for parent class calculations

        for index,arg in enumerate(args):

            if isinstance(arg,ints):
                targ = numpy.array([arg[0]])
                sarg = arg.astype(float)

                if method == "accumulate":
                    sarg[arg.isnull] = ufunc.identity
                elif method in ('reduce','reduceat'):
                    sarg = sarg[arg.isvalid]

            else:
                sarg = numpy.array(arg).flatten()
                targ = numpy.array([sarg[0]])
                
            trialargs.append(targ)
            superargs.append(sarg)

        if out is not None:

            out = list(out)
            
            for index,arg in enumerate(out):

                if isinstance(arg,ints):
                    sarg = arg.astype(float)
                else:
                    sarg = numpy.array(arg).flatten()

                out[index] = sarg

            out = tuple(out)

        temp = super().__array_ufunc__(ufunc,method,*superargs,out=out,**kwargs)

        if not hasattr(temp,"__len__"):
            return temp.tolist()

        if temp.size == 0:
            return ints(temp,null=self.null)

        test = super().__array_ufunc__(ufunc,method,*trialargs,out=None,**kwargs)
        
        test = test.flatten().tolist()[0]

        if isinstance(test,float):
            return temp
        elif isinstance(test,bool):
            return temp

        isnan = numpy.isnan(temp)

        temp[isnan] = self.null

        if isinstance(test,int):

            if method == "outer":
                return temp.astype("int32")

            return ints(temp,null=self.null)

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
            return ints(vals.flatten(),null=self.null)
        else:
            return vals

    def astype(self,dtype):

        if dtype is int:
            return self

        isnull = self.isnull

        vals = self.view(numpy.ndarray).copy()

        vals = vals.astype(dtype)

        if dtype is bool:
            vals[isnull] = False
        elif dtype is float:
            vals[isnull] = numpy.nan

        return vals

    def mean(self):
        """Returns sample mean."""

        vals = self.view(numpy.ndarray).copy()

        vals = vals[self.isvalid]

        return numpy.mean(vals)

    def var(self):
        """Returns sample variance."""

        vals = self.view(numpy.ndarray).copy()

        vals = vals[self.isvalid]

        N = vals.size

        S = numpy.sum(vals)

        return numpy.sum((vals-S/N)**2)/(N-1)

    def argmin(self):

        vals = self.view(numpy.ndarray).copy()

        vals[self.isnull] = vals.max()+1

        return numpy.argmin(vals)

    def argmax(self):

        vals = self.view(numpy.ndarray).copy()

        vals[self.isnull] = vals.min()-1

        return numpy.argmax(vals)

    def ceil(self,digit_count=1):
        """Return the ceil round for the given digit count."""
        tens = 10**digit_count

        vals = self.view(numpy.ndarray).copy()

        vals[self.isvalid] = (vals[self.isvalid]//tens+1)*tens

        return ints(vals,null=self.null)

    def floor(self,digit_count=1):
        """Return the floor round for the given digit count."""

        tens = 10**digit_count

        vals = self.view(numpy.ndarray).copy()

        vals[self.isvalid] = (vals[self.isvalid]//tens)*tens

        return ints(vals,null=self.null)

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

        vals = self.view(numpy.ndarray)

        vals = vals[self.isvalid]

        return numpy.all(vals[:-1]<=vals[1:])

    @staticmethod
    def adopt(vals,null):
        """
        vals    : flat list
        null    : null integer
        """

        null = int(null)

        for index,value in enumerate(vals):

            if isinstance(value,int):
                continue
                
            try: # trying to convert to float
                value = float(value)
            except TypeError: # happens with everything other than real number and str
                value = null
            except ValueError: # happens with str
                value = null
            else: # execute code when there is no error in the try.
                
                try:
                    value = int(value)
                except ValueError: # happens with float("nan"), numpy.nan
                    value = null
                
            vals[index] = value

        return vals

    @staticmethod
    def arange(start=None,stop=None,step=None,size=None):

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