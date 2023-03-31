import re

import numpy

import pint

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
        """Console representation of column."""

        # return f'floats(head="{self.head}", unit="{self.unit}", info="{self.info}", vals={self._valstr(2)})'

        parent = super().__repr__()

        child = parent.replace('nan','null')

        return re.sub(r"\s+"," ",child)

    def __str__(self):
        """Print representation of column."""

        # text = "{}\n"*4

        # head = f"head\t: {self.head}"
        # unit = f"unit\t: {self.unit}"
        # info = f"info\t: {self.info}"
        # vals = f"vals\t: {self._valstr(2)}"

        # return text.format(head,unit,info,vals)

        parent = super().__str__()

        child = parent.replace('nan','null')

        return re.sub(r"\s+"," ",child)

    """COMPARISON"""

    def __lt__(self,other):
        """Implementing '<' operator."""
        
        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            return self.vals<other.vals
        else:
            return self.vals<other

    def __le__(self,other):
        """Implementing '<=' operator."""
        
        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            return self.vals<=other.vals
        else:
            return self.vals<=other

    def __gt__(self,other):
        """Implementing '>' operator."""
        
        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            return self.vals>other.vals
        else:
            return self.vals>other

    def __ge__(self,other):
        """Implementing '>=' operator."""

        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            return self.vals>=other.vals
        else:
            return self.vals>=other

    def __eq__(self,other,tol=1e-12):
        """Implementing '==' operator."""

        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
                return numpy.abs(self.vals-other.vals)<tol*numpy.maximum(numpy.abs(self.vals),numpy.abs(other.vals))
                #numpy.allclose(self.vals,other.vals,rtol=1e-10,atol=1e-10)
            else:
                return self.vals==other.vals
        else:
            return self.vals==other

    def __ne__(self,other,tol=1e-12):
        """Implementing '!=' operator."""
        
        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
                return numpy.abs(self.vals-other.vals)>tol*numpy.maximum(numpy.abs(self.vals),numpy.abs(other.vals))
            else:
                return self.vals!=other.vals
        else:
            return self.vals!=other

    def __bool__(self):

        if self.vals.dtype.type is numpy.object_:
            return self.vals.any()
        elif self.vals.dtype.type is numpy.int32:
            return self.vals.any()
        elif self.vals.dtype.type is numpy.float64:
            return not numpy.all(numpy.isnan(self.vals))
        elif self.vals.dtype.type is numpy.str_:
            return self.vals.any()
        elif self.vals.dtype.type is numpy.datetime64:
            return not numpy.all(numpy.isnat(self.vals))

    """MATHEMATICAL OPERATIONS"""

    def __add__(self,other):
        """Implementing '+' operator."""

        if curnt.dtype.type is numpy.dtype('int').type:
            if not other.dtype.type is numpy.dtype('int').type:
                other = other.astype('int')
            curnt.vals += other.vals
        elif curnt.dtype.type is numpy.dtype('float').type:
            if not other.dtype.type is numpy.dtype('float').type:
                other = other.astype('float')
            other = other.convert(curnt.unit)
            curnt.vals += other.vals
        elif curnt.dtype.type is numpy.dtype('str').type:
            if not other.dtype.type is numpy.dtype('str').type:
                other = other.astype('str')
            curnt.vals = numpy.char.add(curnt.vals,other.vals)
        elif curnt.dtype.type is numpy.dtype('datetime64').type:
            if not other.dtype.type is numpy.dtype('float').type:
                raise TypeError(f"Only floats with delta time unit is supported.")
            elif other.unit=="dimensionless":
                raise TypeError(f"Only floats with delta time unit is supported.")
            else:
                unrg = pint.UnitRegistry()
                unit = unrg.Unit(other.unit).__str__()
                curnt = curnt.shift(other.vals,deltaunit=unit)

        return curnt

    def __floordiv__(self,other):
        """Implementing '//' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
            # ureg = pint.UnitRegistry()
            # unit = ureg.Unit(f"{self.unit}/({other.unit})").__str__()

            if other.nondim and self.nondim:
                unit = "dimensionless"
            elif not other.nondim and self.nondim:
                unit = f"1/{other.unit}"
            elif other.nondim and not self.nondim:
                unit = self.unit
            else:
                unit = f"{self.unit}/({other.unit})"

            datacolumn.vals = self.vals//other.vals
            datacolumn._valsunit(unit)

        else:
            datacolumn.vals = self.vals//other
            
        return datacolumn

    def __mod__(self,other):
        """Implementing '%' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
        #     ureg = pint.UnitRegistry()
        #     unit = ureg.Unit(f"{self.unit}/({other.unit})").__str__()
        #     return column(self.vals%other.vals,unit=unit)
            if other.nondim:
                datacolumn.vals = self.vals%other.vals
            else:
                raise TypeError(f"unsupported operand type for dimensional column arrays.")
        else:
            datacolumn.vals = self.vals%other
            
        return datacolumn

    def __mul__(self,other):
        """Implementing '*' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
            # ur = pint.UnitRegistry()
            # unit = ur.Unit(f"{self.unit}*{other.unit}").__str__()

            if other.nondim:
                unit = self.unit
            elif self.nondim:
                unit = other.unit
            else:
                unit = f"{self.unit}*{other.unit}"

            datacolumn.vals = self.vals*other.vals
            datacolumn._valsunit(unit)
        else:
            datacolumn.vals = self.vals*other

        return datacolumn

    def __pow__(self,other):
        """Implementing '**' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,int) or isinstance(other,float):
            # ureg = pint.UnitRegistry()
            # unit = ureg.Unit(f"{self.unit}^{other}").__str__()
            datacolumn.vals = self.vals**other
            datacolumn._valsunit(f"({self.unit})**{other}")
        else:
            raise TypeError(f"unsupported operand type for non-int or non-float entries.")

        return datacolumn

    def __sub__(self,other):
        """Implementing '-' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            datacolumn.vals = self.vals-other.vals
        else:
            datacolumn.vals = self.vals-other
        
        return datacolumn

    def __truediv__(self,other):
        """Implementing '/' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
            # ur = pint.UnitRegistry()
            # unit = ur.Unit(f"{self.unit}/({other.unit})").__str__()

            if other.nondim and self.nondim:
                unit = "dimensionless"
            elif not other.nondim and self.nondim:
                unit = f"1/{other.unit}"
            elif other.nondim and not self.nondim:
                unit = self.unit
            else:
                unit = f"{self.unit}/({other.unit})"

            datacolumn.vals = self.vals/other.vals
            datacolumn._valsunit(unit)
        else:
            datacolumn.vals = self.vals/other
        
        return datacolumn

    def tostr(self):

        if numpy.isnan(self.null):
            return self.astype(str)

        vals = self.view(numpy.ndarray).copy()

        vals[self.isnull] = self.null

        return vals.astype(str)

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

    def convert(self,unit):
        """It converts the vals to the new unit."""

        if self.unit==unit:
            return self

        datacolumn = copy.deepcopy(self)

        if self.dtype.type is not numpy.dtype('float').type:
            datacolumn = datacolumn.astype('float')
        else:
            ureg = pint.UnitRegistry()
            ureg.Quantity(datacolumn.vals,datacolumn.unit).ito(unit)

        datacolumn.unit = unit

        return datacolumn

    def valids(self):

        vals = self.copy()

        return vals[self.isvalid]

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

        return numpy.nanmin(self.view(numpy.ndarray))

    def max(self):

        return numpy.nanmax(self.view(numpy.ndarray))

    def tostring(self,fstring=None,upper=False,lower=False,zfill=None):
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
            
            if fstring is None:
                text = '{:g}'.format(val)
            else:
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