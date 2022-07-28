import calendar
import copy
import datetime

from dateutil import parser, relativedelta

from difflib import SequenceMatcher

import itertools

import logging

import math
import os
import re
import string as pythonstring

import numpy as np
import openpyxl as opxl
import pint
import lasio

if __name__ == "__main__":
    import setup

from cypy.vectorpy import str2int
from cypy.vectorpy import str2float
from cypy.vectorpy import str2str
from cypy.vectorpy import str2datetime64

class nones():
    """Base class to manage none values for int, float, str, datetime64."""

    __types = ("int","float","str","datetime64")

    def __init__(self,nint=None,nfloat=None,nstr=None,ndatetime64=None):
        """Initializes all the types with defaults."""

        self.int = -99_999 if nint is None else nint
        self.float = np.nan if nfloat is None else nfloat
        self.str = "" if nstr is None else nstr
        self.datetime64 = np.datetime64('NaT') if ndatetime64 is None else ndatetime64

    def __str__(self):

        row0 = "None-Values"
        row2 = "{:,d}".format(self.int)
        row3 = "{:,f}".format(self.float)
        row4 = "'{:s}'".format(self.str)
        
        if np.isnan(self.datetime64):
            row5 = "{}".format(self.datetime64)
        else:
            row5 = self.datetime64.tolist().strftime("%Y-%b-%d")

        count = len(max((row0,row2,row3,row4,row5),key=len))

        string = ""

        string += "{:>10s}  {:s}\n".format("Data-Types",row0)
        string += "{:>10s}  {:s}\n".format("-"*10,"-"*count)
        string += "{:>10s}  {:s}\n".format("integers",row2)
        string += "{:>10s}  {:s}\n".format("floats",row3)
        string += "{:>10s}  {:s}\n".format("strings",row4)
        string += "{:>10s}  {:s}\n".format("datetime64",row5)

        return string

    def __setattr__(self,dtype,non_value):

        if dtype == "int":
            non_value = int(non_value)
        elif dtype == "float":
            non_value = float(non_value)
        elif dtype == "str":
            non_value = str(non_value)
        elif dtype == "datetime64":
            non_value = np.datetime64(non_value)
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

    def __init__(self,unit=None,**kwargs):

        self.nones = nones()

        dtype = kwargs.get('dtype')

        if dtype is None:
            dtype = np.dtype('float64')
        elif isinstance(dtype,str):
            dtype = np.dtype(dtype)

        if dtype.type is np.dtype('int').type:
            arr_ = self._arrint(**kwargs)
        elif dtype.type is np.dtype('float').type:
            arr_ = self._arrfloat(unit,**kwargs)
        elif dtype.type is np.dtype('str').type:
            try:
                arr_ = self._arrstr(**kwargs)
            except TypeError:
                arr_ = self._arrstr_fromarrs(**kwargs)
        elif dtype.type is np.dtype('datetime64').type:
            try:
                arr_ = self._arrdatetime64(**kwargs)
            except TypeError:
                arr_ = self._arrdatetime64_fromarrs(**kwargs)
        else:
            raise ValueError(f"dtype is not int, float, str or datetime64, given {dtype=}")

        return arr_

    def get_iterator(self,*args):

        size = 1

        for arg in args:
            if not isinstance(arg,list):
                raise TypeError(f"input can be list only, not type={type(arg)}")
            size = max(size,len(arg))

        items = []

        for arg in args:
            rep = int(np.ceil(size/len(arg))) 
            items.append((arg*rep)[:size])

        return zip(*items)

    def get_time_dtype(self,variable):

        datetime_ = self.get_time_datetime(variable)

        if datetime_ is None:
            return None
        elif isinstance(datetime_,datetime.date):
            datetime_ = datetime.datetime.combine(datetime_,datetime.datetime.min.time())

        if datetime_.second!=0:
            return np.dtype('datetime64[s]')
        elif datetime_.minute!=0:
            return np.dtype('datetime64[m]')
        elif datetime_.hour!=0:
            return np.dtype('datetime64[h]')
        elif datetime_.day!=0:
            return np.dtype('datetime64[D]')
        elif datetime_.month!=0:
            return np.dtype('datetime64[M]')
        elif datetime_.year!=0:
            return np.dtype('datetime64[Y]')

    def get_time_datetime(self,variable):

        if variable is None:
            datetime_ = None
        elif isinstance(variable,str):
            if variable=="now":
                datetime_ = datetime.datetime.today()
            elif variable=="today":
                datetime_ = datetime.date.today()
            elif variable=="yesterday":
                datetime_ = datetime.date.today()+relativedelta.relativedelta(days=-1)
            elif variable=="tomorrow":
                datetime_ = datetime.date.today()+relativedelta.relativedelta(days=+1)
            else:
                try:
                    datetime_ = parser.parse(variable)
                except parser.ParserError:
                    datetime_ = None
        elif isinstance(variable,datetime.datetime):
            datetime_ = variable
        elif isinstance(variable,datetime.date):
            datetime_ = variable
        elif isinstance(variable,np.datetime64):
            datetime_ = variable.tolist()
        else:
            datetime_ = None

        return datetime_

    def _arrint(self,start=0,stop=None,step=1,size=None,dtype=None):

        if dtype is None:
            dtype = np.dtype('int32')
        elif isinstance(dtype,str):
            dtype = np.dtype(dtype)

        if size is None:
            if stop is None:
                raise ValueError("stop value must be provided!")
            return np.arange(start,stop,step,dtype=dtype)
        else:
            if stop is None:
                stop = start+size*step
            return np.linspace(start,stop,size,endpoint=False,dtype=dtype)

    def _arrfloat(self,start=0.,stop=None,step=1.,size=None,dtype=None,unit='dimensionless',step_unit='dimensionless'):

        if unit!=step_unit:
            unrg = pint.UnitRegistry()
            step = unrg.Quantity(step,step_unit).to(unit).magnitude

        if dtype is None:
            dtype = np.dtype('float64')
        elif isinstance(dtype,str):
            dtype = np.dtype(dtype)

        if size is None:
            if stop is None:
                raise ValueError("stop value must be provided!")
            return np.arange(start,stop,step,dtype=dtype)
        else:
            if stop is None:
                stop = start+size*step
            return np.linspace(start,stop,size,dtype=dtype)

    def _arrstr(self,start='A',stop=None,step=1,size=None,dtype=None):

        if isinstance(dtype,str):
            dtype = np.dtype(str)

        def excel_column_headers():
            n = 1
            while True:
                yield from (
                    ''.join(group) for group in itertools.product(
                        pythonstring.ascii_uppercase,repeat=n
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
            arr_ = np.array(list(itertools.islice(excel_column_headers(),stop_index)))[start_index:stop_index]
            arr_ = arr_[::step]
        else:
            arr_ = np.array(list(itertools.islice(excel_column_headers(),start_index+size*step)))[start_index:]
            arr_ = arr_[::step]

        if dtype is not None:
            return arr_.astype(dtype)
        else:
            return arr_

    def _arrstr_fromarrs(self,phrases=None,repeats=None,dtype=None):

        if phrases is None:
            phrases = [" "]

        if repeats is None:
            repeats = [1]

        if isinstance(dtype,str):
            dtype = np.dtype(dtype)

        iter_ = self.get_iterator(phrases,repeats)

        arr_ = np.array([name*num for name,num in iter_])

        if dtype is None:
            return arr_
        else:
            return arr_.astype(dtype)

    def _arrdatetime64(self,start=None,stop="today",step=1,size=None,dtype=None,step_unit=None):

        if step_unit is None:
            step_unit = 'D'

        if isinstance(dtype,str):
            dtype = np.dtype(dtype)

        if dtype is None:
            dtype = self.get_time_dtype(start)

        if dtype is None:
            dtype = self.get_time_dtype(stop)

        if dtype is None:
            dtype = np.dtype(f"datetime64[{step_unit}]")

        if start is None:
            start = stop-delta*size
        else:
            start = self.get_time_datetime(start)

        stop = self.get_time_datetime(stop)
        
        if step_unit == "Y":
            delta = relativedelta.relativedelta(years=int(step//1),months=int(step%1*12),days=(step%1*12-step_months)*30)
        elif step_unit == "M":
            delta = relativedelta.relativedelta(months=int(step//1),days=step%1*30)
        elif step_unit == "D":
            delta = relativedelta.relativedelta(days=step)
        elif step_unit == "h":
            delta = relativedelta.relativedelta(hours=step)
        elif step_unit == "m":
            delta = relativedelta.relativedelta(minutes=step)
        elif step_unit == "s":
            delta = relativedelta.relativedelta(seconds=step)
        else:
            raise ValueError("step_unit can not be anything other than 'Y','M','D','h','m','s'.")

        date = copy.deepcopy(start)

        arr_date = []

        while date<stop:

            arr_date.append(date)

            date += delta

        return np.array(arr_date,dtype=dtype)

    def _arrdatetime64_fromarrs(year=None,month=None,day=-1,hour=0,minute=0,second=0,dtype=None):

        if size is None:
            for arg in (year,month,day):
                if not isinstance(arg,str) and hasattr(arg,"__len__"):
                    size = len(arg)

        if size is None:
            size = 50

        if isinstance(year,int):
            arr_y = np.array([year]*size).astype("str")
        elif isinstance(year,str):
            arr_y = np.array([year]*size)
        elif not hasattr(year,"__len__"):
            raise TypeError(f"year can not be the type {type(year)}")
        elif not isinstance(year,np.ndarray):
            arr_y = np.array(year).astype("str")
        else:
            arr_y = year.astype("str")

        if isinstance(month,int):
            arr_m = np.array([month]*size).astype("str")
        elif isinstance(month,str):
            if len(month)<=2:
                month = datetime.datetime.strptime(month,"%m").month
            elif len(month)==3:
                month = datetime.datetime.strptime(month,"%b").month
            else:
                month = datetime.datetime.strptime(month,"%B").month
            arr_m = np.array([month]*size).astype("str")
        elif not hasattr(month,"__len__"):
            raise TypeError(f"month can not be the type {type(month)}")
        elif not isinstance(month,np.ndarray):
            arr_m = np.array(month).astype("str")
        else:
            arr_m = month.astype("str")

        if isinstance(day,int):
            arr_d = np.array([day]*size)
        elif isinstance(day,str):
            arr_d = np.array([int(day)]*size)
        elif not hasattr(day,"__len__"):
            raise TypeError(f"day can not be the type {type(day)}")
        elif not isinstance(month,np.ndarray):
            arr_d = np.array(day)
        else:
            arr_d = day[:]

        arr_date = []

        for str_y,str_m,int_d in zip(arr_y,arr_m,arr_d):

            int_y,int_m = int(str_y),int(str_m)

            if (int_y==self.nones.int) or (int_m==self.nones.int) or (int_d==self.nones.int):
                arr_date.append(None)

            else:

                if int_d<0:
                    int_d += calendar.monthrange(int_y,int_m)[1]+1

                str_date = "-".join((str_y,str_m,str(int_d)))

                arr_date.append(parser.parse(str_date))

        return np.array(arr_date,dtype='datetime64')

class column():
    """It is a numpy array of shape (N,) with additional attributes of head, unit and info."""

    """INITIALIZATION"""
    def __init__(self,vals=None,head=None,unit=None,info=None,**kwargs):
        """Initializes a column with vals of numpy array (N,) and additional attributes."""

        """
        Initialization can be done in two ways:
        
        1) Defining vals by sending int, float, string, datetime.date, numpy.datetime64 as standalone or
        in a list, tuple or numpy.array
        
        2) Generating a numpy array by defining dtype and sending the keywords for array creating methods.
        
        The argument "dtype" is optional and can be any of the {int, float, str, datetime64}

        """

        self.nones = nones()

        self._valsarr(vals,kwargs.get('size'))

        self.astype(kwargs.get('dtype'))

        self._valshead(head)
        self._valsunit(unit)
        self._valsinfo(info)

    def _valsarr(self,vals=None,size=None):
        """Sets the vals of column."""

        if vals is None:
            num = 1 if size is None else size
            arr = np.array([np.nan]*num)
        elif isinstance(vals,int):
            num = 1 if size is None else size
            arr = np.array([vals,]*num)
        elif isinstance(vals,float):
            num = 1 if size is None else size
            arr = np.array([vals,]*num)
        elif isinstance(vals,str):
            num = 1 if size is None else size
            arr = np.array([vals,]*num)
        elif isinstance(vals,datetime.datetime):
            num = 1 if size is None else size
            arr = np.array([vals,]*num,dtype='datetime64[s]')
        elif isinstance(vals,datetime.date):
            num = 1 if size is None else size
            arr = np.array([vals,]*num,dtype='datetime64[D]')
        elif isinstance(vals,np.datetime64):
            num = 1 if size is None else size
            arr = np.array([vals,]*num)
        elif isinstance(vals,np.ndarray):
            arr = vals.flatten()
            rep = 1 if size is None else int(np.ceil(size/arr.size))
            num = arr.size if size is None else size
            arr = arr if size is None else np.tile(arr,rep)[:num]
        elif isinstance(vals,list):
            arr = np.array(vals).flatten()
            rep = 1 if size is None else int(np.ceil(size/arr.size))
            num = arr.size if size is None else size
            arr = arr if size is None else np.tile(arr,rep)[:num]
        elif isinstance(vals,tuple):
            arr = np.array(vals).flatten()
            rep = 1 if size is None else int(np.ceil(size/arr.size))
            num = arr.size if size is None else size
            arr = arr if size is None else np.tile(arr,rep)[:num]
        else:
            logging.warning(f"Unexpected object type {type(arr)}.")

        super().__setattr__("vals",arr)

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

        if self.dtype.type is np.dtype('float').type:
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

    def astype(self,dtype=None):
        """It changes the dtype of the column and alters the None values accordingly."""

        if isinstance(dtype,str):
            dtype = np.dtype(dtype)

        if dtype is None:
            pass
        elif not isinstance(dtype,np.dtype):
            raise TypeError(f"dtype must be numpy.dtype, not type={type(dtype)}")
        elif dtype.type is np.object_:
            raise TypeError(f"Unexpected numpy.dtype, {dtype=}")
        elif self.dtype==dtype:
            return

        if dtype is None:
            dtype = self.dtype

        if dtype.type is np.dtype('int').type:
            none = getattr(self.nones,'int')
        elif dtype.type is np.dtype('float').type:
            none = getattr(self.nones,'float')
        elif dtype.type is np.dtype('str').type:
            none = getattr(self.nones,'str')
        elif dtype.type is np.dtype('datetime64').type:
            none = getattr(self.nones,'datetime64')
        else:
            raise TypeError(f"Unexpected numpy.dtype, {dtype=}")

        isnone = self.isnone()

        vals_arr = np.empty(self.vals.size,dtype=dtype)

        vals_arr[isnone] = none
        vals_arr[~isnone] = self.vals[~isnone].astype(dtype=dtype)

        super().__setattr__("vals",vals_arr)

        self._valsunit()

    def fromstring(self,dtype,regex=None,sep_thousand=",",sep_decimal="."):

        if isinstance(dtype,str):
            dtype = np.dtype(dtype)

        if dtype.type is np.dtype('int').type:
            dnone = self.nones.todict("str","int")
            regex = r"[-+]?\d+\b" if regex is None else regex
            self.vals = str2int(self.vals,regex=regex,**dnone)
        elif dtype.type is np.dtype('float').type:
            dnone = self.nones.todict("str","float")
            regex = f"[-+]?(?:\\d*\\{sep_thousand}*\\d*\\{sep_decimal}\\d+|\\d+)" if regex is None else regex
            self.vals = str2float(self.vals,regex=regex,**dnone)
            self._valsunit()
        elif dtype.type is np.dtype('str').type:
            dnone = self.nones.todict("str")
            self.vals = str2str(self.vals,regex=regex,**dnone)
        elif dtype.type is np.dtype('datetime64').type:
            dnone = self.nones.todict("str","datetime64")
            self.vals = str2datetime64(self.vals,regex=regex,**dnone)
        else:
            raise TypeError("dtype can be either int, float, str or datetime64")

    def tostring(self,fstring=None,upper=False,lower=False,zfill=None):
        """It has more capabilities than str2str on the outputting part."""

        if fstring is None:
            fstring_inner = "{}"
            fstring_clean = "{}"
        else:
            fstring_inner = re.search(r"\{(.*?)\}",fstring).group()
            fstring_clean = re.sub(r"\{(.*?)\}","{}",fstring,count=1)

        vals_str = []

        for val,none_bool in zip(self.vals.tolist(),self.isnone()):

            if none_bool:
                vals_str.append(self.nones.str)
                continue

            if isinstance(val,datetime.date):
                string = val.strftime(fstring_inner[1:-1])
            else:
                string = fstring_inner.format(val)

            if zfill is not None:
                string = string.zfill(zfill)

            if upper:
                string = string.upper()
            elif lower:
                string = string.lower()

            string = fstring_clean.format(string)

            vals_str.append(string)

        vals_str = np.array(vals_str,dtype="str")

        column_ = copy.copy(self)

        column_.astype("str")

        column_.vals = vals_str

        return column_

    """REPRESENTATION"""
    def _valstr_(self,num=None):
        """It outputs column.vals in string format. If num is not defined it edites numpy.ndarray.__str__()."""

        if num is None:

            vals_str = self.vals.__str__()

            if self.vals.dtype.type is np.int32:
                vals_lst = re.findall(r"[-+]?[0-9]+",vals_str)
                vals_str = re.sub(r"[-+]?[0-9]+","{}",vals_str)
            elif self.vals.dtype.type is np.float64:
                vals_lst = re.findall(r"[-+]?(?:\d*\.\d+|\d+)",vals_str)
                vals_str = re.sub(r"[-+]?(?:\d*\.\d+|\d+)","{}",vals_str)
            elif self.vals.dtype.type is np.str_:
                vals_lst = re.findall(r"\'(.*?)\'",vals_str)
                vals_str = re.sub(r"\'(.*?)\'","\'{}\'",vals_str)
            elif self.vals.dtype.type is np.datetime64:
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
                part1,part2 = int(np.ceil(num/2)),int(np.floor(num/2))
                fstring = "[{}...{}]".format("{},"*part1,",{}"*part2)

            if self.vals.dtype.type is np.int32:
                vals_str = fstring.format(*["{:d}"]*part1,*["{:d}"]*part2)
            elif self.vals.dtype.type is np.float64:
                vals_str = fstring.format(*["{:g}"]*part1,*["{:g}"]*part2)
            elif self.vals.dtype.type is np.str_:
                vals_str = fstring.format(*["'{:s}'"]*part1,*["'{:s}'"]*part2)
            elif self.vals.dtype.type is np.datetime64:
                vals_str = fstring.format(*["'{}'"]*part1,*["'{}'"]*part2)

            return vals_str.format(*self.vals[:part1],*self.vals[-part2:])

    def __repr__(self):
        """Console representation of column."""

        return f'column(head="{self.head}", unit="{self.unit}", info="{self.info}", vals={self._valstr_(2)})'

    def __str__(self):
        """Print representation of column."""

        string = "{}\n"*4

        head = f"head\t: {self.head}"
        unit = f"unit\t: {self.unit}"
        info = f"info\t: {self.info}"
        vals = f"vals\t: {self._valstr_(2)}"

        return string.format(head,unit,info,vals)

    """COMPARISON"""
    def isnone(self):
        """It return boolean array by comparing the values of vals to none types defined by column."""

        if self.vals.dtype.type is np.object_:

            bool_arr = np.full(self.vals.shape,False,dtype=bool)

            for index,val in enumerate(self.vals):
                if val is None:
                    bool_arr[index] = True
                elif isinstance(val,int):
                    if val==self.nones.int:
                        bool_arr[index] = True
                elif isinstance(val,float):
                    if np.isnan(val):
                        bool_arr[index] = True
                    elif not np.isnan(self.nones.float):
                        if val==self.nones.float:
                            bool_arr[index] = True
                elif isinstance(val,str):
                    if val==self.nones.str:
                        bool_arr[index] = True
                elif isinstance(val,np.datetime64):
                    if np.isnat(val):
                        bool_arr[index] = True
                    elif not np.isnat(self.nones.datetime64):
                        if val==self.nones.datetime64:
                            bool_arr[index] = True

        elif self.dtype.type is np.dtype("int").type:
            bool_arr = self.vals==self.nones.int

        elif self.dtype.type is np.dtype("float").type:
            bool_arr = np.isnan(self.vals)
            if not np.isnan(self.nones.float):
                bool_arr = np.logical_or(bool_arr,self.vals==self.nones.float)

        elif self.dtype.type is np.dtype("str").type:
            bool_arr = self.vals == self.nones.str

        elif self.dtype.type is np.dtype("datetime64").type:
            bool_arr = np.isnat(self.vals)
            if not np.isnat(self.nones.datetime64):
                bool_arr = np.logical_or(bool_arr,self.vals==self.nones.datetime64)

        else:
            raise TypeError(f"Unidentified problem with column dtype={self.vals.dtype.type}")

        return bool_arr

    def nondim(self):
        """It checks whether column has unit or not."""

        if self.vals.dtype.type is np.float64:
            return self.unit=="dimensionless"
        else:
            return True

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
                return np.abs(self.vals-other.vals)<tol*np.maximum(np.abs(self.vals),np.abs(other.vals))
                #np.allclose(self.vals,other.vals,rtol=1e-10,atol=1e-10)
            else:
                return self.vals==other.vals
        else:
            return self.vals==other

    def __ne__(self,other,tol=1e-12):
        """Implementing '!=' operator."""
        
        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
                return np.abs(self.vals-other.vals)>tol*np.maximum(np.abs(self.vals),np.abs(other.vals))
            else:
                return self.vals!=other.vals
        else:
            return self.vals!=other

    def __bool__(self):

        if self.vals.dtype.type is np.object_:
            return self.vals.any()
        elif self.vals.dtype.type is np.int32:
            return self.vals.any()
        elif self.vals.dtype.type is np.float64:
            return not np.all(np.isnan(self.vals))
        elif self.vals.dtype.type is np.str_:
            return self.vals.any()
        elif self.vals.dtype.type is np.datetime64:
            return not np.all(np.isnat(self.vals))

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

    """CONTAINER METHODS"""
    def min(self):
        """It returns none-minimum value of column."""

        if self.vals.dtype.type is np.int32:
            return self.vals[~self.isnone()].min()
        elif self.vals.dtype.type is np.float64:
            return np.nanmin(self.vals)
        elif self.vals.dtype.type is np.str_:
            return min(self.vals[~self.isnone()],key=len)
        elif self.vals.dtype.type is np.datetime64:
            return np.nanmin(self.vals)

    def max(self):
        """It returns none-maximum value of column."""

        if self.vals.dtype.type is np.int32:
            return self.vals[~self.isnone()].max()
        elif self.vals.dtype.type is np.float64:
            return np.nanmax(self.vals)
        elif self.vals.dtype.type is np.str_:
            return max(self.vals[~self.isnone()],key=len)
        elif self.vals.dtype.type is np.datetime64:
            return np.nanmax(self.vals)

    def maxchar(self,string=False):
        """It returns the maximum character count in stringified column."""

        if self.vals.dtype.type is np.str_:
            vals = self.vals
        else:
            vals = self.tostring().vals

        charsize = np.dtype(f"{vals.dtype.char}1").itemsize

        if string:
            return max(vals,key=len)
        else:
            return int(vals.dtype.itemsize/charsize)

    def replace(self,new=None,old=None,method="upper"):
        """It replaces old with new. If old is not defined, it replaces nones.
        If new is not defined, it uses upper or lower values to replace the olds."""

        if old is None:
            conds = self.isnone()
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

    def __setitem__(self,key,vals):

        self.vals[key] = vals

    def __iter__(self):

        return iter(self.vals)

    def __len__(self):

        return len(self.vals)

    def __getitem__(self,key):

        column_ = copy.deepcopy(self)

        column_.vals = self.vals[key]

        return column_

    """OPERATIONS"""
    def convert(self,unit):
        """It converts the vals to the new unit."""

        if self.unit==unit:
            return self

        column_ = copy.deepcopy(self)

        if self.dtype.type is not np.dtype('float').type:
            column_.astype('float')
        else:
            unrg = pint.UnitRegistry()
            unrg.Quantity(column_.vals,column_.unit).ito(unit)

        column_.unit = unit

        return column_
    
    def shift(self,delta,deltaunit=None):
        """Shifting the entries depending on its dtype."""

        column_ = copy.deepcopy(self)

        if column_.dtype.type is np.dtype('int').type:
            delta_ = column(delta,dtype='int')
            vals_shifted = column_.vals+delta_.vals
        elif column_.dtype.type is np.dtype('float').type:
            delta_ = column(delta,dtype='float',unit=deltaunit)
            delta_ = delta_.convert(column_.unit)
            vals_shifted = column_.vals+delta_.vals
        elif column_.dtype.type is np.dtype('str').type:
            delta_ = column(None,dtype='str',space=delta)
            vals_shifted = np.char.add(delta_.vals,column_)
        elif column_.dtype.type is np.dtype('datetime64').type:
            if deltaunit is None:
                arr_y = column_.year[:]
                arr_m = column_.month[:]
                arr_d = 1 if delta=="BOM" else column_.eom[:]
                vals_shifted = column_._arrdatetime64_(year=arr_y,month=arr_m,day=arr_d)
            elif deltaunit == "Y":
                year0 = column_.year
                year1 = year0+delta
                feb28_bool = np.logical_and(column_.month==2,column_.day==28)
                feb29_bool = np.logical_and(column_.month==2,column_.day==29)
                year0_leap_bool = year0%4==0
                year0_leap_bool[year0%100==0] = False
                year0_leap_bool[year0%400==0] = True
                year0_leap_bool[column_.month>2] = False
                year0_leap_bool[feb29_bool] = False
                year1_leap_bool = year1%4==0
                year1_leap_bool[year1%100==0] = False
                year1_leap_bool[year1%400==0] = True
                year1_leap_bool[column_.month>2] = False
                year1_leap_bool[np.logical_and(~year0_leap_bool,feb28_bool)] = False
                year1_leap_bool[feb29_bool] = False
                leap_year_count4 = year1//4-year0//4
                leap_year_count100 = year1//100-year0//100
                leap_year_count400 = year1//400-year0//400
                leap_year_count = leap_year_count4-leap_year_count100+leap_year_count400
                day_arr = 365*delta+leap_year_count+year0_leap_bool-year1_leap_bool
                day_arr = day_arr.astype("str")
                day_arr[column_.isnone()] = "NaT"
                vals_shifted = column_.vals+day_arr.astype("timedelta64[D]")
            elif deltaunit == "M":
                delta_ = column(delta,size=len(column_),dtype='float',unit='months')
                delta_month = (delta_.vals//1).astype('int')
                vals_shifted = []
                for (val,delta) in zip(column_.vals.tolist(),delta_month):
                    delta = relativedelta.relativedelta(months=delta)
                    if val is not None:
                        vals_shifted.append(val+delta)
                    else:
                        vals_shifted.append(None)
                vals_shifted = np.array(vals_shifted,dtype=column_.dtype)
                delta_monthfraction_ = (delta_.vals%1)
                cond_days = np.logical_and(~np.isnan(vals_shifted),delta_monthfraction_!=0)
                column_temp = column(vals_shifted[cond_days],dtype=column_.dtype)
                delta_monthfraction = delta_monthfraction_[cond_days]
                day_ = column_temp.day
                eom_ = column_temp.eom
                eonm_ = column_temp.eonm
                cond1 = (eom_-day_)/eom_>delta_monthfraction
                cond2 = ~cond1
                delta_day = np.empty(column_temp.vals.shape,dtype='float')
                fraction = (eom_[cond2]-eonm_[cond2])*(eom_[cond2]-day_[cond2])/eom_[cond2]
                delta_day[cond1] = delta_monthfraction[cond1]*eom_[cond1]
                delta_day[cond2] = delta_monthfraction[cond2]*eonm_[cond2]+fraction
                for index,(val,delta) in enumerate(zip(column_temp.vals,delta_day)):
                    column_temp.vals[index] += relativedelta.relativedelta(days=delta)
                vals_shifted[cond_days] = column_temp.vals
            else:
                timedelta = np.timedelta64(delta,deltaunit)
                vals_shifted = column_.vals+timedelta

        column_.vals = vals_shifted

        return column_

    def __add__(self,other):
        """Implementing '+' operator."""

        curnt = copy.deepcopy(self)

        if not isinstance(other,column):
            other = column(other)

        if curnt.dtype.type is np.dtype('int').type:
            if not other.dtype.type is np.dtype('int').type:
                other.astype('int')
            curnt.vals += other.vals
        elif curnt.dtype.type is np.dtype('float').type:
            if not other.dtype.type is np.dtype('float').type:
                other.astype('float')
            other = other.convert(curnt.unit)
            curnt.vals += other.vals
        elif curnt.dtype.type is np.dtype('str').type:
            if not other.dtype.type is np.dtype('str').type:
                other.astype('str')
            curnt.vals = np.char.add(curnt.vals,other.vals)
        elif curnt.dtype.type is np.dtype('datetime64').type:
            unrg = pint.UnitRegistry()
            unit = unrg.Unit(other.unit).__str__()
            if unit is None:
                raise TypeError(f"Only floats with delta time unit is supported.")
            else:
                curnt = curnt.shift(other.vals,deltaunit=unit)

        return curnt

    def __floordiv__(self,other):
        """Implementing '//' operator."""

        column_ = copy.copy(self)

        if isinstance(other,column):
            # ureg = pint.UnitRegistry()
            # unit = ureg.Unit(f"{self.unit}/({other.unit})").__str__()

            if other.nondim() and self.nondim():
                unit = "dimensionless"
            elif not other.nondim() and self.nondim():
                unit = f"1/{other.unit}"
            elif other.nondim() and not self.nondim():
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

        column_ = copy.copy(self)

        if isinstance(other,column):
        #     ureg = pint.UnitRegistry()
        #     unit = ureg.Unit(f"{self.unit}/({other.unit})").__str__()
        #     return column(self.vals%other.vals,unit=unit)
            if other.nondim():
                column_.vals = self.vals%other.vals
            else:
                raise TypeError(f"unsupported operand type for dimensional column arrays.")
        else:
            column_.vals = self.vals%other
            
        return column_

    def __mul__(self,other):
        """Implementing '*' operator."""

        column_ = copy.copy(self)

        if isinstance(other,column):
            # ur = pint.UnitRegistry()
            # unit = ur.Unit(f"{self.unit}*{other.unit}").__str__()

            if other.nondim():
                unit = self.unit
            elif self.nondim():
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

        column_ = copy.copy(self)

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

        column_ = copy.copy(self)

        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            column_.vals = self.vals-other.vals
        else:
            column_.vals = self.vals-other
        
        return column_

    def __truediv__(self,other):
        """Implementing '/' operator."""

        column_ = copy.copy(self)

        if isinstance(other,column):
            # ur = pint.UnitRegistry()
            # unit = ur.Unit(f"{self.unit}/({other.unit})").__str__()

            if other.nondim() and self.nondim():
                unit = "dimensionless"
            elif not other.nondim() and self.nondim():
                unit = f"1/{other.unit}"
            elif other.nondim() and not self.nondim():
                unit = self.unit
            else:
                unit = f"{self.unit}/({other.unit})"

            column_.vals = self.vals/other.vals
            column_._valsunit(unit)
        else:
            column_.vals = self.vals/other
        
        return column_

    """PROPERTY METHODS"""
    @property
    def dtype(self):
        """Return dtype of column.vals."""

        if self.vals.dtype.type is np.object_:
            array_ = self.vals[~self.isnone()]

            if array_.size==0:
                dtype_ = np.dtype('U1')
            elif isinstance(array_[0],datetime.datetime):
                dtype_ = np.dtype('M8[s]')
            elif isinstance(array_[0],datetime.date):
                dtype_ = np.dtype('M8[D]')
            else:
                dtype_ = np.array([array_[0]]).dtype

        else:
            dtype_ = self.vals.dtype

        return dtype_
    
    @property
    def year(self):

        if self.vals.dtype.type is not np.datetime64:
            return

        year_arr = np.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):
            if dt is None:
                year_arr[index] = self.nones.int
            else:
                year_arr[index] = dt.year

        return year_arr

    @property
    def month(self):

        if self.vals.dtype.type is not np.datetime64:
            return

        month_arr = np.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):
            if dt is None:
                month_arr[index] = self.nones.int
            else:
                month_arr[index] = dt.month

        return month_arr

    @property
    def eom(self): # End of Month
        """It returns the day count in the month in the datetime array."""

        if self.vals.dtype.type is not np.datetime64:
            return

        days_arr = np.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):
            if dt is None:
                days_arr[index] = self.nones.int
            else:
                days_arr[index] = calendar.monthrange(dt.year,dt.month)[1]

        return days_arr

    @property
    def eonm(self): # End of Next Month
        """It returns the day count in the next month in the datetime array."""

        if self.vals.dtype.type is not np.datetime64:
            return

        days_arr = np.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):

            if dt is None:
                days_arr[index] = self.nones.int
            else:
                dt += relativedelta.relativedelta(months=1)
                days_arr[index] = calendar.monthrange(dt.year,dt.month)[1]

        return days_arr

    @property
    def eopm(self): # End of Previous Month
        """It returns the day count in the next month in the datetime array."""

        if self.vals.dtype.type is not np.datetime64:
            return

        days_arr = np.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):

            if dt is None:
                days_arr[index] = self.nones.int
            else:
                dt -= relativedelta.relativedelta(months=1)
                days_arr[index] = calendar.monthrange(dt.year,dt.month)[1]

        return days_arr

    @property
    def day(self):

        if self.vals.dtype.type is not np.datetime64:
            return

        day_arr = np.empty(self.vals.shape,dtype=int)

        for index,dt in enumerate(self.vals.tolist()):
            if dt is None:
                day_arr[index] = self.nones.int
            else:
                day_arr[index] = dt.day

        return day_arr

class alphabet():

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

    def __init__(self,string):

        self.string = string

    def convert(self,language="aze",from_="cyril",to="latin"):

        from_lower = getattr(self,f"{language}_{from_}_lower")
        from_upper = getattr(self,f"{language}_{from_}_upper")

        to_lower = getattr(self,f"{language}_{to}_lower")
        to_upper = getattr(self,f"{language}_{to}_upper")

        for from_letter,to_letter in zip(from_lower,to_lower):
            self.string.replace(from_letter,to_letter)

        for from_letter,to_letter in zip(from_upper,to_upper):
            self.string.replace(from_letter,to_letter)

if __name__ == "__main__":

    import unittest

    from tests import coretest

    unittest.main(coretest)

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