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

    def replace(self,new=None,old=None,method="upper"):
        """It replaces old with new. If old is not defined, it replaces nones.
        If new is not defined, it uses upper or lower values to replace the olds."""

        if old is None:
            conds = self.isnone
        else:
            conds = self.vals == old

        if new is None:

            if method=="upper":
                for index in range(self.vals.size):
                    if conds[index]:
                        self.vals[index] = self.vals[index-1]
            elif method=="lower":
                for index in range(self.vals.size):
                    if conds[index]:
                        self.vals[index] = self.vals[index+1]
        else:
            self.vals[conds] = new

    def min(self):

        vals = self.view(numpy.ndarray).copy()

        return vals[self.isvalid].min()

    def max(self):

        vals = self.view(numpy.ndarray).copy()

        return vals[self.isvalid].max()

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

    """ADVANCED METHODS"""

    def sort(self,reverse=False,return_indices=False):
        
        sort_index = numpy.argsort(self.vals)

        if reverse:
            sort_index = numpy.flip(sort_index)

        if return_indices:
            return sort_index
        else:
            return self[sort_index]

    def filter(self,keywords=None,regex=None,return_indices=False):
        
        if keywords is not None:
            match = [index for index,val in enumerate(self.vals) if val in keywords]
            # numpy way of doing the same thing:
            # kywrd = numpy.array(keywords).reshape((-1,1))
            # match = numpy.any(datacolumn.vals==kywrd,axis=0)
        elif regex is not None:
            pttrn = re.compile(regex)
            match = [index for index,val in enumerate(self.vals) if pttrn.match(val)]
            # numpy way of doing the same thing:
            # vectr = numpy.vectorize(lambda x: bool(re.compile(regex).match(x)))
            # match = vectr(datacolumn.vals)

        if return_indices:
            return match
        else:
            return self[match]

    def flip(self):

        datacolumn = copy.deepcopy(self)

        datacolumn.vals = numpy.flip(self.vals)

        return datacolumn
            
    def unique(self):

        datacolumn = copy.deepcopy(self)

        datacolumn.vals = numpy.unique(self.vals)

        return datacolumn

    def tostrs(self,fstring=None,upper=False,lower=False,zfill=None):
        """It has more capabilities than str2str on the outputting part."""

        if fstring is None:
            fstring_inner = "{}"
            fstring_clean = "{}"
        else:
            fstring_inner = re.search(r"\{(.*?)\}",fstring).group()
            fstring_clean = re.sub(r"\{(.*?)\}","{}",fstring,count=1)

        vals_str = []

        for val,none_bool in zip(self.vals.tolist(),self.isnone):

            if none_bool:
                vals_str.append(self.nones.str)
                continue

            text = fstring_inner.format(val)

            if zfill is not None:
                text = text.zfill(zfill)

            if upper:
                text = text.upper()
            elif lower:
                text = text.lower()

            text = fstring_clean.format(text)

            vals_str.append(text)

        vals_str = numpy.array(vals_str,dtype="str")

        datacolumn = copy.deepcopy(self)

        datacolumn = datacolumn.astype("str")

        datacolumn.vals = vals_str

        return datacolumn

    def tostr(self):

        return self.view(numpy.ndarray).astype(str)

    @property
    def null(self):

        return self._null

    @property
    def isvalid(self):
        """It return numpy bool array True for integer and False for null."""
        return numpy.not_equal(self.view(numpy.ndarray),self.null)
    
    @property
    def isnull(self):
        """It return numpy bool array, True for null and False for integer."""
        return numpy.equal(self.view(numpy.ndarray),self.null)

    @property
    def issorted(self):
        """It returns bool stating whether the array is sorted or not, excluding null entries."""

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
            
            step = 1 if step is None else step
            
            stop = start+step*size

        if step is None:
            if size is None:
                step = 1
            else:
                step = stop/(size-1)

        array = numpy.arange(start=start,stop=stop+step/2,step=step,dtype=int)

        null = -99_999

        while null>start:
            null = null*10-9

        return ints(array,null=null)

if __name__ == "__main__":

    a = ints(["5.c",2,3,4])

    print(a,type(a))

    print(a.mean())

    a = integers([1,2,3,4,5,6,-99_999,"01.,5"],null=-99_999)
    b = np.array([1,2,3,4,5,6,-10000,-10000])

    c = integers([True,False,False])
    d = integers(True)

    x = a.view(np.ndarray).astype('float64')

    # print(a.issorted)
    # print(b)
    # print(a.dtype)
    # print(b.dtype)

    # print(a+b)
    # print(a*b)
    # print(a-b)
    # print(a/b)
    # print(a//b)

    # print(a==-99999)

    # print(None==None)