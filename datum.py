import calendar
import copy
import datetime

from dateutil import parser
from dateutil import relativedelta

import itertools
import logging
import re
import string

from matplotlib import pyplot

import numpy
import pint

if __name__ == "__main__":
    import dirsetup

from cypy.vectorpy import strtype

from cypy.vectorpy import str2int
from cypy.vectorpy import str2float
from cypy.vectorpy import str2str
from cypy.vectorpy import str2datetime64

from cypy.vectorpy import datetime_addyears
from cypy.vectorpy import datetime_addmonths
from cypy.vectorpy import datetime_adddelta

def pop(kwargs,key,default=None):

    try:
        return kwargs.pop(key)
    except KeyError:
        return default

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

class array():
    """It is one dimensional numpy.ndarray with modified methods."""

    def __init__(self,**kwargs):

        if len(kwargs)!=1:
            raise "One optional argument is accepted!"

        head,vals = kwargs.popitem()

        self.head = head

        self._setvals(vals)

    def _setvals(self,vals):

        if type(vals).__module__=="numpy":
            onedimarray = vals.flatten()
        elif isinstance(vals,str):
            onedimarray = numpy.array([vals])
        elif hasattr(vals,"__iter__"):
            onedimarray = numpy.array(list(vals))
        else:
            onedimarray = numpy.array([vals])

        super().__setattr__("vals",onedimarray)

    def __getattr__(self,key):

        return getattr(self.vals,key)

    def __getitem__(self,key):

        return self.vals[key]

class column():# MUST BE RENAMED TO DataColumn AND INITIALIZATION MUST BE SIMPLIFIED TO: head=vals
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

    def maxchar(self,fstring=None,return_value=False):
        """It returns the maximum character count in stringified column."""

        if return_value:
            return max(self.tostring(fstring),key=len) #self.vals.astype('str_')

        if self.vals.dtype.type is numpy.str_:
            vals = numpy.array(self.vals.tolist())
        else:
            vals = self.tostring(fstring).vals

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

        datacolumn = copy.deepcopy(self)

        datacolumn.vals = self.vals[key]

        return datacolumn

    """CONVERSION METHODS"""

    def astype(self,dtype=None):

        datacolumn = copy.deepcopy(self)

        datacolumn._astype(dtype)

        return datacolumn

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

        datacolumn = copy.deepcopy(self)

        if self.dtype.type is not numpy.dtype('float').type:
            datacolumn = datacolumn.astype('float')
        else:
            ureg = pint.UnitRegistry()
            ureg.Quantity(datacolumn.vals,datacolumn.unit).ito(unit)

        datacolumn.unit = unit

        return datacolumn

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

    def fromstring(self,dtype,regex=None):

        datacolumn = copy.deepcopy(self)

        # line = re.sub(r"[^\w]","",line) # cleans non-alphanumerics, keeps 0-9, A-Z, a-z, or underscore.

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if dtype.type is numpy.dtype('int').type:
            dnone = self.nones.todict("str","int")
            regex = r"[-+]?\d+\b" if regex is None else regex
            datacolumn.vals = str2int(datacolumn.vals,regex=regex,**dnone)
        elif dtype.type is numpy.dtype('float').type:
            dnone = self.nones.todict("str","float")
            regex = r"[-+]?[0-9]*\.?[0-9]+" if regex is None else regex
            datacolumn.vals = str2float(datacolumn.vals,regex=regex,**dnone)
            datacolumn._valsunit()
        elif dtype.type is numpy.dtype('str').type:
            dnone = self.nones.todict("str")
            datacolumn.vals = str2str(datacolumn.vals,regex=regex,**dnone)
        elif dtype.type is numpy.dtype('datetime64').type:
            dnone = self.nones.todict("str","datetime64")
            datacolumn.vals = str2datetime64(datacolumn.vals,regex=regex,**dnone)
        else:
            raise TypeError("dtype can be either int, float, str or datetime64")

        return datacolumn

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

        datacolumn = copy.deepcopy(self)

        datacolumn = datacolumn.astype("str")

        datacolumn.vals = vals_str

        return datacolumn

    """SHIFTING"""
    
    def shift(self,delta,deltaunit=None):
        """Shifting the entries depending on its dtype."""

        datacolumn = copy.deepcopy(self)

        if datacolumn.dtype.type is numpy.dtype('int').type:
            delta_column = column(delta,dtype='int')
            vals_shifted = datacolumn.vals+delta_column.vals
        elif datacolumn.dtype.type is numpy.dtype('float').type:
            delta_column = column(delta,dtype='float',unit=deltaunit)
            delta_column = delta_column.convert(datacolumn.unit)
            vals_shifted = datacolumn.vals+delta_column.vals
        elif datacolumn.dtype.type is numpy.dtype('str').type:
            delta_column = any2column(phrases=' ',repeats=delta,dtype='str')
            vals_shifted = numpy.char.add(delta_column.vals,datacolumn)
        elif datacolumn.dtype.type is numpy.dtype('datetime64').type:
            vals_shifted = self._add_deltatime(delta,deltaunit)

        datacolumn.vals = vals_shifted

        return datacolumn

    def toeom(self):

        if self.vals.dtype.type is not numpy.datetime64:
            return

        datacolumn = copy.deepcopy(self)

        not_none = ~datacolumn.isnone

        datacolumnsub = datacolumn[not_none]

        dataarray = _any2column.arrdatetime64(
            year=datacolumnsub.year,month=datacolumnsub.month,day=0,dtype=datacolumnsub.dtype)

        datacolumn[not_none] = dataarray

        return datacolumn

    def tobom(self):

        if self.vals.dtype.type is not numpy.datetime64:
            return

        datacolumn = copy.deepcopy(self)

        not_none = ~datacolumn.isnone

        datacolumnsub = datacolumn[not_none]

        dataarray = _any2column.arrdatetime64(
            year=datacolumnsub.year,month=datacolumnsub.month,day=1,dtype=datacolumnsub.dtype)

        datacolumn[not_none] = dataarray

        return datacolumn

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
                
        dataarray = numpy.append(self.vals,other.vals)
        
        super().__setattr__("vals",dataarray)

    """PLOTTING"""

    def histogram(self,axis,logscale=False):

        show = True if axis is None else False

        if axis is None:
            axis = pyplot.figure().add_subplot()

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

        if show:
            pyplot.show()

    """GENERAL PROPERTIES"""

    @property
    def dtype(self):
        """Return dtype of column.vals."""

        if self.vals.dtype.type is numpy.object_:
            dataarray = self.vals[~self.isnone]

            if dataarray.size==0:
                datatype = numpy.dtype('float64')
            elif isinstance(dataarray[0],int):
                datatype = numpy.dtype('float64')
            elif isinstance(dataarray[0],str):
                datatype = numpy.dtype('str_')
            elif isinstance(dataarray[0],datetime.datetime):
                datatype = numpy.dtype('datetime64[s]')
            elif isinstance(dataarray[0],datetime.date):
                datatype = numpy.dtype('datetime64[D]')
            else:
                datatype = numpy.array([dataarray[0]]).dtype

        else:
            datatype = self.vals.dtype

        return datatype

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
    def issorted(self):

        return numpy.all(self.vals[:-1]<self.vals[1:])
    
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

class frame(): # MUST BE RENAMED TO DataBundle 
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

            if not isinstance(arg,column):
                raise TypeError(f"Argument/s need/s to be column type only!")

            if self.shape[1]!=0 and self.shape[0]!=arg.size:
                raise ValueError(f"Attached column size is not the same as of dataframe.")

            if arg.head in self.heads:
                self.running[self._index(arg.head)[0]] = arg
            else:
                self.running.append(arg)

    def _append(self,*args):

        if len(args)==0:
            return
        elif len(set([len(arg) for arg in args]))!=1:
            raise ValueError("columns have variable lenghts.")

        if self.shape[1]==0:
            self._setup(*args)
        elif self.shape[1]!=len(args):
            raise ValueError("Number of columns does not match columns in dataframe.")
        else:
            [datacolumn.append(arg) for datacolumn,arg in zip(self.running,args)]

    """REPRESENTATION"""

    def __repr__(self):

        return self.__str__(limit=10,comment="")

    def __str__(self,limit:int=20,comment=None,**kwargs):
        """It prints to the console limited number of rows with headers."""

        upper = int(numpy.ceil(limit/2))
        lower = int(numpy.floor(limit/2))

        if self.shape[0]>limit:
            rows = list(range(upper))
            rows.extend(list(range(-lower,0,1)))
        else:
            rows = list(range(self.shape[0]))

        if comment is None:
            comment = ""

        dataframe = copy.deepcopy(self)

        running = [datacolumn.tostring(**kwargs) for datacolumn in dataframe.running]

        object.__setattr__(dataframe,'running',running)

        dataframe = dataframe[rows]

        headcount = [len(head) for head in dataframe.heads]
        bodycount = [datacolumn.maxchar() for datacolumn in dataframe.running]
        charcount = [max(hc,bc) for (hc,bc) in zip(headcount,bodycount)]

        # print(headcount,bodycount,charcount)

        bspaces = " "*len(comment)

        fstring = " ".join(["{{:>{}s}}".format(cc) for cc in charcount])

        fstringH = "{}{}\n".format(comment,fstring)
        fstringB = "{}{}\n".format(bspaces,fstring)

        heads_str = fstringH.format(*dataframe.heads)
        lines_str = fstringH.format(*["-"*count for count in charcount])
        large_str = fstringH.format(*[".." for _ in charcount])

        vprint = numpy.vectorize(lambda *args: fstringB.format(*args))

        bodycols = vprint(*dataframe.running).tolist()

        if self.shape[0]>limit:
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

        datacolumn = column(vals,head=key)

        self._setup(datacolumn)

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
        
        dataframe = copy.deepcopy(self)
        object.__setattr__(dataframe,'running',
            [numpy.delete(datacolumn,key) for datacolumn in self.running])

        return dataframe
        
    def __iter__(self):

        return iter([row for row in zip(*self.running)])

    def __len__(self):

        return self.shape[0]

    def __getitem__(self,key):

        if isinstance(key,str):
            return self.running[self._index(key)[0]]

        if isinstance(key,list) or isinstance(key,tuple):

            if all([type(_key) is str for _key in key]):

                running = [self.running[i] for i in self._index(*key)]

                dataframe = copy.deepcopy(self)

                object.__setattr__(dataframe,'running',running)

                return dataframe

            elif any([type(_key) is str for _key in key]):
                
                raise ValueError("Arguments can not contain non-string and string entries together.")
        
        running = [datacolumn[key] for datacolumn in self.running]

        dataframe = copy.deepcopy(self)

        object.__setattr__(dataframe,'running',running)

        return dataframe

    """CONVERSION METHODS"""

    def str2col(self,key=None,delimiter=None,maxsplit=None):
        """Breaks the column into new columns by splitting based on delimiter and maxsplit."""

        idcolumn = self._index(key)[0]

        datacolumn = self.pop(key)

        if maxsplit is None:
            maxsplit = numpy.char.count(datacolumn,delimiter).max()

        heads = ["{}_{}".format(datacolumn.head,index) for index in range(maxsplit+1)]

        running = []

        for index,string in enumerate(datacolumn.vals):

            row = string.split(delimiter,maxsplit=maxsplit)

            if maxsplit+1>len(row):
                [row.append(datacolumn.nones.str) for _ in range(maxsplit+1-len(row))]

            running.append(row)

        running = numpy.array(running,dtype=str).T

        for index,(vals,head) in enumerate(zip(running,heads),start=idcolumn):
            datacolumn_new = datacolumn[:]
            datacolumn_new.vals = vals
            datacolumn_new.head = head
            self.running.insert(index,datacolumn_new)

    def col2str(self,heads=None,headnew=None,fstring=None):

        if heads is None:
            heads = self.heads

        dataarray = [self[head].vals for head in heads]

        if fstring is None:
            fstring = ("{} "*len(dataarray))[:-1]

        vprint = numpy.vectorize(lambda *args: fstring.format(*args))

        arrnew = vprint(*dataarray)

        if headnew is None:
            fstring = ("{}_"*len(dataarray))[:-1]
            headnew = fstring.format(*heads)

        return column(arrnew,head=headnew)

    def tostruct(self):
        """Returns numpy structure of dataframe."""

        datatype_string = [datacolumn.vals.dtype.str for datacolumn in self.running]

        datatypes = [datatype for datatype in zip(self.heads,datatype_string)]

        return numpy.array([row for row in self],datatypes)

    """ADVANCED METHODS"""
            
    def sort(self,heads,reverse=False,return_indices=False):
        """Returns sorted dataframe."""

        if not (isinstance(heads,list) or isinstance(heads,tuple)):
            raise TypeError("heads must be list or tuple.")

        match = numpy.argsort(self[heads].tostruct(),axis=0,order=heads)

        if reverse:
            match = numpy.flip(match)

        if return_indices:
            return match

        dataframe = copy.deepcopy(self)

        running = [datacolumn[match] for datacolumn in self.running]

        object.__setattr__(dataframe,'running',running)

        return dataframe

    def flip(self):

        dataframe = copy.deepcopy(self)

        running = [datacolumn.flip() for datacolumn in self.running]

        object.__setattr__(dataframe,'running',running)

    def filter(self,key,keywords=None,regex=None,return_indices=False):
        """Returns filtered dataframe based on keywords or regex."""

        datacolumn = self[key]

        match = datacolumn.filter(keywords,regex,return_indices=True)

        if return_indices:
            return match
        else:
            dataframe = copy.deepcopy(self)
            object.__setattr__(dataframe,'running',
                [datacolumn[match] for datacolumn in self.running])
            return dataframe

    def unique(self,heads):
        """Returns dataframe with unique entries of column/s.
        The number of columns will be equal to the length of heads."""

        if not (isinstance(heads,list) or isinstance(heads,tuple)):
            raise TypeError("heads must be list or tuple.")

        df = self[heads]

        npstruct = df.tostruct()

        npstruct = numpy.unique(npstruct,axis=0)

        dataframe = copy.deepcopy(self)

        object.__setattr__(dataframe,'running',[])

        for head in heads:

            datacolumn = copy.deepcopy(self[head])

            datacolumn.vals = npstruct[head]

            dataframe.running.append(datacolumn)

        return dataframe

    """PROPERTY METHODS"""

    @property
    def shape(self):

        if len(self.running)>0:
            return (max([len(datacolumn) for datacolumn in self.running]),len(self.running))
        else:
            return (0,0)

    @property
    def dtypes(self):

        return [datacolumn.vals.dtype for datacolumn in self.running]

    @property
    def types(self):

        return [datacolumn.vals.dtype.type for datacolumn in self.running]

    @property
    def heads(self):

        return [datacolumn.head for datacolumn in self.running]

    @property
    def units(self):

        return [datacolumn.unit for datacolumn in self.running]

    @property
    def infos(self):

        return [datacolumn.info for datacolumn in self.running]

class scape(): # MUST BE RENAMED TO DataScape

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        self.dirname = os.path.dirname(__file__)

    def draw(self,func=None):

        self.scrollbar = tkinter.Scrollbar(self.root)

        self.columns = ["#"+str(idx) for idx,_ in enumerate(self.headers,start=1)]

        self.tree = tkinter.ttk.Treeview(self.root,columns=self.columns,show="headings",selectmode="browse",yscrollcommand=self.scrollbar.set)

        self.sortReverseFlag = [False for column in self.columns]

        for idx,(column,header) in enumerate(zip(self.columns,self.headers)):
            self.tree.column(column,anchor=tkinter.W,stretch=tkinter.NO)
            self.tree.heading(column,text=header,anchor=tkinter.W)

        self.tree.column(self.columns[-1],stretch=tkinter.YES)

        self.tree.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.scrollbar.pack(side=tkinter.LEFT,fill=tkinter.Y)

        self.scrollbar.config(command=self.tree.yview)

        # self.frame = tkinter.Frame(self.root,width=50)
        # self.frame.configure(background="white")
        # self.frame.pack(side=tkinter.LEFT,fill=tkinter.Y)

        self.tree.bind("<KeyPress-i>",self.addItem)

        # self.button_Add = tkinter.Button(self.frame,text="Add Item",width=50,command=self.addItem)
        # self.button_Add.pack(side=tkinter.TOP,ipadx=5,padx=10,pady=(5,1))

        self.tree.bind("<KeyPress-e>",self.editItem)
        self.tree.bind("<Double-1>",self.editItem)

        self.tree.bind("<Delete>",self.deleteItem)

        self.tree.bind("<KeyPress-j>",self.moveDown)
        self.tree.bind("<KeyPress-k>",self.moveUp)

        self.tree.bind("<Button-1>",self.sort_column)

        self.tree.bind("<Control-KeyPress-s>",lambda event: self.saveChanges(func,event))

        # self.button_Save = tkinter.Button(self.frame,text="Save Changes",width=50,command=lambda: self.saveChanges(func))
        # self.button_Save.pack(side=tkinter.TOP,ipadx=5,padx=10,pady=(10,1))

        self.root.protocol('WM_DELETE_WINDOW',lambda: self.close_no_save(func))

        self.counter = self.running[0].size

        self.iids = numpy.arange(self.counter)

        self.added = []
        self.edited = []
        self.deleted = []

        self.refill()

    def refill(self):

        self.tree.delete(*self.tree.get_children())

        rows = numpy.array(self.running).T.tolist()

        for iid,row in zip(self.iids,rows):
            self.tree.insert(parent="",index="end",iid=iid,values=row)

    def addItem(self,event):

        if hasattr(self,"topAddItem"):
            if self.topAddItem.winfo_exists():
                return

        self.topAddItem = tkinter.Toplevel()

        self.topAddItem.resizable(0,0)

        for index,header in enumerate(self.headers):
            label = "label_"+str(index)
            entry = "entry_"+str(index)
            pady = (30,5) if index==0 else (5,5)
            setattr(self.topAddItem,label,tkinter.Label(self.topAddItem,text=header,font="Helvetica 11",width=20,anchor=tkinter.E))
            setattr(self.topAddItem,entry,tkinter.Entry(self.topAddItem,width=30,font="Helvetica 11"))
            getattr(self.topAddItem,label).grid(row=index,column=0,ipady=5,padx=(10,5),pady=pady)
            getattr(self.topAddItem,entry).grid(row=index,column=1,ipady=5,padx=(5,10),pady=pady)

        self.topAddItem.entry_0.focus()

        self.topAddItem.button = tkinter.Button(self.topAddItem,text="Add Item",command=self.addItemEnterClicked)
        self.topAddItem.button.grid(row=index+1,column=0,columnspan=2,ipady=5,padx=15,pady=(15,30),sticky=tkinter.EW)

        self.topAddItem.button.bind('<Return>',self.addItemEnterClicked)

        self.topAddItem.mainloop()

    def addItemEnterClicked(self,event=None):

        if event is not None and event.widget!=self.topAddItem.button:
            return

        values = []

        for idx,header in enumerate(self.headers):
            entry = "entry_"+str(idx)
            value = getattr(self.topAddItem,entry).get()
            values.append(value)

        self.added.append(self.counter)

        self.set_rows(values)

        self.iids = numpy.append(self.iids,self.counter)

        self.tree.insert(parent="",index="end",iid=self.counter,values=values)

        self.counter += 1

        self.topAddItem.destroy()

    def editItem(self,event):

        region = self.tree.identify('region',event.x,event.y)

        if region=="separator":
            self.autowidth(event)
            return

        if not(region=="cell" or event.char=="e"):
            return

        if hasattr(self,"topEditItem"):
            if self.topEditItem.winfo_exists():
                return

        if not self.tree.selection():
            return
        else:
            item = self.tree.selection()[0]

        values = self.tree.item(item)['values']

        self.topEditItem = tkinter.Toplevel()

        self.topEditItem.resizable(0,0)

        for idx,(header,explicit) in enumerate(zip(self.headers,self.headers)):
            label = "label_"+str(idx)
            entry = "entry_"+str(idx)
            pady = (30,5) if idx==0 else (5,5)
            setattr(self.topEditItem,label,tkinter.Label(self.topEditItem,text=explicit,font="Helvetica 11",width=20,anchor=tkinter.E))
            setattr(self.topEditItem,entry,tkinter.Entry(self.topEditItem,width=30,font="Helvetica 11"))
            getattr(self.topEditItem,label).grid(row=idx,column=0,ipady=5,padx=(10,5),pady=pady)
            getattr(self.topEditItem,entry).grid(row=idx,column=1,ipady=5,padx=(5,10),pady=pady)
            getattr(self.topEditItem,entry).insert(0,values[idx])

        self.topEditItem.entry_0.focus()

        self.topEditItem.button = tkinter.Button(self.topEditItem,text="Save Item Edit",command=lambda: self.editItemEnterClicked(item))
        self.topEditItem.button.grid(row=idx+1,column=0,columnspan=2,ipady=5,padx=15,pady=(15,30),sticky=tkinter.EW)

        self.topEditItem.button.bind('<Return>',lambda event: self.editItemEnterClicked(item,event))

        self.topEditItem.mainloop()

    def editItemEnterClicked(self,item,event=None):

        if event is not None and event.widget!=self.topEditItem.button:
            return

        values = []

        for idx,header in enumerate(self.headers):
            entry = "entry_"+str(idx)
            value = getattr(self.topEditItem,entry).get()
            values.append(value)

        self.edited.append([int(item),self.tree.item(item)["values"]])

        self.set_rows(values,numpy.argmax(self.iids==int(item)))

        self.tree.item(item,values=values)

        self.topEditItem.destroy()

    def deleteItem(self,event):

        if not self.tree.selection():
            return
        else:
            item = self.tree.selection()[0]

        self.deleted.append([int(item),self.tree.item(item)["values"]])

        self.del_rows(numpy.argmax(self.iids==int(item)),inplace=True)

        self.iids = numpy.delete(self.iids,numpy.argmax(self.iids==int(item)))

        self.tree.delete(item)

    def autowidth(self,event):

        column = self.tree.identify('column',event.x,event.y)

        index = self.columns.index(column)

        if index==len(self.columns)-1:
            return

        header_char_count = len(self.headers[index])

        vcharcount = numpy.vectorize(lambda x: len(x))

        if self.running[index].size != 0:
            column_char_count = vcharcount(self.running[index].astype(str)).max()
        else:
            column_char_count = 0

        char_count = max(header_char_count,column_char_count)

        width = tkinter.font.Font(family="Consolas", size=12).measure("A"*char_count)

        column_width_old = self.tree.column(column,"width")

        self.tree.column(column,width=width)

        column_width_new = self.tree.column(column,"width")

        column_width_last_old = self.tree.column(self.columns[-1],"width")

        column_width_last_new = column_width_last_old+column_width_old-column_width_new

        self.tree.column(self.columns[-1],width=column_width_last_new)

    def moveUp(self,event):
 
        if not self.tree.selection():
            return
        else:
            item = self.tree.selection()[0]

        self.tree.move(item,self.tree.parent(item),self.tree.index(item)-1)

    def moveDown(self,event):

        if not self.tree.selection():
            return
        else:
            item = self.tree.selection()[0]

        self.tree.move(item,self.tree.parent(item),self.tree.index(item)+1)

    def sort_column(self,event):

        region = self.tree.identify('region',event.x,event.y)

        if region!="heading":
            return

        column = self.tree.identify('column',event.x,event.y)

        header_index = self.columns.index(column)

        reverseFlag = self.sortReverseFlag[header_index]

        N = self.running[0].size

        argsort = numpy.argsort(self.running[header_index])

        if reverseFlag:
            argsort = numpy.flip(argsort)

        for index,column in enumerate(self.running):
            self.running[index] = column[argsort]

        self.iids = self.iids[argsort]
        # indices = numpy.arange(N)

        # sort_indices = indices[numpy.argsort(argsort)]

        self.refill()

        # for item,sort_index in zip(self.iids,sort_indices):
        #     self.tree.move(item,self.tree.parent(item),sort_index)

        self.sortReverseFlag[header_index] = not reverseFlag

    def saveChanges(self,func=None,event=None):

        self.added = []
        self.edited = []
        self.deleted = []

        if func is not None:
            func()

    def close_no_save(self,func=None):

        try:
            for deleted in self.deleted:
                self.set_rows(deleted[1])
        except:
            print("Could not bring back deleted rows ...")

        try:
            for edited in self.edited:
                self.set_rows(edited[1],numpy.argmax(self.iids==edited[0]))
        except:
            print("Could not bring back editions ...")

        added = [numpy.argmax(self.iids==add) for add in self.added]

        try:
            self.del_rows(added,inplace=True)
        except:
            print("Could not remove additions ...")

        try:
            if func is not None:
                func()
        except:
            print("Could not run the called function ...")

        self.root.destroy()

def array1d(argument,size=None):
    """
    All of this will go to inside of array
    """

    array = to_numpy(argument)
    array = to_dtype(array)
    array = to_size(array,size)

    return array

def to_numpy(argument):
    """returns numpy array"""

    if type(argument).__module__=="numpy":
        oneDarray = argument.flatten()
    elif isinstance(argument,str):
        oneDarray = numpy.array([argument])
    elif hasattr(argument,"__iter__"):
        oneDarray = numpy.array(list(argument))
    else:
        oneDarray = numpy.array([argument])

    return oneDarray

def to_dtype(numpy_array,dtype=None):
    """returns numpy array with specified dtype"""

    if numpy_array.dtype.type is numpy.object_:

        numpy_array_temp = numpy_array[numpy_array!=None]

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

def to_size(numpy_array,size=None):
    """returns numpy array with specified shape"""

    if size is None or numpy_array.size==0:
        return numpy_array

    repeat_count = int(numpy.ceil(size/numpy_array.size))

    numpy_array = numpy.tile(numpy_array,repeat_count)[:size]

    return numpy_array

def any2column(*args,**kwargs): # THIS CAN GO TO ARRAY
    """Sets the vals of column."""

    head = pop(kwargs,'head')
    unit = pop(kwargs,'unit')
    info = pop(kwargs,'info')

    dtype = kwargs.get('dtype')

    if dtype is None:
        dtype = _any2column.get_dtype(args)
    elif isinstance(dtype,str):
        dtype = numpy.dtype(dtype)

    if dtype.type is numpy.object_:
        pass
    elif dtype.type is numpy.dtype('int').type:    
        dataarray = _any2column.arrint(*args,**kwargs)
    elif dtype.type is numpy.dtype('float').type:
        dataarray = _any2column.arrfloat(*args,**kwargs)
    elif dtype.type is numpy.dtype('str').type:
        dataarray = _any2column.arrstr(*args,**kwargs)
    elif dtype.type is numpy.dtype('datetime64').type:
        dataarray = _any2column.arrdatetime64(*args,**kwargs)
    else:
        raise ValueError(f"dtype.type is not int, float, str or datetime64, given {dtype.type=}")

    return column(dataarray,head=head,unit=unit,info=info,dtype=dtype)

def key2column(*args,**kwargs): # IT IS KIND OF SIMILAR TO LINSPACE FOR ALL DTYPES
    """Generating column by defining dtype and sending the keywords for array creating methods."""

    head = pop(kwargs,'head')
    unit = pop(kwargs,'unit')
    info = pop(kwargs,'info')

    dtype = kwargs.get('dtype')

    if dtype is None:
        dtype = _key2column.get_dtype(args)
    elif isinstance(dtype,str):
        dtype = numpy.dtype(dtype)

    if dtype.type is numpy.dtype('int').type:    
        dataarray = _key2column.arrint(*args,**kwargs)
    elif dtype.type is numpy.dtype('float').type:
        dataarray = _key2column.arrfloat(*args,**kwargs)
    elif dtype.type is numpy.dtype('str').type:
        dataarray = _key2column.arrstr(*args,**kwargs)
    elif dtype.type is numpy.dtype('datetime64').type:
        dataarray = _key2column.arrdatetime64(*args,**kwargs)
    else:
        raise ValueError(f"dtype.type is not int, float, str or datetime64, given {dtype.type=}")

    return column(dataarray,head=head,unit=unit,info=info,dtype=dtype)

class _any2column():

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

        for index,dataarray in enumerate(arrs):
            repeat_count = int(numpy.ceil(size/dataarray.size))
            arrs[index] = numpy.tile(dataarray,repeat_count)[:size]

        return zip(*arrs)

    def arrint(*args,size=None,dtype=None):

        if len(args)==0:
            return
        elif len(args)==1:
            dataarray = array1d(args[0],size)

        if dtype is None:
            return dataarray
        else:
            return dataarray.astype(dtype)

    def arrfloat(*args,size=None,dtype=None):

        if len(args)==0:
            return
        elif len(args)==1:
            dataarray = array1d(args[0],size)

        if dtype is None:
            return dataarray
        else:
            return dataarray.astype(dtype)

    def arrstr(*args,phrases=None,repeats=None,size=None,dtype=None):

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if len(args)==0:
            if phrases is None:
                phrases = " "
            if repeats is None:
                repeats = 1

            iterator = _any2column.toiterator(phrases,repeats,size=size)

            dataarray = numpy.array(["".join([name]*num) for name,num in iterator])

        elif len(args)==1:
            dataarray = array1d(args[0],size)
        else:
            raise TypeError("Number of arguments can not be larger than 1!")

        if dtype is None:
            return dataarray
        else:
            return dataarray.astype(dtype)

    def arrdatetime64(*args,year=2000,month=1,day=-1,hour=0,minute=0,second=0,size=None,dtype=None):

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if len(args)==0:

            items = [year,month,day,hour,minute,second]

            iterator = _any2column.toiterator(*items,size=size)

            if dtype is None:
                dtype = numpy.dtype(f"datetime64[s]")

            array_date = []

            for row in iterator:
                arguments = list(row)
                if arguments[2]<=0:
                    arguments[2] += calendar.monthrange(*arguments[:2])[1]
                if arguments[2]<=0:
                    arguments[2] = 1
                array_date.append(datetime.datetime(*arguments))

            return numpy.array(array_date,dtype=dtype)

        elif len(args)==1:

            dataarray = array1d(args[0],size)

            if dtype is None:
                return dataarray
            
            try:
                return dataarray.astype(dtype)
            except ValueError:
                array_date = [parser.parse(dt) for dt in dataarray]
                return numpy.array(array_date,dtype=dtype)

class _key2column():

    def get_dtype(args):

        if len(args)==0:
            return

        arg = args[0]

        if arg is None:
            return
        elif isinstance(arg,int):
            return numpy.dtype(type(arg))
        elif isinstance(arg,float):
            return numpy.dtype(type(arg))
        elif isinstance(arg,str):
            arg = _key2column.todatetime(arg)
            if arg is None:
                return numpy.str_(arg).dtype
            else:
                return numpy.dtype('datetime64[s]')
        elif isinstance(arg,datetime.datetime):
            return numpy.dtype('datetime64[s]')
        elif isinstance(arg,datetime.date):
            return numpy.dtype('datetime64[D]')
        elif isinstance(arg,numpy.datetime64):
            return arg.dtype
        else:
            return

    def todatetime(variable):

        if variable is None:
            return
        elif isinstance(variable,str):
            datetime_variable = str2datetime64(variable,unit_code='s').tolist()
        elif isinstance(variable,numpy.datetime64):
            datetime_variable = variable.tolist()
        elif type(variable).__module__=="datetime":
            datetime_variable = variable
        else:
            return

        if isinstance(datetime_variable,datetime.datetime):
            return datetime_variable
        elif isinstance(datetime_variable,datetime.date):
            return datetime.datetime.combine(datetime_variable,datetime.datetime.min.time())

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
            dataarray = numpy.array(list(itertools.islice(excel_column_headers(),stop_index)))[start_index:stop_index]
            dataarray = dataarray[::step]
        else:
            dataarray = numpy.array(list(itertools.islice(excel_column_headers(),start_index+size*step)))[start_index:]
            dataarray = dataarray[::step]

        if dtype is not None:
            return dataarray.astype(dtype)
        else:
            return dataarray

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
            array_date = []
            while date<stop:
                array_date.append(date)
                date = func(date,step)
            return numpy.array(array_date,dtype=dtype)
        elif start is None:
            date = copy.deepcopy(stop)
            array_date = []
            for index in range(size):
                date = func(date,-index*step)
                array_date.append(date)
            return numpy.flip(numpy.array(array_date,dtype=dtype))
        else:
            delta_na = stop-start
            delta_us = (delta_na.days*86_400+delta_na.seconds)*1000_000+delta_na.microseconds

            deltas = numpy.linspace(0,delta_us,size)

            date = copy.deepcopy(start)
            
            array_date = []
            for delta_us in deltas:
                date += relativedelta.relativedelta(microseconds=delta_us)
                array_date.append(date)
            return numpy.array(array_date,dtype=dtype)

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

    from tests.datum import nones
    from tests.datum import array
    from tests.datum import column
    from tests.datum import frame

    unittest.main(nones)
    unittest.main(array)
    unittest.main(column)
    unittest.main(frame)

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