import calendar
import copy
import datetime

from dateutil import parser
from dateutil import relativedelta

import itertools
import logging
import re
import string

import numpy
import pint

if __name__ == "__main__":
    import setup

from cypy.vectorpy import str2int
from cypy.vectorpy import str2float
from cypy.vectorpy import str2str
from cypy.vectorpy import str2datetime64

from cypy.vectorpy import datetime_addyears
from cypy.vectorpy import datetime_addmonths
from cypy.vectorpy import datetime_adddelta

class nones():
    """Base class to manage none values for int, float, str, datetime64."""

    __types = ("int","float","str","datetime64")

    def __init__(self,nint=None,nfloat=None,nstr=None,ndatetime64=None):
        """Initializes all the types with defaults."""

        self.int = -99_999 if nint is None else nint
        self.float = numpy.nan if nfloat is None else nfloat
        self.str = "" if nstr is None else nstr
        self.datetime64 = numpy.datetime64('NaT') if ndatetime64 is None else ndatetime64

    def __str__(self):

        row0 = "None-Values"
        row2 = "{:,d}".format(self.int)
        row3 = "{:,f}".format(self.float)
        row4 = "'{:s}'".format(self.str)
        
        if numpy.isnan(self.datetime64):
            row5 = "{}".format(self.datetime64)
        else:
            row5 = self.datetime64.tolist().strftime("%Y-%b-%d")

        count = len(max((row0,row2,row3,row4,row5),key=len))

        text = ""

        text += "{:>10s}  {:s}\n".format("Data-Types",row0)
        text += "{:>10s}  {:s}\n".format("-"*10,"-"*count)
        text += "{:>10s}  {:s}\n".format("integers",row2)
        text += "{:>10s}  {:s}\n".format("floats",row3)
        text += "{:>10s}  {:s}\n".format("strings",row4)
        text += "{:>10s}  {:s}\n".format("datetime64",row5)

        return text

    def __setattr__(self,dtype,non_value):

        if dtype == "int":
            non_value = int(non_value)
        elif dtype == "float":
            non_value = float(non_value)
        elif dtype == "str":
            non_value = str(non_value)
        elif dtype == "datetime64":
            non_value = numpy.datetime64(non_value)
        else:
            raise KeyError("int, float, str, datetime64 are the attributes to modify.")

        super().__setattr__(dtype,non_value)

    def todict(self,*args):

        nones_dict = {}

        if len(args)==0:
            args = self._nones__types

        for arg in args:
            nones_dict[f'none_{arg}'] = getattr(self,arg)

        return nones_dict

class column():
    """It is a numpy array of shape (N,) with additional attributes of head, unit and info."""

    """INITIALIZATION"""

    def __init__(self,vals,head=None,unit=None,info=None,size=None,dtype=None):
        """Initializes a column with vals of numpy array (N,) and additional attributes."""

        """
        Initialization can be done by sending int, float, str, datetime, numpy as standalone or
        in a list, tuple or numpy.ndarray
        
        The argument "size" is optional and dicates the size of 1 dimensional numpy array.
        The argument "dtype" is optional and can be any type in {int, float, str, datetime64}

        """

        self.nones = nones()

        super().__setattr__("vals",array1d(vals,size))

        self._astype(dtype)
        self._valshead(head)
        self._valsunit(unit)
        self._valsinfo(info)

    def _valsarr(self,vals):
        """Sets the vals of column."""

        super().__setattr__("vals",array1d(vals))

        self._astype()

        self._valsunit()

    def _astype(self,dtype=None):
        """It changes the dtype of the column and alters the None values accordingly."""

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if dtype is None:
            pass
        elif not isinstance(dtype,numpy.dtype):
            raise TypeError(f"dtype must be numpy.dtype, not type={type(dtype)}")
        elif dtype.type is numpy.object_:
            raise TypeError(f"Unsupported numpy.dtype, {dtype=}")
        elif self.dtype==dtype:
            return self

        if dtype is None:
            dtype = self.dtype

        if dtype.type is numpy.dtype('int').type:
            none = self.nones.int
        elif dtype.type is numpy.dtype('float').type:
            none = self.nones.float
        elif dtype.type is numpy.dtype('str').type:
            none = self.nones.str
        elif dtype.type is numpy.dtype('datetime64').type:
            none = self.nones.datetime64
        else:
            raise TypeError(f"Unexpected numpy.dtype, {dtype=}")

        vals_arr = self.vals.astype(numpy.object_)

        try:
            vals_arr[self.isnone] = none
            vals_arr = vals_arr.astype(dtype=dtype)
        except ValueError:
            vals_arr[self.isnone] = self.nones.str
            vals_arr = vals_arr.astype(dtype='str')

        object.__setattr__(self,"vals",vals_arr)

        self._valsunit()

    def _valshead(self,head=None):
        """Sets the head of column."""

        if head is None:
            if hasattr(self,"head"):
                return
            else:
                super().__setattr__("head","HEAD")
        else:
            super().__setattr__("head",re.sub(r"[^\w]","",str(head)))

    def _valsunit(self,unit=None):
        """Sets the unit of column."""

        if self.dtype.type is numpy.dtype('float').type:
            if unit is None:
                if hasattr(self,"unit"):
                    if self.unit is None:
                        super().__setattr__("unit","dimensionless")
                else:
                    super().__setattr__("unit","dimensionless")
            else:
                super().__setattr__("unit",unit)
        elif unit is not None:
            try:
                self.vals = self.vals.astype("float")
            except ValueError:
                logging.critical(f"Only numpy.float64 or float-convertables can have units, not {self.vals.dtype.type}")
            else:
                super().__setattr__("unit",unit)
        else:
            super().__setattr__("unit",None)

    def _valsinfo(self,info=None):
        """Sets the info of column."""

        if info is None:
            if hasattr(self,"info"):
                return
            else:
                super().__setattr__("info"," ")
        else:
            super().__setattr__("info",str(info))

    """REPRESENTATION"""

    def _valstr(self,num=None):
        """It outputs column.vals. If num is not defined it edites numpy.ndarray.__str__()."""

        if num is None:

            vals_str = self.vals.__str__()

            if self.vals.dtype.type is numpy.int32:
                vals_lst = re.findall(r"[-+]?[0-9]+",vals_str)
                vals_str = re.sub(r"[-+]?[0-9]+","{}",vals_str)
            elif self.vals.dtype.type is numpy.float64:
                vals_lst = re.findall(r"[-+]?(?:\d*\.\d+|\d+)",vals_str)
                vals_str = re.sub(r"[-+]?(?:\d*\.\d+|\d+)","{}",vals_str)
            elif self.vals.dtype.type is numpy.str_:
                vals_lst = re.findall(r"\'(.*?)\'",vals_str)
                vals_str = re.sub(r"\'(.*?)\'","\'{}\'",vals_str)
            elif self.vals.dtype.type is numpy.datetime64:
                vals_lst = re.findall(r"\'(.*?)\'",vals_str)
                vals_str = re.sub(r"\'(.*?)\'","\'{}\'",vals_str)

            vals_str = vals_str.replace("[","")
            vals_str = vals_str.replace("]","")

            vals_str = vals_str.strip()

            vals_str = vals_str.replace("\t"," ")
            vals_str = vals_str.replace("\n"," ")

            vals_str = re.sub(' +',',',vals_str)

            vals_str = vals_str.format(*vals_lst)

            return f"[{vals_str}]"

        else:

            if self.vals.size==0:
                part1,part2 = 0,0
                fstring = "[]"
            elif self.vals.size==1:
                part1,part2 = 1,0
                fstring = "[{}]"
            elif self.vals.size==2:
                part1,part2 = 1,1
                fstring = "[{},{}]"
            else:
                part1,part2 = int(numpy.ceil(num/2)),int(numpy.floor(num/2))
                fstring = "[{}...{}]".format("{},"*part1,",{}"*part2)

            if self.vals.dtype.type is numpy.int32:
                vals_str = fstring.format(*["{:d}"]*part1,*["{:d}"]*part2)
            elif self.vals.dtype.type is numpy.float64:
                vals_str = fstring.format(*["{:g}"]*part1,*["{:g}"]*part2)
            elif self.vals.dtype.type is numpy.str_:
                vals_str = fstring.format(*["'{:s}'"]*part1,*["'{:s}'"]*part2)
            elif self.vals.dtype.type is numpy.datetime64:
                vals_str = fstring.format(*["'{}'"]*part1,*["'{}'"]*part2)

            return vals_str.format(*self.vals[:part1],*self.vals[-part2:])

    def __repr__(self):
        """Console representation of column."""

        return f'column(head="{self.head}", unit="{self.unit}", info="{self.info}", vals={self._valstr(2)})'

    def __str__(self):
        """Print representation of column."""

        text = "{}\n"*4

        head = f"head\t: {self.head}"
        unit = f"unit\t: {self.unit}"
        info = f"info\t: {self.info}"
        vals = f"vals\t: {self._valstr(2)}"

        return text.format(head,unit,info,vals)

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

    """ATTRIBUTE ACCESS"""

    def __setattr__(self,name,value):

        if name=="vals":
            self._valsarr(value)
        elif name=="unit":
            self._valsunit(value)
        elif name=="head":
            self._valshead(value)
        elif name=="info":
            self._valsinfo(value)
        else:
            super().__setattr__(name,value)

    """SEARCH METHODS"""

    def min(self):
        """It returns none-minimum value of column."""

        if self.vals.dtype.type is numpy.int32:
            return self.vals[~self.isnone].min()
        elif self.vals.dtype.type is numpy.float64:
            return numpy.nanmin(self.vals)
        elif self.vals.dtype.type is numpy.str_:
            return min(self.vals[~self.isnone],key=len)
        elif self.vals.dtype.type is numpy.datetime64:
            return numpy.nanmin(self.vals)

    def max(self):
        """It returns none-maximum value of column."""

        if self.vals.dtype.type is numpy.int32:
            return self.vals[~self.isnone].max()
        elif self.vals.dtype.type is numpy.float64:
            return numpy.nanmax(self.vals)
        elif self.vals.dtype.type is numpy.str_:
            return max(self.vals[~self.isnone],key=len)
        elif self.vals.dtype.type is numpy.datetime64:
            return numpy.nanmax(self.vals)

    def maxchar(self,return_value=False):
        """It returns the maximum character count in stringified column."""

        if return_value:
            return max(self.vals.astype('str_'),key=len)

        if self.vals.dtype.type is numpy.str_:
            vals = numpy.array(self.vals.tolist())
        else:
            vals = self.tostring().vals

        charsize = numpy.dtype(f"{vals.dtype.char}1").itemsize
        
        return int(vals.dtype.itemsize/charsize)

    """CONTAINER METHODS"""

    def __setitem__(self,key,vals):

        self.vals[key] = vals

    def __delitem__(self,key):

        return numpy.delete(self.vals,key)

    def __iter__(self):

        return iter(self.vals)

    def __len__(self):

        return len(self.vals)

    def __getitem__(self,key):

        column_ = copy.deepcopy(self)

        column_.vals = self.vals[key]

        return column_

    """CONVERSION METHODS"""

    def astype(self,dtype=None):

        col_ = copy.deepcopy(self)

        col_._astype(dtype)

        return col_

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

    def convert(self,unit):
        """It converts the vals to the new unit."""

        if self.unit==unit:
            return self

        column_ = copy.deepcopy(self)

        if self.dtype.type is not numpy.dtype('float').type:
            column_ = column_.astype('float')
        else:
            unrg = pint.UnitRegistry()
            unrg.Quantity(column_.vals,column_.unit).ito(unit)

        column_.unit = unit

        return column_

    def fromstring(self,dtype,regex=None):

        col_ = copy.deepcopy(self)

        # line = re.sub(r"[^\w]","",line) # cleans non-alphanumerics, keeps 0-9, A-Z, a-z, or underscore.

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if dtype.type is numpy.dtype('int').type:
            dnone = self.nones.todict("str","int")
            regex = r"[-+]?\d+\b" if regex is None else regex
            col_.vals = str2int(col_.vals,regex=regex,**dnone)
        elif dtype.type is numpy.dtype('float').type:
            dnone = self.nones.todict("str","float")
            regex = r"[-+]?[0-9]*\.?[0-9]+" if regex is None else regex
            col_.vals = str2float(col_.vals,regex=regex,**dnone)
            col_._valsunit()
        elif dtype.type is numpy.dtype('str').type:
            dnone = self.nones.todict("str")
            col_.vals = str2str(col_.vals,regex=regex,**dnone)
        elif dtype.type is numpy.dtype('datetime64').type:
            dnone = self.nones.todict("str","datetime64")
            col_.vals = str2datetime64(col_.vals,regex=regex,**dnone)
        else:
            raise TypeError("dtype can be either int, float, str or datetime64")

        return col_

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
            
            if isinstance(val,float):
                if fstring is None:
                    text = '{:g}'.format(val)
                else:
                    text = fstring_inner.format(val)
            elif isinstance(val,datetime.datetime):
                if fstring is None:
                    text = val.strftime("%Y-%m-%d || %H:%M:%S")
                else:
                    text = val.strftime(fstring_inner[1:-1])
            elif isinstance(val,datetime.date):
                if fstring is None:
                    text = val.strftime("%Y-%m-%d")
                else:
                    text = val.strftime(fstring_inner[1:-1])
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

        column_ = copy.deepcopy(self)

        column_ = column_.astype("str")

        column_.vals = vals_str

        return column_

    """SHIFTING"""
    
    def shift(self,delta,deltaunit=None):
        """Shifting the entries depending on its dtype."""

        column_ = copy.deepcopy(self)

        if column_.dtype.type is numpy.dtype('int').type:
            delta_ = column(delta,dtype='int')
            vals_shifted = column_.vals+delta_.vals
        elif column_.dtype.type is numpy.dtype('float').type:
            delta_ = column(delta,dtype='float',unit=deltaunit)
            delta_ = delta_.convert(column_.unit)
            vals_shifted = column_.vals+delta_.vals
        elif column_.dtype.type is numpy.dtype('str').type:
            delta_ = any2column(phrases=' ',repeats=delta,dtype='str')
            vals_shifted = numpy.char.add(delta_.vals,column_)
        elif column_.dtype.type is numpy.dtype('datetime64').type:
            vals_shifted = self._add_deltatime(delta,deltaunit)

        column_.vals = vals_shifted

        return column_

    def toeom(self):

        if self.vals.dtype.type is not numpy.datetime64:
            return

        dt = copy.deepcopy(self)

        dt_ = dt[~dt.isnone]

        arr_ = _any2column.arrdatetime64(
            year=dt_.year,month=dt_.month,day=0,dtype=dt.dtype)

        dt[~dt.isnone] = arr_

        return dt

    def tobom(self):

        if self.vals.dtype.type is not numpy.datetime64:
            return

        dt = copy.deepcopy(self)

        dt_ = dt[~dt.isnone]

        arr_ = _any2column.arrdatetime64(
            year=dt_.year,month=dt_.month,day=1,dtype=dt.dtype)

        dt[~dt.isnone] = arr_

        return dt

    """MATHEMATICAL OPERATIONS"""

    def __add__(self,other):
        """Implementing '+' operator."""

        curnt = copy.deepcopy(self)

        if not isinstance(other,column):
            other = column(other)

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

    def _add_deltatime(self,delta,unit=None):

        if unit is None:
            unit = "M"

        if unit == "Y" or unit == "year":
            vals_shifted = datetime_addyears(self.vals,delta)
        elif unit == "M" or unit == "month":
            vals_shifted = datetime_addmonths(self.vals,delta)
        elif unit == "D" or unit == "day":
            vals_shifted = datetime_adddelta(self.vals,days=delta)
        elif unit == "h" or unit == "hour":
            vals_shifted = datetime_adddelta(self.vals,hours=delta)
        elif unit == "m" or unit == "minute":
            vals_shifted = datetime_adddelta(self.vals,minutes=delta)
        elif unit == "s" or unit == "second":
            vals_shifted = datetime_adddelta(self.vals,seconds=delta)
        else:
            raise TypeError("units can be either of Y, M, D, h, m or s.")

        return vals_shifted

    def __floordiv__(self,other):
        """Implementing '//' operator."""

        column_ = copy.deepcopy(self)

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

            column_.vals = self.vals//other.vals
            column_._valsunit(unit)

        else:
            column_.vals = self.vals//other
            
        return column_

    def __mod__(self,other):
        """Implementing '%' operator."""

        column_ = copy.deepcopy(self)

        if isinstance(other,column):
        #     ureg = pint.UnitRegistry()
        #     unit = ureg.Unit(f"{self.unit}/({other.unit})").__str__()
        #     return column(self.vals%other.vals,unit=unit)
            if other.nondim:
                column_.vals = self.vals%other.vals
            else:
                raise TypeError(f"unsupported operand type for dimensional column arrays.")
        else:
            column_.vals = self.vals%other
            
        return column_

    def __mul__(self,other):
        """Implementing '*' operator."""

        column_ = copy.deepcopy(self)

        if isinstance(other,column):
            # ur = pint.UnitRegistry()
            # unit = ur.Unit(f"{self.unit}*{other.unit}").__str__()

            if other.nondim:
                unit = self.unit
            elif self.nondim:
                unit = other.unit
            else:
                unit = f"{self.unit}*{other.unit}"

            column_.vals = self.vals*other.vals
            column_._valsunit(unit)
        else:
            column_.vals = self.vals*other

        return column_

    def __pow__(self,other):
        """Implementing '**' operator."""

        column_ = copy.deepcopy(self)

        if isinstance(other,int) or isinstance(other,float):
            # ureg = pint.UnitRegistry()
            # unit = ureg.Unit(f"{self.unit}^{other}").__str__()
            column_.vals = self.vals**other
            column_._valsunit(f"({self.unit})**{other}")
        else:
            raise TypeError(f"unsupported operand type for non-int or non-float entries.")

        return column_

    def __sub__(self,other):
        """Implementing '-' operator."""

        column_ = copy.deepcopy(self)

        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            column_.vals = self.vals-other.vals
        else:
            column_.vals = self.vals-other
        
        return column_

    def __truediv__(self,other):
        """Implementing '/' operator."""

        column_ = copy.deepcopy(self)

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

            column_.vals = self.vals/other.vals
            column_._valsunit(unit)
        else:
            column_.vals = self.vals/other
        
        return column_

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
            # match = numpy.any(col_.vals==kywrd,axis=0)
        elif regex is not None:
            pttrn = re.compile(regex)
            match = [index for index,val in enumerate(self.vals) if pttrn.match(val)]
            # numpy way of doing the same thing:
            # vectr = numpy.vectorize(lambda x: bool(re.compile(regex).match(x)))
            # match = vectr(col_.vals)

        if return_indices:
            return match
        else:
            return self[match]

    def flip(self):

        col_ = copy.deepcopy(self)

        col_.vals = numpy.flip(self.vals)

        return col_
            
    def unique(self):

        col_ = copy.deepcopy(self)

        col_.vals = numpy.unique(self.vals)

        return col_

    """APPENDING"""

    def append(self,other):

        if not isinstance(other,column):
            other = column(other)

        if self.dtype.type is numpy.dtype('int').type:
            if not other.dtype.type is numpy.dtype('int').type:
                other = other.astype('int')
        elif self.dtype.type is numpy.dtype('float').type:
            if not other.dtype.type is numpy.dtype('float').type:
                other = other.astype('float')
            other = other.convert(self.unit)
        elif self.dtype.type is numpy.dtype('str').type:
            if not other.dtype.type is numpy.dtype('str').type:
                other = other.astype('str')
        elif self.dtype.type is numpy.dtype('datetime64').type:
            if not other.dtype.type is numpy.dtype('datetime64').type:
                other = other.astype('datetime64')
                
        arr_ = numpy.append(self.vals,other.vals)
        
        super().__setattr__("vals",arr_)

    """PLOTTING"""

    def histogram(self,axis,logscale=False):

        yaxis = self.vals

        if logscale:
            yaxis = numpy.log10(yaxis[numpy.nonzero(yaxis)[0]])

        if logscale:
            xlabel = "log10(nonzero-{}) [{}]".format(self.info,self.unit)
        else:
            xlabel = "{} [{}]".format(self.info,self.unit)

        axis.hist(yaxis,density=True,bins=30)  # density=False would make counts
        axis.set_ylabel("Probability")
        axis.set_xlabel(xlabel)

        return axis

    """GENERAL PROPERTIES"""

    @property
    def dtype(self):
        """Return dtype of column.vals."""

        if self.vals.dtype.type is numpy.object_:
            array_ = self.vals[~self.isnone]

            if array_.size==0:
                dtype_ = numpy.dtype('float64')
            elif isinstance(array_[0],int):
                dtype_ = numpy.dtype('float64')
            elif isinstance(array_[0],str):
                dtype_ = numpy.dtype('str_')
            elif isinstance(array_[0],datetime.datetime):
                dtype_ = numpy.dtype('datetime64[s]')
            elif isinstance(array_[0],datetime.date):
                dtype_ = numpy.dtype('datetime64[D]')
            else:
                dtype_ = numpy.array([array_[0]]).dtype

        else:
            dtype_ = self.vals.dtype

        return dtype_

    @property
    def size(self):
        """It returns the size of array in the column."""
        return len(self.vals)
    
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

        elif self.dtype.type is numpy.dtype("int").type:
            bool_arr = self.vals==self.nones.int

        elif self.dtype.type is numpy.dtype("float").type:
            bool_arr = numpy.isnan(self.vals)
            if not numpy.isnan(self.nones.float):
                bool_arr = numpy.logical_or(bool_arr,self.vals==self.nones.float)

        elif self.dtype.type is numpy.dtype("str").type:
            bool_arr = self.vals == self.nones.str

        elif self.dtype.type is numpy.dtype("datetime64").type:
            bool_arr = numpy.isnat(self.vals)
            if not numpy.isnat(self.nones.datetime64):
                bool_arr = numpy.logical_or(bool_arr,self.vals==self.nones.datetime64)

        else:
            raise TypeError(f"Unidentified problem with column dtype={self.vals.dtype.type}")

        return bool_arr

    @property
    def nondim(self):
        """It checks whether column has unit or not."""

        if self.vals.dtype.type is numpy.float64:
            return self.unit=="dimensionless"
        else:
            return True
    
    """DATE-TIME PROPERTIES"""

    @property
    def year(self):
        """It returns the year in the given datetime64 array."""

        if self.vals.dtype.type is not numpy.datetime64:
            return

        year_arr = numpy.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):
            if dt is None:
                year_arr[index] = self.nones.int
            else:
                year_arr[index] = dt.year

        return year_arr

    @property
    def month(self):
        """It returns the month in the given datetime64 array."""

        if self.vals.dtype.type is not numpy.datetime64:
            return

        month_arr = numpy.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):
            if dt is None:
                month_arr[index] = self.nones.int
            else:
                month_arr[index] = dt.month

        return month_arr

    @property
    def monthrange(self):
        """It returns the day count in the month in the datetime64 array."""

        if self.vals.dtype.type is not numpy.datetime64:
            return

        days_arr = numpy.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):
            if dt is None:
                days_arr[index] = self.nones.int
            else:
                days_arr[index] = calendar.monthrange(dt.year,dt.month)[1]

        return days_arr

    @property
    def nextmonthrange(self):
        """It returns the day count in the next month in the datetime array."""

        if self.vals.dtype.type is not numpy.datetime64:
            return

        days_arr = numpy.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):

            if dt is None:
                days_arr[index] = self.nones.int
            else:
                dt += relativedelta.relativedelta(months=1)
                days_arr[index] = calendar.monthrange(dt.year,dt.month)[1]

        return days_arr

    @property
    def prevmonthrange(self):
        """It returns the day count in the next month in the datetime array."""

        if self.vals.dtype.type is not numpy.datetime64:
            return

        days_arr = numpy.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):

            if dt is None:
                days_arr[index] = self.nones.int
            else:
                dt -= relativedelta.relativedelta(months=1)
                days_arr[index] = calendar.monthrange(dt.year,dt.month)[1]

        return days_arr

    @property
    def day(self):
        """It returns the day in the given datetime64 array."""

        if self.vals.dtype.type is not numpy.datetime64:
            return

        day_arr = numpy.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):
            if dt is None:
                day_arr[index] = self.nones.int
            else:
                day_arr[index] = dt.day

        return day_arr

class frame():
    """It stores equal-size one-dimensional numpy arrays in a list."""

    """INITIALIZATION"""
    def __init__(self,*args,**kwargs):
        """Initializes frame with headers & running and parent class DirBase."""

        super().__setattr__("running",[])

        self._setup(*args)

        for key,vals in kwargs.items():
            self.__setitem__(key,vals)

    def _setup(self,*args):

        for arg in args:

            if type(arg) is not column:
                raise TypeError(f"Argument/s need/s to be column type only!")

            if self.shape[1]!=0 and self.shape[0]!=arg.size:
                raise ValueError(f"Attached column size is not the same as of dataframe.")

            if arg.head in self.heads:
                self.running[self._index(arg.head)[0]] = arg
            else:
                self.running.append(arg)

    def _append(self,*args):

        if len(args)==0: return
        elif len(set([len(arg) for arg in args]))!=1:
            raise ValueError("columns have variable lenghts.")

        if self.shape[1]==0:
            self._setup(*args)
        elif self.shape[1]!=len(args):
            raise ValueError("Number of columns does not match columns in dataframe.")
        else:
            [col_.append(arg_) for col_,arg_ in zip(self.running,args)]

    """REPRESENTATION"""
    def __str__(self):
        """It prints to the console limited number of rows with headers."""

        print_limit = 20

        print_limit = int(print_limit)

        upper = int(numpy.ceil(print_limit/2))
        lower = int(numpy.floor(print_limit/2))

        if self.shape[0]>print_limit:
            rows = list(range(upper))
            rows.extend(list(range(-lower,0,1)))
        else:
            rows = list(range(self.shape[0]))

        frame_ = self[rows]

        headcount = [len(head) for head in frame_.heads]
        bodycount = [col_.maxchar() for col_ in frame_.running]
        charcount = [max(hc,bc) for (hc,bc) in zip(headcount,bodycount)]

        # print(headcount,bodycount,charcount)

        fstring = " ".join(["{{:>{}s}}".format(cc) for cc in charcount])
        fstring = "{}\n".format(fstring)

        heads_str = fstring.format(*frame_.heads)
        lines_str = fstring.format(*["-"*count for count in charcount])
        large_str = fstring.format(*[".." for _ in charcount])

        vprint = numpy.vectorize(lambda *args: fstring.format(*args))

        bodycols = vprint(*[col_.tostring() for col_ in frame_.running]).tolist()

        if self.shape[0]>print_limit:
            [bodycols.insert(upper,large_str) for _ in range(3)]

        string = ""
        string += heads_str
        string += lines_str
        string += "".join(bodycols)

        return string

    """ATTRIBUTE ACCESS"""

    def __setattr__(self,key,vals):

        raise AttributeError(f"'frame' object has no attribute '{key}'.")

    """CONTAINER METHODS"""

    def pop(self,key):

        return self.running.pop(self._index(key)[0])

    def _index(self,*args):

        if len(args)==0:
            raise TypeError(f"Index expected at least 1 argument, got 0")

        if any([type(key) is not str for key in args]):
            raise TypeError(f"argument/s must be string!")

        if any([key not in self.heads for key in args]):
            raise ValueError(f"The dataframe does not have key specified in {args}.")

        return tuple([self.heads.index(key) for key in args])

    def __setitem__(self,key,vals):

        if not isinstance(key,str):
            raise TypeError(f"The key can be str, not type={type(key)}.")

        column_ = column(vals,head=key)

        self._setup(column_)

    def __delitem__(self,key):

        if isinstance(key,str):
            self.pop(key)
            return

        if isinstance(key,list) or isinstance(key,tuple):

            if all([type(_key) is str for _key in key]):
                [self.pop(_key) for _key in key]
                return
            elif any([type(_key) is str for _key in key]):
                raise ValueError("Arguments can not contain non-string and string entries together.")
        
        dataframe_ = copy.deepcopy(self)
        object.__setattr__(dataframe_,'running',
            [numpy.delete(col_,key) for col_ in self.running])

        return dataframe_
        
    def __iter__(self):

        return iter([row for row in zip(*self.running)])

    def __len__(self):

        return self.shape[0]

    def __getitem__(self,key):

        if isinstance(key,str):
            return self.running[self._index(key)[0]]

        if isinstance(key,list) or isinstance(key,tuple):

            if all([type(_key) is str for _key in key]):

                running_ = [self.running[i] for i in self._index(*key)]

                dataframe_ = copy.deepcopy(self)

                object.__setattr__(dataframe_,'running',running_)

                return dataframe_

            elif any([type(_key) is str for _key in key]):
                
                raise ValueError("Arguments can not contain non-string and string entries together.")
        
        running_ = [col_[key] for col_ in self.running]

        dataframe_ = copy.deepcopy(self)

        object.__setattr__(dataframe_,'running',running_)

        return dataframe_

    """CONVERSION METHODS"""

    def str2col(self,key=None,delimiter=None,maxsplit=None):
        """Breaks the column into new columns by splitting based on delimiter and maxsplit."""

        idcol_ = self._index(key)[0]

        col_ = self.pop(key)

        if maxsplit is None:
            maxsplit = numpy.char.count(col_,delimiter).max()

        heads = ["{}_{}".format(col_.head,index) for index in range(maxsplit+1)]

        running = []

        for index,string in enumerate(col_.vals):

            row = string.split(delimiter,maxsplit=maxsplit)

            if maxsplit+1>len(row):
                [row.append(col_.nones.str) for _ in range(maxsplit+1-len(row))]

            running.append(row)

        running = numpy.array(running,dtype=str).T

        for index,(vals,head) in enumerate(zip(running,heads),start=idcol_):
            col_new = col_[:]
            col_new.vals = vals
            col_new.head = head
            self.running.insert(index,col_new)

    def col2str(self,heads=None,headnew=None,fstring=None):

        if heads is None:
            heads = self.heads

        arr_ = [self[head].vals for head in heads]

        if fstring is None:
            fstring = ("{} "*len(arr_))[:-1]

        vprint = numpy.vectorize(lambda *args: fstring.format(*args))

        arrnew = vprint(*arr_)

        if headnew is None:
            fstring = ("{}_"*len(arr_))[:-1]
            headnew = fstring.format(*heads)

        return column(arrnew,head=headnew)

    def tostruct(self):
        """Returns numpy structure of dataframe."""

        dtype_str_ = [col_.vals.dtype.str for col_ in self.running]

        dtypes_ = [dtype_ for dtype_ in zip(self.heads,dtype_str_)]

        return numpy.array([row for row in self],dtypes_)

    """ADVANCED METHODS"""
            
    def sort(self,heads,reverse=False,return_indices=False):
        """Returns sorted dataframe."""

        if not (isinstance(heads,list) or isinstance(heads,tuple)):
            raise TypeError("heads must be list or tuple.")

        running_ = self[heads]

        match = numpy.argsort(running_.tostruct(),axis=0,order=heads)

        if reverse:
            match = numpy.flip(match)

        if return_indices:
            return match
        else:
            dataframe_ = copy.deepcopy(self)
            running_ = [col_[match] for col_ in self.running]
            object.__setattr__(dataframe_,'running',running_)
            return dataframe_

    def flip(self):

        dataframe_ = copy.deepcopy(self)

        running_ = [col_.flip() for col_ in self.running]

        object.__setattr__(dataframe_,'running',running_)

    def filter(self,key,keywords=None,regex=None,return_indices=False):
        """Returns filtered dataframe based on keywords or regex."""

        col_ = self[key]

        match = col_.filter(keywords,regex,return_indices=True)

        if return_indices:
            return match
        else:
            dataframe_ = copy.deepcopy(self)
            object.__setattr__(dataframe_,'running',
                [col_[match] for col_ in self.running])
            return dataframe_

    def unique(self,heads):
        """Returns dataframe with unique entries of column/s.
        The number of columns will be equal to the length of heads."""

        if not (isinstance(heads,list) or isinstance(heads,tuple)):
            raise TypeError("heads must be list or tuple.")

        df = self[heads]

        npstruct = df.tostruct()

        npstruct = numpy.unique(npstruct,axis=0)

        dataframe_ = copy.deepcopy(self)

        object.__setattr__(dataframe_,'running',[])

        for head in heads:

            col_ = copy.deepcopy(self[head])

            col_.vals = npstruct[head]

            dataframe_.running.append(col_)

        return dataframe_

    """PROPERTY METHODS"""

    @property
    def shape(self):

        if len(self.running)>0:
            return (max([len(col_) for col_ in self.running]),len(self.running))
        else:
            return (0,0)

    @property
    def dtypes(self):

        return [col_.vals.dtype for col_ in self.running]

    @property
    def types(self):

        return [col_.vals.dtype.type for col_ in self.running]

    @property
    def heads(self):

        return [col_.head for col_ in self.running]

    @property
    def units(self):

        return [col_.unit for col_ in self.running]

    @property
    def infos(self):

        return [col_.info for col_ in self.running]

def array1d(arg,size=None):

    if type(arg).__module__=="numpy":
        arr_ = arg.flatten()
    elif type(arg) is str:
        arr_ = numpy.array([arg])
    elif hasattr(arg,"__iter__"):
        arr_ = numpy.array(list(arg))
    else:
        arr_ = numpy.array([arg])

    if arr_.dtype.type is numpy.object_:
        arr_temp = arr_[arr_!=None]

        if arr_temp.size==0:
            dtype_ = numpy.dtype('float64')
        elif isinstance(arr_temp[0],int):
            dtype_ = numpy.dtype('float64')
        elif isinstance(arr_temp[0],str):
            dtype_ = numpy.dtype('str_')
        elif isinstance(arr_temp[0],datetime.datetime):
            dtype_ = numpy.dtype('datetime64[s]')
        elif isinstance(arr_temp[0],datetime.date):
            dtype_ = numpy.dtype('datetime64[D]')
        else:
            dtype_ = numpy.array([arr_temp[0]]).dtype

        try:
            arr_ = arr_.astype(dtype_)
        except ValueError:
            arr_ = arr_.astype('str_')

    if size is None or arr_.size==0:
        return arr_

    rep_ = int(numpy.ceil(size/arr_.size))

    arr_ = numpy.tile(arr_,rep_)[:size]

    return arr_

def any2column(*args,**kwargs):
    """Sets the vals of column."""

    try:
        head = kwargs.pop('head')
    except KeyError:
        head = None

    try:
        unit = kwargs.pop('unit')
    except KeyError:
        unit = None

    try:
        info = kwargs.pop('info')
    except KeyError:
        info = None

    dtype = kwargs.get('dtype')

    if dtype is None:
        dtype = _any2column.get_dtype(args)
    elif isinstance(dtype,str):
        dtype = numpy.dtype(dtype)

    if dtype.type is numpy.object_:
        pass
    elif dtype.type is numpy.dtype('int').type:    
        arr_ = _any2column.arrint(*args,**kwargs)
    elif dtype.type is numpy.dtype('float').type:
        arr_ = _any2column.arrfloat(*args,**kwargs)
    elif dtype.type is numpy.dtype('str').type:
        arr_ = _any2column.arrstr(*args,**kwargs)
    elif dtype.type is numpy.dtype('datetime64').type:
        arr_ = _any2column.arrdatetime64(*args,**kwargs)
    else:
        raise ValueError(f"dtype.type is not int, float, str or datetime64, given {dtype.type=}")

    return column(arr_,head=head,unit=unit,info=info,dtype=dtype)

def key2column(*args,**kwargs):
    "Generating column by defining dtype and sending the keywords for array creating methods."

    head = kwargs.get('head')
    unit = kwargs.get('unit')
    info = kwargs.get('info')

    [kwargs.pop(item) for item in ('head','unit','info') if kwargs.get(item) is not None]

    dtype = kwargs.get('dtype')

    if dtype is None:
        dtype = _key2column.get_dtype(args)
    elif isinstance(dtype,str):
        dtype = numpy.dtype(dtype)

    if dtype.type is numpy.dtype('int').type:    
        arr_ = _key2column.arrint(*args,**kwargs)
    elif dtype.type is numpy.dtype('float').type:
        arr_ = _key2column.arrfloat(*args,**kwargs)
    elif dtype.type is numpy.dtype('str').type:
        arr_ = _key2column.arrstr(*args,**kwargs)
    elif dtype.type is numpy.dtype('datetime64').type:
        arr_ = _key2column.arrdatetime64(*args,**kwargs)
    else:
        raise ValueError(f"dtype.type is not int, float, str or datetime64, given {dtype.type=}")

    return column(arr_,head=head,unit=unit,info=info,dtype=dtype)

class _any2column:

    def get_dtype(args):

        if len(args)==0:
            return

        arg = args[0]

        arg = array1d(arg)

        return arg.dtype

    def toiterator(*args,size=None):

        arrs = [array1d(arg) for arg in args]

        if size is None:
            size = len(max(arrs,key=len))

        for index,arr_ in enumerate(arrs):
            rep_ = int(numpy.ceil(size/arr_.size))
            arrs[index] = numpy.tile(arr_,rep_)[:size]

        return zip(*arrs)

    def arrint(*args,size=None,dtype=None):

        if len(args)==0:
            return
        elif len(args)==1:
            arr_ = array1d(args[0],size)

        if dtype is None:
            return arr_
        else:
            return arr_.astype(dtype)

    def arrfloat(*args,size=None,dtype=None):

        if len(args)==0:
            return
        elif len(args)==1:
            arr_ = array1d(args[0],size)

        if dtype is None:
            return arr_
        else:
            return arr_.astype(dtype)

    def arrstr(*args,phrases=None,repeats=None,size=None,dtype=None):

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if len(args)==0:
            if phrases is None:
                phrases = " "
            if repeats is None:
                repeats = 1

            iter_ = _any2column.toiterator(phrases,repeats,size=size)

            arr_ = numpy.array(["".join([name]*num) for name,num in iter_])

        elif len(args)==1:
            arr_ = array1d(args[0],size)
        else:
            raise TypeError("Number of arguments can not be larger than 1!")

        if dtype is None:
            return arr_
        else:
            return arr_.astype(dtype)

    def arrdatetime64(*args,year=2000,month=1,day=-1,hour=0,minute=0,second=0,size=None,dtype=None):

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if len(args)==0:

            items = [year,month,day,hour,minute,second]

            iter_ = _any2column.toiterator(*items,size=size)

            if dtype is None:
                dtype = numpy.dtype(f"datetime64[s]")

            arr_date = []

            for row in iter_:
                arguments = list(row)
                if arguments[2]<=0:
                    arguments[2] += calendar.monthrange(*arguments[:2])[1]
                if arguments[2]<=0:
                    arguments[2] = 1
                arr_date.append(datetime.datetime(*arguments))

            return numpy.array(arr_date,dtype=dtype)

        elif len(args)==1:

            arr_ = array1d(args[0],size)

            if dtype is None:
                return arr_
            
            try:
                return arr_.astype(dtype)
            except ValueError:
                arr_date = [parser.parse(dt) for dt in arr_]
                return numpy.array(arr_date,dtype=dtype)

class _key2column:

    def get_dtype(args):

        if len(args)==0:
            return

        arg = args[0]

        if arg is None:
            return
        elif type(arg) is int:
            return numpy.dtype(type(arg))
        elif type(arg) is float:
            return numpy.dtype(type(arg))
        elif type(arg) is str:
            arg = _key2column.todatetime(arg)
            if arg is None:
                return numpy.str_(arg).dtype
            else:
                return numpy.dtype('datetime64[s]')
        elif type(arg) is datetime.datetime:
            return numpy.dtype('datetime64[s]')
        elif type(arg) is datetime.date:
            return numpy.dtype('datetime64[D]')
        elif type(arg) is numpy.datetime64:
            return arg.dtype
        else:
            return

    def todatetime(var_):

        if var_ is None:
            return
        elif isinstance(var_,str):
            if var_=="now":
                datetime_ = datetime.datetime.today()
            elif var_=="today":
                datetime_ = datetime.date.today()
            elif var_=="yesterday":
                datetime_ = datetime.date.today()+relativedelta.relativedelta(days=-1)
            elif var_=="tomorrow":
                datetime_ = datetime.date.today()+relativedelta.relativedelta(days=+1)
            else:
                try:
                    datetime_ = parser.parse(var_)
                except parser.ParserError:
                    datetime_ = None
        elif isinstance(var_,numpy.datetime64):
            datetime_ = var_.tolist()
        elif type(var_).__module__=="datetime":
            datetime_ = var_
        else:
            return

        if isinstance(datetime_,datetime.datetime):
            return datetime_
        elif isinstance(datetime_,datetime.date):
            return datetime.datetime.combine(datetime_,datetime.datetime.min.time())

    def arrint(*args,start=0,stop=None,step=1,size=None,dtype=None):

        if len(args)==0:
            pass
        elif len(args)==1:
            stop, = args
        elif len(args)==2:
            start,stop = args
        elif len(args)==3:
            start,stop,size = args
        elif len(args)==4:
            start,stop,size,dtype = args
        else:
            raise TypeError("Arguments are too many!")

        if dtype is None:
            dtype = numpy.dtype('int32')
        elif isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if size is None:
            if stop is None:
                raise ValueError("stop value must be provided!")
            return numpy.arange(start,stop,step,dtype=dtype)
        else:
            if stop is None:
                stop = start+size*step
            return numpy.linspace(start,stop,size,endpoint=False,dtype=dtype)

    def arrfloat(*args,start=0.,stop=None,step=1.,size=None,dtype=None,unit='dimensionless',step_unit='dimensionless'):

        if len(args)==0:
            pass
        elif len(args)==1:
            stop, = args
        elif len(args)==2:
            start,stop = args
        elif len(args)==3:
            start,stop,size = args
        elif len(args)==4:
            start,stop,size,dtype = args
        else:
            raise TypeError("Arguments are too many!")

        if unit!=step_unit:
            unrg = pint.UnitRegistry()
            step = unrg.Quantity(step,step_unit).to(unit).magnitude

        if dtype is None:
            dtype = numpy.dtype('float64')
        elif isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if size is None:
            if stop is None:
                raise ValueError("stop value must be provided!")
            return numpy.arange(start,stop,step,dtype=dtype)
        else:
            if stop is None:
                stop = start+size*step
            return numpy.linspace(start,stop,size,dtype=dtype)

    def arrstr(*args,start='A',stop=None,step=1,size=None,dtype=None):

        if len(args)==0:
            pass
        elif len(args)==1:
            stop, = args
        elif len(args)==2:
            start,stop = args
        elif len(args)==3:
            start,stop,size = args
        elif len(args)==4:
            start,stop,size,dtype = args
        else:
            raise TypeError("Arguments are too many!")

        if start is not None:
            if len(start)>5:
                raise TypeError(f'tried excel like letters and failed because of size of start {len(start)}!')
            elif not all([char in string.ascii_letters for char in start]):
                raise TypeError(f'tried excel like letters and failed because of {start=}!')
            start = start.upper()

        if stop is not None:
            if len(stop)>5:
                raise TypeError(f'tried excel like letters and failed because of size of stop {len(stop)}!')  
            elif not all([char in string.ascii_letters for char in stop]):
                raise TypeError(f'tried excel like letters and failed because of {stop=}!!')
            stop = stop.upper()

        if size is not None:
            if size>1000_000:
                raise TypeError(f'tried excel like letters and failed because of {size=}!')

        if isinstance(dtype,str):
            dtype = numpy.dtype(str)

        def excel_column_headers():
            n = 1
            while True:
                yield from (
                    ''.join(group) for group in itertools.product(
                        string.ascii_uppercase,repeat=n
                        )
                    )
                n += 1

        for start_index,combo in enumerate(excel_column_headers()):
            if start==combo:
                break

        if size is None:
            if stop is None:
                raise ValueError("stop value must be provided!")
            for stop_index,combo in enumerate(excel_column_headers(),start=1):
                if stop==combo:
                    break
            arr_ = numpy.array(list(itertools.islice(excel_column_headers(),stop_index)))[start_index:stop_index]
            arr_ = arr_[::step]
        else:
            arr_ = numpy.array(list(itertools.islice(excel_column_headers(),start_index+size*step)))[start_index:]
            arr_ = arr_[::step]

        if dtype is not None:
            return arr_.astype(dtype)
        else:
            return arr_

    def arrdatetime64(*args,start=None,stop="today",step=1,size=None,dtype=None,step_unit='M'):

        if len(args)==0:
            pass
        elif len(args)==1:
            start, = args
        elif len(args)==2:
            start,stop = args
        elif len(args)==3:
            start,stop,size = args
        elif len(args)==4:
            start,stop,size,dtype = args
        else:
            raise TypeError("Arguments are too many!")

        if dtype is None:
            dtype = numpy.dtype(f"datetime64[s]")
        elif isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        start = _key2column.todatetime(start)
        stop = _key2column.todatetime(stop)

        def datetime_adddays(dtcurr,delta):
            return dtcurr+relativedelta.relativedelta(days=delta)

        def datetime_addhours(dtcurr,delta):
            return dtcurr+relativedelta.relativedelta(hours=delta)

        def datetime_addminutes(dtcurr,delta):
            return dtcurr+relativedelta.relativedelta(minutes=delta)

        def datetime_addseconds(dtcurr,delta):
            return dtcurr+relativedelta.relativedelta(seconds=delta)
        
        if step_unit == "Y":
            func = datetime_addyears
        elif step_unit == "M":
            func = datetime_addmonths
        elif step_unit == "D":
            func = datetime_adddays
        elif step_unit == "h":
            func = datetime_addhours
        elif step_unit == "m":
            func = datetime_addminutes
        elif step_unit == "s":
            func = datetime_addseconds
        else:
            raise ValueError("step_unit can be anything from 'Y','M','D','h','m' or 's'.")

        if size is None:
            if start is None:
                raise ValueError("start value must be provided!")
            date = copy.deepcopy(start)
            arr_date = []
            while date<stop:
                arr_date.append(date)
                date = func(date,step)
            return numpy.array(arr_date,dtype=dtype)
        elif start is None:
            date = copy.deepcopy(stop)
            arr_date = []
            for index in range(size):
                date = func(date,-index*step)
                arr_date.append(date)
            return numpy.flip(numpy.array(arr_date,dtype=dtype))
        else:
            delta_ = stop-start
            delta_us = (delta_.days*86_400+delta_.seconds)*1000_000+delta_.microseconds
            deltas = numpy.linspace(0,delta_us,size)
            date = copy.deepcopy(start)
            arr_date = []
            for delta_us in deltas:
                date += relativedelta.relativedelta(microseconds=delta_us)
                arr_date.append(date)
            return numpy.array(arr_date,dtype=dtype)

class _alphabet():

    aze_cyril_lower = [
        "а","б","ҹ","ч","д","е","я","ф","ҝ","ғ","һ","х","ы","и","ж","к",
        "г","л","м","н","о","ю","п","р","с","ш","т","у","ц","в","й","з"]

    aze_latin_lower = [
        "a","b","c","ç","d","e","ə","f","g","ğ","h","x","ı","i","j","k",
        "q","l","m","n","o","ö","p","r","s","ş","t","u","ü","v","y","z"]

    aze_cyril_upper = [
        "А","Б","Ҹ","Ч","Д","Е","Я","Ф","Ҝ","Ғ","Һ","Х","Ы","И","Ж","К",
        "Г","Л","М","Н","О","Ю","П","Р","С","Ш","Т","У","Ц","В","Й","З"]

    aze_latin_upper = [
        "A","B","C","Ç","D","E","Ə","F","G","Ğ","H","X","I","İ","J","K",
        "Q","L","M","N","O","Ö","P","R","S","Ş","T","U","Ü","V","Y","Z"]

    def __init__(self,text):

        self.text = text

    def convert(self,language="aze",from_="cyril",to="latin"):

        from_lower = getattr(self,f"{language}_{from_}_lower")
        from_upper = getattr(self,f"{language}_{from_}_upper")

        to_lower = getattr(self,f"{language}_{to}_lower")
        to_upper = getattr(self,f"{language}_{to}_upper")

        for from_letter,to_letter in zip(from_lower,to_lower):
            self.text.replace(from_letter,to_letter)

        for from_letter,to_letter in zip(from_upper,to_upper):
            self.text.replace(from_letter,to_letter)

if __name__ == "__main__":

    import unittest

    from tests import core_test

    unittest.main(core_test)

    """
    For numpy.datetime64, the issue with following deltatime units
    has been solved by considering self.vals:

    Y: year,
    M: month,
    
    For numpy.datetime64, following deltatime units
    have no inherent issue:

    W: week,
    D: day,
    h: hour,
    m: minute,
    s: second,
    
    For numpy.datetime64, also include:

    ms: millisecond,
    us: microsecond,
    ns: nanosecond,

    For numpy.datetime64, do not include:

    ps: picosecond,
    fs: femtosecond,
    as: attosecond,
    """