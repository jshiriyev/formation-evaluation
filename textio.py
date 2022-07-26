import calendar
import copy
import datetime

from dateutil import parser, relativedelta

from difflib import SequenceMatcher

import logging

import math
import os
import re

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

"""
1. DataFrame representation
2. DataFrame attributes and glossary
3. DataFrame sort, filter, unique
4. DataFrame read, write
5. Finalize RegText
6. Finalize LogASCII
7. Finalize Excel
8. loadtext should be working well
"""

class DirBase():
    """Base directory class to manage files in the input & output directories."""

    def __init__(self,homedir=None,filedir=None):
        """Initializes base directory class with home & file directories."""

        self.set_homedir(homedir)
        self.set_filedir(filedir)

    def set_homedir(self,path=None):
        """Sets home directory to put outputs."""

        if path is None:
            path = os.getcwd()
        elif not os.path.isdir(path):
            path = os.path.dirname(path)

        if os.path.isabs(path):
            self.homedir = path
        else:
            self.homedir = os.path.normpath(os.path.join(os.getcwd(),path))

    def set_filedir(self,path=None):
        """Sets file directory to get inputs."""

        if path is None:
            path = self.homedir
        elif not os.path.isdir(path):
            path = os.path.dirname(path)

        if os.path.isabs(path):
            self.filedir = path
        else:
            self.filedir = os.path.normpath(os.path.join(self.homedir,path))

    def get_abspath(self,path,homeFlag=False):
        """Returns absolute path for a given relative path."""

        if os.path.isabs(path):
            return path
        elif homeFlag:
            return os.path.normpath(os.path.join(self.homedir,path))
        else:
            return os.path.normpath(os.path.join(self.filedir,path))

    def get_dirpath(self,path,homeFlag=False):
        """Returns absolute directory path for a given relative path."""

        path = self.get_abspath(path,homeFlag=homeFlag)

        if os.path.isdir(path):
            return path
        else:
            return os.path.dirname(path)

    def get_fnames(self,path=None,prefix=None,extension=None,returnAbsFlag=False,returnDirsFlag=False):
        """Return directory(folder)/file names for a given relative path."""

        if path is None:
            path = self.filedir
        else:
            path = self.get_dirpath(path)

        fnames = os.listdir(path)

        fpaths = [self.get_abspath(fname,homeFlag=False) for fname in fnames]

        if returnDirsFlag:

            foldernames = [fname for (fname,fpath) in zip(fnames,fpaths) if os.path.isdir(fpath)]
            folderpaths = [fpath for fpath in fpaths if os.path.isdir(fpath)]

            if prefix is None:
                if returnAbsFlag:
                    return folderpaths
                else:
                    return foldernames
            else:
                if returnAbsFlag:
                    return [folderpath for (folderpath,foldername) in zip(folderpaths,foldernames) if foldername.startswith(prefix)]
                else:
                    return [foldername for foldername in foldernames if foldername.startswith(prefix)]
        else:

            filenames = [fname for (fname,fpath) in zip(fnames,fpaths) if not os.path.isdir(fpath)]
            filepaths = [fpath for fpath in fpaths if not os.path.isdir(fpath)]

            if prefix is None and extension is None:
                if returnAbsFlag:
                    return filepaths
                else:
                    return filenames
            elif prefix is None and extension is not None:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.endswith(extension)]
                else:
                    return [filename for filename in filenames if filename.endswith(extension)]
            elif prefix is not None and extension is None:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.startswith(prefix)]
                else:
                    return [filename for filename in filenames if filename.startswith(prefix)]
            else:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.startswith(prefix) and filename.endswith(extension)]
                else:
                    return [filename for filename in filenames if filename.startswith(prefix) and filename.endswith(extension)]

class ColNone():
    """Base class to manage none values for int, float, str and datetime64."""

    __dtypes = ("int","float","str","datetime64")

    def __init__(self,nint=None,nfloat=None,nstr=None,ndatetime64=None):
        """Initializes all the dtypes with defaults."""

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
            raise KeyError("int, float, str and datetime64 are the attributes to modify.")

        super().__setattr__(dtype,non_value)

    def todict(self,*args):

        nones_dict = {}

        if len(args)==0:
            args = self._ColNone__dtypes

        for arg in args:
            nones_dict[f'none_{arg}'] = getattr(self,arg)

        return nones_dict

class ColArray():
    """It is a numpy array of shape (N,) with additional attributes of head, unit and info."""

    """INITIALIZATION"""
    def __init__(self,vals=None,dtype=None,head=None,unit=None,info=None,**kwargs):
        """Initializes a column with vals of numpy array (N,) and additional attributes."""

        """
        Initialization can be done in two ways:
        
        1) Defining vals by sending int, float, string, datetime.date, numpy.datetime64 as standalone or
        in a list, tuple or numpy.array
        
        2) Generating a numpy array by defining dtype and sending the keywords for array creating methods.
        
        The argument "dtype" is optional and can be any of the {int, float, str, np.datetime64}

        """

        self.nones = ColNone()

        if isinstance(dtype,str):
            dtype = np.dtype(dtype)

        try:
            charcount = kwargs.pop("charcount")
        except KeyError:
            charcount = None

        if vals is not None:

            if isinstance(vals,int):
                vals = np.array([vals])
            elif isinstance(vals,float):
                vals = np.array([vals])
            elif isinstance(vals,str):
                vals = np.array([vals])
            elif isinstance(vals,datetime.date):
                vals = np.array([vals])
            elif isinstance(vals,np.datetime64):
                vals = np.array([vals])
            elif isinstance(vals,np.ndarray):
                vals = vals.flatten()
            elif isinstance(vals,list):
                vals = np.array(vals).flatten()
            elif isinstance(vals,tuple):
                vals = np.array(vals).flatten()
            else:
                logging.warning(f"Unexpected object type {type(vals)}.")

            self.vals = vals

            self.astype(dtype=dtype,charcount=charcount)

        elif dtype is not None:

            if dtype.type is np.dtype('int').type:
                self.vals = self._arrint_(**kwargs)
            elif dtype.type is np.dtype('float').type:
                self.vals = self._arrfloat_(**kwargs)
            elif dtype.type is np.dtype('str').type:
                self.vals = self._arrstr_(**kwargs)
                self.astype(dtype,charcount=charcount)
            elif dtype.type is np.dtype('datetime64').type:
                self.vals = self._arrdatetime64_(**kwargs)
            else:
                raise ValueError(f"dtype is not int, float, str or np.datetime64, given {dtype=}")

        else:

            if len(kwargs)==0:
                vals = self._arrfloat_(size=0)
            else:
                vals = self._arrfloat_(**kwargs)
            
            self.vals = vals

        self._valshead_(head)
        self._valsunit_(unit)
        self._valsinfo_(info)

    def _valsarr_(self):
        """Sets the vals of ColArray."""

        pass

    def _valshead_(self,head=None):
        """Sets the head of ColArray."""

        if head is None:
            if hasattr(self,"head"):
                return
            else:
                self.head = "HEAD"
        else:
            self.head = re.sub(r"[^\w]","",str(head))

    def _valsunit_(self,unit=None):
        """Sets the unit of ColArray."""

        if self.vals.dtype.type is np.float64:
            if unit is None:
                if hasattr(self,"unit"):
                    if self.unit is None:
                        self.unit = "dimensionless"
                    return
                else:
                    self.unit = "dimensionless"
            else:
                self.unit = unit
        elif unit is not None:
            try:
                self.vals = self.vals.astype("float")
            except ValueError:
                logging.critical(f"Only numpy.float64 or float-convertables can have units, not {self.vals.dtype.type}")
            else:
                self.unit = unit
        else:
            self.unit = None

    def _valsinfo_(self,info=None):
        """Sets the info of ColArray."""

        if info is None:
            if hasattr(self,"info"):
                return
            else:
                self.info = " "
        else:
            self.info = str(info)

    def astype(self,dtype=None,charcount=None,datetimeunit=None):
        """It changes the dtype of the ColArray and alters the None values accordingly."""

        if dtype is None:
            dtype = self.dtype
        elif isinstance(dtype,str):
            dtype = np.dtype(dtype)
        elif dtype.type is np.object_:
            raise TypeError(f"Unexpected numpy.dtype, {dtype=}")

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

        vals_arry = np.empty(self.vals.size,dtype=dtype)

        vals_arry[isnone] = none
        vals_arry[~isnone] = self.vals[~isnone].astype(dtype=dtype)

        self.vals = vals_arry

        if (dtype.type is np.dtype('str').type) and (charcount is not None):
            self.vals = self.vals.astype(dtype=f"U{charcount}")  

        self._valsunit_()

    def _arrint_(self,start:int=0,stop:int=None,step:int=1,size:int=None):

        if size is None:
            stop = start+50 if stop is None else stop
            return np.arange(start,stop,step,dtype=int)
        else:
            stop = start+size if stop is None else stop
            return np.linspace(start,stop,size,endpoint=False,dtype=int)

    def _arrfloat_(self,start:float=0.,stop:float=None,step:float=1.,size:int=None):

        if size is None:
            stop = start+50 if stop is None else stop
            return np.arange(start,stop,step,dtype=float)
        else:
            stop = start+size if stop is None else stop
            return np.linspace(start,stop,size,dtype=float)

    def _arrstr_(self,start=None,stop=None,step=None,size=None):

        return np.empty((size,),dtype=str)

    def _arrdatetime64_(self,start=None,stop="today",step=1,step_unit="D",size=None,year=None,month=None,day=-1):

        if (year is None) or (month is None):

            if size is None:
                size = 50

            if step_unit == "D":
                delta = relativedelta.relativedelta(days=step)
            elif step_unit == "M":
                delta = relativedelta.relativedelta(months=step)
            elif step_unit == "Y":
                delta = relativedelta.relativedelta(years=step)
            else:
                raise ValueError("step_unit can not be anything other than 'D', 'M', 'Y'.")

            if isinstance(stop,datetime.date):
                pass
            elif isinstance(stop,str):
                if stop=="today":
                    stop = datetime.datetime.today()
                elif stop=="yesterday":
                    stop = datetime.datetime.today()
                    stop += relativedelta.relativedelta(days=-1)
                elif stop=="tomorrow":
                    stop = datetime.datetime.today()
                    stop += relativedelta.relativedelta(days=+1)
                else:
                    stop = parser.parse(stop)
            else:
                raise TypeError(f"stop can not be the type {type(stop)}")

            if isinstance(start,datetime.date):
                pass
            elif isinstance(start,str):
                if start=="today":
                    start = datetime.datetime.today()
                elif start=="yesterday":
                    start = datetime.datetime.today()
                    start += relativedelta.relativedelta(days=-1)
                elif start=="tomorrow":
                    start = datetime.datetime.today()
                    start += relativedelta.relativedelta(days=+1)
                else:
                    start = parser.parse(start)
            elif start is None:
                start = stop-delta*size
            else:
                raise TypeError(f"start can not be the type {type(start)}")

            date = copy.copy(start)

            arr_date = []

            while date<stop:

                arr_date.append(date)

                date += delta

            return np.array(arr_date,dtype=np.datetime64)

        else: # this is the case when we create datetime array from given year, month, day arrays

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

            return np.array(arr_date,dtype=np.datetime64)

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
            self._valsunit_()
        elif dtype.type is np.dtype('str').type:
            dnone = self.nones.todict("str")
            self.vals = str2str(self.vals,regex=regex,**dnone)
        elif dtype.type is np.dtype('datetime64').type:
            dnone = self.nones.todict("str","datetime64")
            self.vals = str2datetime64(self.vals,regex=regex,**dnone)
        else:
            raise TypeError("dtype can be either int, float, str or np.datetime64")

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
        """It outputs ColArray.vals in string format. If num is not defined it edites numpy.ndarray.__str__()."""

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
        """Console representation of ColArray."""

        return f'ColArray(head="{self.head}", unit="{self.unit}", info="{self.info}", vals={self._valstr_(2)})'

    def __str__(self):
        """Print representation of ColArray."""

        string = "{}\n"*4

        head = f"head\t: {self.head}"
        unit = f"unit\t: {self.unit}"
        info = f"info\t: {self.info}"
        vals = f"vals\t: {self._valstr_(2)}"

        return string.format(head,unit,info,vals)

    """COMPARISON"""
    def isnone(self):
        """It return boolean array by comparing the values of vals to none types defined by ColArray."""

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
        """It checks whether ColArray has unit or not."""

        if self.vals.dtype.type is np.float64:
            return self.unit=="dimensionless"
        else:
            return True

    def __lt__(self,other):
        """Implementing '<' operator."""
        
        if isinstance(other,ColArray):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            return self.vals<other.vals
        else:
            return self.vals<other

    def __le__(self,other):
        """Implementing '<=' operator."""
        
        if isinstance(other,ColArray):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            return self.vals<=other.vals
        else:
            return self.vals<=other

    def __gt__(self,other):
        """Implementing '>' operator."""
        
        if isinstance(other,ColArray):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            return self.vals>other.vals
        else:
            return self.vals>other

    def __ge__(self,other):
        """Implementing '>=' operator."""

        if isinstance(other,ColArray):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            return self.vals>=other.vals
        else:
            return self.vals>=other

    def __eq__(self,other,tol=1e-12):
        """Implementing '==' operator."""

        if isinstance(other,ColArray):
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
        
        if isinstance(other,ColArray):
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

    """CONTAINER METHODS"""
    def min(self):
        """It returns none-minimum value of ColArray."""

        if self.vals.dtype.type is np.int32:
            return self.vals[~self.isnone()].min()
        elif self.vals.dtype.type is np.float64:
            return np.nanmin(self.vals)
        elif self.vals.dtype.type is np.str_:
            return min(self.vals[~self.isnone()],key=len)
        elif self.vals.dtype.type is np.datetime64:
            return np.nanmin(self.vals)

    def max(self):
        """It returns none-maximum value of ColArray."""

        if self.vals.dtype.type is np.int32:
            return self.vals[~self.isnone()].max()
        elif self.vals.dtype.type is np.float64:
            return np.nanmax(self.vals)
        elif self.vals.dtype.type is np.str_:
            return max(self.vals[~self.isnone()],key=len)
        elif self.vals.dtype.type is np.datetime64:
            return np.nanmax(self.vals)

    def maxchar(self,string=False):
        """It returns the maximum character count in stringified ColArray."""

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

        column_ = copy.copy(self)
        column_.vals = self.vals[key]

        return column_

    """OPERATIONS"""
    def convert(self,unit):
        """It converts the vals to the new unit."""

        if self.unit!=unit:

            ur = pint.UnitRegistry()

            vals = ur.Quantity(self.vals,self.unit).to(unit).magnitude

            column_ = copy.copy(self)

            column_.vals = vals
            column_._valsunit_(unit)

        return column_
    
    def shift(self,delta,deltaunit=None):
        """Shifting the entries depending on its dtype."""

        if self.vals.dtype.type is np.int32:
            vals_shifted = self.vals+delta
        elif self.vals.dtype.type is np.float64:
            other = ColArray(vals=delta,unit=deltaunit)
            other = other.convert(self.unit)
            vals_shifted = self.vals+other.vals
        elif self.vals.dtype.type is np.str_:
            vals_shifted = np.char.add(" "*delta,self.vals)
        elif self.vals.dtype.type is np.datetime64:

            if deltaunit is None:

                arr_y = self.year[:]
                arr_m = self.month[:]

                if delta=="BOM":
                    arr_d = 1
                elif delta=="EOM":
                    arr_d = self.eom[:]

                vals_shifted = self._arrdatetime64_(year=arr_y,month=arr_m,day=arr_d)

            elif deltaunit == "Y":

                year0 = self.year
                year1 = year0+delta

                feb28_bool = np.logical_and(self.month==2,self.day==28)
                feb29_bool = np.logical_and(self.month==2,self.day==29)

                year0_leap_bool = year0%4==0
                year0_leap_bool[year0%100==0] = False
                year0_leap_bool[year0%400==0] = True
                year0_leap_bool[self.month>2] = False
                year0_leap_bool[feb29_bool] = False

                year1_leap_bool = year1%4==0
                year1_leap_bool[year1%100==0] = False
                year1_leap_bool[year1%400==0] = True
                year1_leap_bool[self.month>2] = False
                year1_leap_bool[np.logical_and(~year0_leap_bool,feb28_bool)] = False
                year1_leap_bool[feb29_bool] = False
                
                leap_year_count4 = year1//4-year0//4
                leap_year_count100 = year1//100-year0//100
                leap_year_count400 = year1//400-year0//400
                leap_year_count = leap_year_count4-leap_year_count100+leap_year_count400
                
                day_arr = 365*delta+leap_year_count+year0_leap_bool-year1_leap_bool
                day_arr = day_arr.astype("str")

                day_arr[self.isnone()] = "NaT"

                vals_shifted = self.vals+day_arr.astype("timedelta64[D]")

            elif deltaunit == "M":

                vals_shifted = []

                delta = relativedelta.relativedelta(months=delta)

                for val in self.vals.tolist():
                    if val is not None:
                        vals_shifted.append(val+delta)
                    else:
                        vals_shifted.append(None)

                vals_shifted = np.array(vals_shifted,dtype=np.datetime64)

            else:

                timedelta = np.timedelta64(delta,deltaunit)

                vals_shifted = self.vals+timedelta

        column_ = copy.copy(self)
        column_.vals = vals_shifted

        return column_

    def __add__(self,other):
        """Implementing '+' operator."""

        column_ = copy.copy(self)

        if isinstance(other,ColArray):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            column_.vals += other.vals
        else:
            column_.vals += other
            
        return column_

    def __floordiv__(self,other):
        """Implementing '//' operator."""

        column_ = copy.copy(self)

        if isinstance(other,ColArray):
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
            column_._valsunit_(unit)

        else:
            column_.vals = self.vals//other
            
        return column_

    def __mod__(self,other):
        """Implementing '%' operator."""

        column_ = copy.copy(self)

        if isinstance(other,ColArray):
        #     ureg = pint.UnitRegistry()
        #     unit = ureg.Unit(f"{self.unit}/({other.unit})").__str__()
        #     return ColArray(self.vals%other.vals,unit=unit)
            if other.nondim():
                column_.vals = self.vals%other.vals
            else:
                raise TypeError(f"unsupported operand type for dimensional ColArray arrays.")
        else:
            column_.vals = self.vals%other
            
        return column_

    def __mul__(self,other):
        """Implementing '*' operator."""

        column_ = copy.copy(self)

        if isinstance(other,ColArray):
            # ur = pint.UnitRegistry()
            # unit = ur.Unit(f"{self.unit}*{other.unit}").__str__()

            if other.nondim():
                unit = self.unit
            elif self.nondim():
                unit = other.unit
            else:
                unit = f"{self.unit}*{other.unit}"

            column_.vals = self.vals*other.vals
            column_._valsunit_(unit)
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
            column_._valsunit_(f"({self.unit})**{other}")
        else:
            raise TypeError(f"unsupported operand type for non-int or non-float entries.")

        return column_

    def __sub__(self,other):
        """Implementing '-' operator."""

        column_ = copy.copy(self)

        if isinstance(other,ColArray):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            column_.vals = self.vals-other.vals
        else:
            column_.vals = self.vals-other
        
        return column_

    def __truediv__(self,other):
        """Implementing '/' operator."""

        column_ = copy.copy(self)

        if isinstance(other,ColArray):
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
            column_._valsunit_(unit)
        else:
            column_.vals = self.vals/other
        
        return column_

    """PROPERTY METHODS"""
    @property
    def dtype(self):
        """Return dtype of ColArray.vals."""

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
    def eom(self):

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

class DataFrame(DirBase):
    """It stores equal-size one-dimensional numpy arrays in a list."""

    print_cols = None
    print_rows = None
    print_rlim = 20

    """INITIALIZATION"""
    def __init__(self,**kwargs):
        """Initializes DataFrame with headers & running and parent class DirBase."""

        homedir = kwargs.get('homedir')
        filedir = kwargs.get('filedir')

        super().__init__(homedir=homedir,filedir=filedir)

        if homedir is not None:
            homedir = kwargs.pop('homedir')

        if filedir is not None:
            filedir = kwargs.pop('filedir')

        self.running = []

        for key,vals in kwargs.items():
            self[key] = vals

    """REPRESENTATION"""
    def __str__(self):
        """It prints to the console limited number of rows with headers."""

        if self.print_cols is None:
            cols = range(len(self.running))
        else:
            cols = self.print_cols

        fstring = "{}\n".format("{}\t"*len(cols))

        headers = self.heads
        unlines = ["-"*len(headers[col]) for col in cols]

        string = ""

        try:
            nrows = self.running[0].vals.size
        except IndexError:
            nrows = 0

        if self.print_rows is None:

            if nrows<=int(self.print_rlim):

                rows = range(nrows)

                string += fstring.format(*headers)
                string += fstring.format(*unlines)

                for row in rows:
                    string += fstring.format(*[self.running[col].vals[row] for col in cols])

            else:

                rows1 = list(range(int(self.print_rlim/2)))
                rows2 = list(range(-1,-int(self.print_rlim/2)-1,-1))

                rows2.reverse()

                string += fstring.format(*headers)
                string += fstring.format(*unlines)

                for row in rows1:
                    string += fstring.format(*[self.running[col][row] for col in cols])

                string += "...\n"*3

                for row in rows2:
                    string += fstring.format(*[self.running[col][row] for col in cols])

        else:

            string += fstring.format(*headers)
            string += fstring.format(*unlines)

            for row in self.print_rows:
                string += fstring.format(*[self.running[col][row] for col in cols])

        return string

    """ATTRIBUTES AND GLOSSARY"""
    def add_attrs(self,**kwargs):

        for key,value in kwargs.items():

            if not hasattr(self,key):
                setattr(self,key,value)
                continue
            else:
                key_edited = f"{key}_{1}"

            for i in range(2,100):
                if hasattr(self,key_edited):
                    key_edited = f"{key}_{i}"
                else:
                    break
            else:
                logging.critical(f"Could not add Glossary, copy limit of key reached 100!")
            
            setattr(self,key_edited,value)

            logging.info(f"Added value after replacing {key} with {key_edited}.")

    def add_glossary(self,title,*args,**kwargs):

        if not hasattr(self,title):

            setattr(self,title,Glossary(*args,**kwargs))

        else:

            logging.warning(f"{title} already exists.")

    """CONTAINER METHODS"""
    def index(self,*args):

        indices = []

        for key in args:

            if isinstance(key,str):
                indices.append(self.heads.index(key))
            elif isinstance(key,int):
                indices.append(key)
            else:
                raise TypeError(f"The input/s can be str or int, not type={type(key)}.")

        if len(args)==0:
            raise TypeError(f"Index expected at least 1 argument, got 0")
        else:
            return tuple(indices)

    def __setitem__(self,key,vals):

        if not isinstance(key,str):
            raise TypeError(f"The key can be str, not type={type(key)}.")

        if key in self.heads:
            index_key = self.heads.index(key)
            self.running[index_key] = ColArray(vals=vals,head=key)
        else:
            self.running.append(ColArray(vals=vals,head=key))

    def __iter__(self):

        return iter(self.running)

    def __len__(self):

        return len(self.running)

    def __getitem__(self,key):

        if key is None:
            key = slice(None,None,None)

        if isinstance(key,int):
            return self.running[key]
        elif isinstance(key,str):
            return self.running[self.index(key)[0]]
        elif isinstance(key,range):
            return [np.asarray(self[KEY].vals) for KEY in key]
        elif isinstance(key,list):
            return [np.asarray(self[KEY].vals) for KEY in key]
        elif isinstance(key,tuple):
            return [np.asarray(self[KEY].vals) for KEY in key]
        elif isinstance(key,slice):
            return [np.asarray(column.vals) for column in self.running[key]]
        else:
            raise TypeError(f"The key cannot be type={type(key)}.") 

    """OPERATIONS"""
    def str2cols(self,col=None,delimiter=None,maxsplit=None):

        if isinstance(col,int):
            idcol = col
        elif isinstance(col,str):
            idcol = self.index(col)[0]
        else:
            logging.critical(f"Excpected col is int or str, input is {type(col)}")

        column_ = self.running.pop(idcol)
        
        header_string = column_.head
        column_string = np.asarray(column_.vals)

        if maxsplit is None:
            maxsplit = np.char.count(column_,delimiter).max()

        headers = [header_string,]

        [headers.append("{}_{}".format(header_string,index)) for index in range(1,maxsplit+1)]

        running = []

        for index,string in enumerate(column_string):

            # string = re.sub(delimiter+'+',delimiter,string)
            row = string.split(delimiter,maxsplit=maxsplit)

            if maxsplit+1>len(row):
                indices = range(maxsplit+1-len(row))
                [row.append("") for index in indices]

            running.append(row)

        running = np.array(running,dtype=str).T

        for index,(vals,head) in enumerate(zip(running,headers),start=idcol):
            self.running.insert(index,ColArray(vals=vals,head=head))

        # line = re.sub(r"[^\w]","",line)
        # line = "_"+line if line[0].isnumeric() else line
        # vmatch = np.vectorize(lambda x: bool(re.compile('[Ab]').match(x)))
        
        # self.headers = self._headers
        # self.running = [np.asarray(column) for column in self._running]

    def cols2str(self,cols=None,header_new=None,fstring=None):

        idcols = self.index(*cols)

        column_new = self[cols]

        if fstring is None:
            fstring = ("{} "*len(column_new)).strip()

        vprint = np.vectorize(lambda *args: fstring.format(*args))

        # column_new = [np.asarray(self._running[idcol]) for idcol in idcols]

        column_new = vprint(*column_new)

        if header_new is None:
            fstring_header = ("{}_"*len(column_new))[:-1]
            header_new = fstring_header.format(*[self.heads[idcol] for idcol in idcols])

        self[header_new] = column_new
        # self._headers.append(header_new)
        # self._running.append(column_new)

        # self.headers = self._headers
        # self.running = [np.asarray(column) for column in self._running]
            
    def sort(self,cols=None,reverse=False,inplace=False,returnFlag=False):

        if cols is None:
            idcols = range(len(self._running))
        elif isinstance(cols,int):
            idcols = (cols,)
        elif isinstance(cols,str):
            idcols = (self._headers.index(cols),)
        elif isinstance(cols,list) or isinstance(cols,tuple):
            if isinstance(cols[0],int):
                idcols = cols
            elif isinstance(cols[0],str):
                idcols = [self._headers.index(col) for col in cols]
            else:
                logging.critical(f"Expected cols is the list or tuple of integer or string; input, however, is {cols}")
        else:
            logging.critical(f"Other than None, expected cols is integer or string or their list or tuples; input, however, is {cols}")

        columns = [self._running[idcol] for idcol in idcols]

        columns.reverse()

        sort_index = np.lexsort(columns)

        if reverse:
            sort_index = np.flip(sort_index)

        if inplace:
            self._running = [column[sort_index] for column in self._running]
            self.running = [np.asarray(column) for column in self._running]
        else:
            self.running = [np.asarray(column[sort_index]) for column in self._running]

        if returnFlag:
            return sort_index

    def filter(self,cols=None,keywords=None,regex=None,year=None):
        """It should allow multiple header indices filtering"""

        if cols is None:
            return
        elif isinstance(cols,int):
            idcols = (cols,)
        elif isinstance(cols,str):
            idcols = (self._headers.index(cols),)
        elif isinstance(cols,list) or isinstance(cols,tuple):
            if isinstance(cols[0],int):
                idcols = cols
            elif isinstance(cols[0],str):
                idcols = [self._headers.index(col) for col in cols]
            else:
                logging.critical(f"Expected cols is the list or tuple of integer or string; input is {cols}")
        else:
            logging.critical(f"Expected cols is integer or string or their list or tuples; input is {cols}")

        if keywords is not None:
            match_array = np.array(keywords).reshape((-1,1))
            match_index = np.any(self._running[idcols[0]]==match_array,axis=0)
        elif regex is not None:
            match_vectr = np.vectorize(lambda x: bool(re.compile(regex).match(x)))
            match_index = match_vectr(self._running[idcols[0]])
        elif year is not None:
            match_vectr = np.vectorize(lambda x: x.year==year)
            match_index = match_vectr(self._running[idcols[0]].tolist())

        if inplace:
            self._running = [column[match_index] for column in self._running]
            self.running = [np.asarray(column) for column in self._running]
        else:
            self.running = [np.asarray(column[match_index]) for column in self._running]

    def unique(self,cols):

        if isinstance(cols,int):
            cols = (cols,)
        elif isinstance(cols,str):
            cols = (cols,)

        idcols = self.index(*cols)

        Z = []

        for idcol in idcols:
            column_ = self[idcol][:]
            column_.astype("str")
            Z.append(column_.vals)

        Z = np.array(Z,dtype=str).T

        _,idrows = np.unique(Z,axis=0,return_index=True)

        # if inplace:
        self.running = [column[idrows] for column in self.running]
            # self.running = [np.asarray(column) for column in self._running]
        # else:
        #     self.running = [np.asarray(column[idrows]) for column in self.running]

    """CONTEXT MANAGERS"""
    def write(self,filepath,fstring=None,**kwargs):
        """It writes text form of DataFrame."""

        header_fstring = ("{}\t"*len(self._headers))[:-1]+"\n"

        if fstring is None:
            running_fstring = ("{}\t"*len(self._headers))[:-1]+"\n"
        else:
            running_fstring = fstring

        vprint = np.vectorize(lambda *args: running_fstring.format(*args))

        with open(filepath,"w",encoding='utf-8') as wfile:
            wfile.write(header_fstring.format(*self._headers))
            for line in vprint(*self._running):
                wfile.write(line)

    def writeb(self,filename):
        """It writes binary form of DataFrame."""

        filepath = self.get_abspath(f"{filename}.npz",homeFlag=True)

        for header,column in zip(self._headers,self._running):
            kwargs[header] = column

        np.savez_compressed(filepath,**kwargs)

    """PROPERTY METHODS"""
    @property
    def types(self):

        return [column.vals.dtype.type for column in self.running]

    @property
    def heads(self):

        return [column.head for column in self.running]

    @property
    def units(self):

        return [column.unit for column in self.running]

    @property
    def infos(self):

        return [column.info for column in self.running]

class Glossary():
    """It is a table of lines vs heads"""

    def __init__(self,*args,**kwargs):

        self.lines = []
        self.heads = []
        self.forms = []

        for arg in args:
            self.heads.append(arg.lower())
            self.forms.append(str)

        for key,value in kwargs.items():
            self.heads.append(key.lower())
            self.forms.append(value)

        self.forms[0] = str

    def add_line(self,**kwargs):

        line = {}

        for index,head in enumerate(self.heads):

            if head in kwargs.keys():
                try:
                    line[head] = self.forms[index](kwargs[head])
                except ValueError:
                    line[head] = kwargs[head]
                finally:
                    kwargs.pop(head)
            elif index==0:
                raise KeyError(f"Missing {self.heads[0]}, it must be defined!")
            else:
                line[head] = " "

        self.lines.append(line)

    def __getitem__(self,key):
        
        if isinstance(key,slice):
            return self.lines[key]
        elif isinstance(key,int):
            return self.lines[key]
        elif isinstance(key,str):
            for line in self:
                if key==line[self.heads[0]]:
                    return line
            else:
                raise ValueError(f"Glossary does not contain line with {key} in its {self.heads[0]}.")
        elif isinstance(key,tuple):
            key1,key2 = key
            lines = self[key1]
            if isinstance(lines,dict):
                return lines[key2]
            elif isinstance(lines,list):
                column = []
                for line in lines:
                    column.append(line[key2])
                return column
        else:
            raise TypeError(f"Glossary key can not be {type(key)}, int, slice or str is accepted.")

    def __repr__(self):

        fstring = ""
        
        underline = []

        for head in self.heads:
            
            column = self[:,head]
            column.append(head)
            
            char_count = max([len(str(value)) for value in column])

            fstring += f"{{:<{char_count}}}   "
            
            underline.append("-"*char_count)

        fstring += "\n"

        text = fstring.format(*[head.capitalize() for head in self.heads])
        
        text += fstring.format(*underline)
        
        for line in self:
            text += fstring.format(*line.values())

        return text

    def __iter__(self):

        return iter(self.lines)

    def __len__(self):

        return len(self.lines)

def loadtxt(path,classname=None,**kwargs):

    if classname is None:
        if path.lower().endswith(".txt"):
            obj = RegText()
        elif path.lower().endswith(".las"):
            obj = LogASCII()
        elif path.lower().endswith(".xlsx"):
            obj = Excel()
        elif path.lower().endswith(".vtk"):
            obj = VTKit()
        else:
            obj = IrrText()
    elif classname.lower()=="regtext":
        obj = RegText()
    elif classname.lower()=="logascii":
        obj = LogASCII()
    elif classname.lower()=="excel":
        obj = Excel()
    elif classname.lower()=="irrtext":
        obj = IrrText()
    elif classname.lower()=="wschedule":
        obj = WSchedule()
    elif classname.lower()=="vtkit":
        obj = VTKit()

    frame = obj.read(path,**kwargs)

    return frame

# Collective Data Input/Output Classes

class RegText(DataFrame):

    def __init__(self,filepaths=None,**kwargs):

        super().__init__(**kwargs)

        self.frames = []

        self.add_frames(filepaths,**kwargs)

    def add_frames(self,filepaths,**kwargs):

        if filepaths is None:
            return
        if not isinstance(filepaths,list) and not isinstance(filepaths,tuple):
            filepaths = (filepaths,)

        for filepath in filepaths:
            self.frames.append(self.read(filepath,**kwargs))
            logging.info(f"Loaded {filepath} as expected.")

    def read(self,filepath,delimiter="\t",comments="#",skiprows=None,nondigitflag=False):

        filepath = self.get_abspath(filepath)

        frame = DataFrame(filedir=filepath)

        frame.filepath = filepath

        with open(filepath,mode="r",encoding="latin1") as text:

            if skiprows is None:
                skiprows = 0
                line = next(text).split("\n")[0]
                while not line.split(delimiter)[0].isdigit():
                    skiprows += 1
                    line = next(text).split("\n")[0]
            else:
                for _ in range(skiprows):
                    line = next(text)

            line = next(text).split("\n")[0]

        if nondigitflag:
            row = line.split(delimiter)
            dtypes = [float if column.isdigit() else str for column in row]
            columns = []
            for index,dtype in enumerate(dtypes):
                column = np.loadtxt(filepath,dtype=dtype,delimiter=delimiter,skiprows=skiprows,usecols=[index],encoding="latin1")
                columns.append(column)
        else:
            data = np.loadtxt(filepath,comments="#",delimiter=delimiter,skiprows=skiprows,encoding="latin1")
            columns = [column for column in data.transpose()]

        frame.set_running(*columns,init=True)

        return frame

class LogASCII(DataFrame):

    def __init__(self,filepaths=None,**kwargs):

        super().__init__(**kwargs)

        self.frames = []

        self.add_frames(filepaths,**kwargs)

    def add_frames(self,filepaths,**kwargs):

        if filepaths is None:
            return

        if not isinstance(filepaths,list) and not isinstance(filepaths,tuple):
            filepaths = (filepaths,)

        for filepath in filepaths:
            self.frames.append(self.read(filepath,**kwargs))
            logging.info(f"Loaded {filepath} as expected.")

    def read(self,filepath):

        filepath = self.get_abspath(filepath)

        datasection = "{}ASCII".format("~")

        skiprows = 1

        frame = DataFrame(filedir=filepath)

        with open(filepath,"r",encoding="latin1") as text:

            line = next(text).strip()

            while not line.startswith(datasection[:2]):

                if line.startswith("~"):

                    title = line[1:].split()[0].lower()

                    mnemonics,units,values,descriptions = [],[],[],[]

                elif len(line)<1:
                    pass

                elif line.startswith("#"):
                    pass

                elif line.find(".")<0:
                    pass

                elif line.find(":")<0:
                    pass

                elif line.index(".")>line.index(":"):
                    pass

                else:

                    line = re.sub(r'[^\x00-\x7F]+','',line)

                    mnemonic,rest = line.split(".",maxsplit=1)
                    rest,descrptn = rest.split(":",maxsplit=1)

                    rest = rest.rstrip()

                    if len(rest)==0:
                        unit,value = "",""
                    elif rest.startswith(" ") or rest.startswith("\t"):
                        unit,value = "",rest.lstrip()
                    elif len(rest.split(" ",maxsplit=1))==1:
                        unit,value = rest,""
                    else:
                        unit,value = rest.split(" ",maxsplit=1)

                    mnemonics.append(mnemonic.strip())
                    units.append(unit.strip())

                    try:
                        value = int(value.strip())
                    except ValueError:
                        try:
                            value = float(value.strip())
                        except ValueError:
                            value = value.strip()

                    values.append(value)
                    descriptions.append(descrptn.strip())

                skiprows += 1

                line = next(text).strip()

                if line.startswith("~"):

                    if title=="version":

                        vnumb = "LAS {}".format(values[mnemonics.index("VERS")])
                        vinfo = descriptions[mnemonics.index("VERS")]
                        mtype = "Un-wrapped" if values[mnemonics.index("WRAP")]=="NO" else "Wrapped"
                        minfo = descriptions[mnemonics.index("WRAP")]

                        frame.add_attrs(info=vnumb)
                        frame.add_attrs(infodetail=vinfo)
                        frame.add_attrs(mode=mtype)
                        frame.add_attrs(modedetail=minfo)

                    elif title=="curve":

                        frame.set_headers(*mnemonics)
                        frame.add_attrs(units=units)
                        frame.add_attrs(details=descriptions)

                    else:

                        frame.add_glossary(title,
                            mnemonic=mnemonics,
                            unit=units,
                            value=values,
                            description=descriptions)

            line = next(text).strip()

            row = re.sub(' +',' ',line).split(" ")

            dtypes = [float if isnumber(cell) else str for cell in row]

        usecols = None

        if all([dtype is float for dtype in dtypes]):

            logdata = np.loadtxt(filepath,
                comments="#",
                skiprows=skiprows,
                usecols=usecols,
                encoding="latin1")

            if hasattr(frame,"well"):
                try:
                    value_null = frame.well.get_row(mnemonic="NULL")["value"]
                except TypeError:
                    value_null = -999.25
                except KeyError:
                    value_null = -999.25
            else:
                value_null = -999.25

            logdata[logdata==value_null] = np.nan

            columns = [column for column in logdata.transpose()]

        else:

            # usecols_flt = [index for index,dtype in enumerate(dtypes) if dtype is float]
            # usecols_str = [index for index,dtype in enumerate(dtypes) if dtype is str]

            columns = []

            for index,dtype in enumerate(dtypes):

                column = np.loadtxt(filepath,
                    dtype=dtype,
                    skiprows=skiprows,
                    usecols=[index],
                    encoding="latin1")

                columns.append(column)

        frame.set_running(*columns,cols=range(len(columns)))

        return frame

    def printwells(self,idframes=None):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            frame = self.frames[index]

            print("\n\tWELL #{}".format(frame.well.get_row(mnemonic="WELL")["value"]))

            # iterator = zip(frame.well["mnemonic"],frame.well["units"],frame.well["value"],frame.well.descriptions)

            iterator = zip(*frame.well.get_columns())

            for mnem,unit,value,descr in iterator:
                print(f"{descr} ({mnem}):\t\t{value} [{unit}]")

    def printcurves(self,idframes=None,mnemonic_space=33,tab_space=8):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            frame = self.frames[index]

            iterator = zip(frame.headers,frame.units,frame.details,frame.running)

            # file.write("\n\tLOG NUMBER {}\n".format(idframes))
            print("\n\tLOG NUMBER {}".format(index))

            for header,unit,detail,column in iterator:

                if np.all(np.isnan(column)):
                    minXval = np.nan
                    maxXval = np.nan
                else:
                    minXval = np.nanmin(column)
                    maxXval = np.nanmax(column)

                tab_num = math.ceil((mnemonic_space-len(header))/tab_space)
                tab_spc = "\t"*tab_num if tab_num>0 else "\t"

                # file.write("Curve: {}{}Units: {}\tMin: {}\tMax: {}\tDescription: {}\n".format(
                #     curve.mnemonic,tab_spc,curve.unit,minXval,maxXval,curve.descr))
                print("Curve: {}{}Units: {}\tMin: {}\tMax: {}\tDescription: {}".format(
                    header,tab_spc,unit,minXval,maxXval,detail))

    def flip(self,idframes=None):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for index in idframes:

            columns = [np.flip(column) for column in self.frames[index].running]

            self.frames[index].set_running(*columns,cols=range(len(columns)))
            
    def set_interval(self,top,bottom,idframes=None,inplace=False):

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        self.top = top
        self.bottom = bottom

        self.gross_thickness = self.bottom-self.top

        for index in idframes:

            depth = self.frames[index].columns(0)

            depth_cond = np.logical_and(depth>self.top,depth<self.bottom)

            if inplace:
                self.frames[index]._running = [column[depth_cond] for column in self.frames[index]._running]
                self.frames[index].running = [np.asarray(column) for column in self.frames[index]._running]
            else:
                self.frames[index].running = [np.asarray(column[depth_cond]) for column in self.frames[index]._running]

    def get_interval(self,top,bottom,idframes=None,curveID=None):

        returningList = []

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for idfile in idframes:

            las = self.frames[idfile]

            try:
                depth = las.columns("MD")
            except ValueError:
                depth = las.columns("DEPT")

            depth_cond = np.logical_and(depth>top,depth<bottom)

            if curveID is None:
                returningList.append(depth_cond)
            else:
                returningList.append(las.columns(curveID)[depth_cond])

        return returningList

    def get_resampled(self,depthsR,depthsO,dataO):

        lowerend = depthsR<depthsO.min()
        upperend = depthsR>depthsO.max()

        interior = np.logical_and(~lowerend,~upperend)

        depths_interior = depthsR[interior]

        indices_lower = np.empty(depths_interior.shape,dtype=int)
        indices_upper = np.empty(depths_interior.shape,dtype=int)

        for index,depth in enumerate(depths_interior):

            diff = depthsO-depth

            indices_lower[index] = np.where(diff<0,diff,-np.inf).argmax()
            indices_upper[index] = np.where(diff>0,diff,np.inf).argmin()

        grads = (depths_interior-depthsO[indices_lower])/(depthsO[indices_upper]-depthsO[indices_lower])

        dataR = np.empty(depthsR.shape,dtype=float)

        dataR[lowerend] = np.nan
        dataR[interior] = dataO[indices_lower]+grads*(dataO[indices_upper]-dataO[indices_lower])
        dataR[upperend] = np.nan

        return dataR

    def resample(self,depthsFID=None,depthsR=None,fileID=None,curveID=None):

        """

        depthsFID:  The index of file id from which to take new depthsR
                    where new curve data will be calculated;

        depthsR:    The numpy array of new depthsR
                    where new curve data will be calculated;
        
        fileID:     The index of file to resample;
                    If None, all files will be resampled;
        
        curveID:    The index of curve in the las file to resample;
                    If None, all curves in the file will be resampled;
                    Else if fileID is not None, resampled data will be returned;

        """

        if depthsFID is not None:
            try:
                depthsR = self.frames[depthsFID].columns("MD")
            except ValueError:
                depthsR = self.frames[depthsFID].columns("DEPT")

        if fileID is None:
            fileIDs = range(len(self.frames))
        else:
            fileIDs = range(fileID,fileID+1)

        for indexI in fileIDs:

            if depthsFID is not None:
                if indexI==depthsFID:
                    continue

            las = self.frames[indexI]

            try:
                depthsO = las.columns("MD")
            except ValueError:
                depthsO = las.columns("DEPT")

            lowerend = depthsR<depthsO.min()
            upperend = depthsR>depthsO.max()

            interior = np.logical_and(~lowerend,~upperend)

            depths_interior = depthsR[interior]

            diff = depthsO-depths_interior.reshape((-1,1))

            indices_lower = np.where(diff<0,diff,-np.inf).argmax(axis=1)
            indices_upper = np.where(diff>0,diff,np.inf).argmin(axis=1)

            grads = (depths_interior-depthsO[indices_lower])/(depthsO[indices_upper]-depthsO[indices_lower])

            if curveID is None:
                running = [depthsR]
                # self.frames[indexI].set_running(depthsR,cols=0,init=True)

            if curveID is None:
                curveIDs = range(1,len(las.running))
            else:
                curveIDs = range(curveID,curveID+1)

            for indexJ in curveIDs:

                curve = las.columns(indexJ)

                dataR = np.empty(depthsR.shape,dtype=float)

                dataR[lowerend] = np.nan
                dataR[interior] = curve[indices_lower]+grads*(curve[indices_upper]-curve[indices_lower])
                dataR[upperend] = np.nan

                if curveID is None:
                    running.append(dataR)

            heads = self.frames[indexI].headers

            if curveID is None:
                curveIDs = list(curveIDs)
                curveIDs.insert(0,0)
                self.frames[indexI].set_running(*running,cols=curveIDs,init=True)
                self.frames[indexI].set_headers(*heads,cols=curveIDs,init=False)
            elif fileID is not None:
                return dataR

    def merge(self,fileIDs,curveNames):

        if isinstance(fileIDs,int):

            try:
                depth = self.frames[fileIDs]["MD"]
            except KeyError:
                depth = self.frames[fileIDs]["DEPT"]

            xvals1 = self.frames[fileIDs][curveNames[0]]

            for curveName in curveNames[1:]:

                xvals2 = self.frames[fileIDs][curveName]

                xvals1[np.isnan(xvals1)] = xvals2[np.isnan(xvals1)]

            return depth,xvals1

        elif np.unique(np.array(fileIDs)).size==len(fileIDs):

            if isinstance(curveNames,str):
                curveNames = (curveNames,)*len(fileIDs)

            depth = np.array([])
            xvals = np.array([])

            for (fileID,curveName) in zip(fileIDs,curveNames):

                try:
                    depth_loc = self.frames[fileID]["MD"]
                except KeyError:
                    depth_loc = self.frames[fileID]["DEPT"]

                xvals_loc = self.frames[fileID][curveName]

                depth_loc = depth_loc[~np.isnan(xvals_loc)]
                xvals_loc = xvals_loc[~np.isnan(xvals_loc)]

                depth_max = 0 if depth.size==0 else depth.max()

                depth = np.append(depth,depth_loc[depth_loc>depth_max])
                xvals = np.append(xvals,xvals_loc[depth_loc>depth_max])

            return depth,xvals

    def write(self,filepath,mnemonics,data,idfile=None,units=None,descriptions=None,values=None):

        """
        filepath:       It will write a lasio.LASFile to the given filepath
        idfile:         The file index which to write to the given filepath
                        If idfile is None, new lasio.LASFile will be created

        kwargs:         These are mnemonics, data, units, descriptions, values
        """

        if idfile is not None:

            lasfile = self.frames[idfile]

        else:

            lasfile = lasio.LASFile()

            lasfile.well.DATE = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

            depthExistFlag = False

            for mnemonic in mnemonics:
                if mnemonic=="MD" or mnemonic=="DEPT" or mnemonic=="DEPTH":
                    depthExistFlag = True
                    break

            if not depthExistFlag:
                curve = lasio.CurveItem(
                    mnemonic="DEPT",
                    unit="",
                    value="",
                    descr="Depth index",
                    data=np.arange(data[0].size))
                lasfile.append_curve_item(curve)            

        for index,(mnemonic,datum) in enumerate(zip(mnemonics,data)):

            if units is not None:
                unit = units[index]
            else:
                unit = ""

            if descriptions is not None:
                description = descriptions[index]
            else:
                description = ""

            if values is not None:
                value = values[index]
            else:
                value = ""

            curve = lasio.CurveItem(mnemonic=mnemonic,data=datum,unit=unit,descr=description,value=value)

            lasfile.append_curve_item(curve)

        with open(filepath, mode='w') as filePathToWrite:
            lasfile.write(filePathToWrite)

class Excel(DataFrame):

    def __init__(self,filepaths=None,**kwargs):

        super().__init__(**kwargs)

        self.books = []
        self.sheets = []
        self.frames = []

        self.add_books(filepaths)

    def add_books(self,filepaths):
        """It adds excel workbooks with the filepaths specified to the self.books."""

        if filepaths is None:
            return

        if not isinstance(filepaths,list) and not isinstance(filepaths,tuple):
            filepaths = (filepaths,)

        for filepath in filepaths:

            filepath = self.get_abspath(filepath)

            self.books.append(opxl.load_workbook(filepath,read_only=True,data_only=True))

            logging.info(f"Loaded {filepath} as expected.")

    def add_sheets(self,sheets=None,**kwargs):
        """It add frames from the excel worksheet."""

        if sheets is None:
            sheets = [(idbook,0) for idbook in range(len(self.books))]

        for sheet in sheets:

            idbook,page = sheet

            frame = self.read((idbook,page),**kwargs)

            self.frames.append(frame)

    def read(self,sheet,hrows=0,min_row=1,min_col=1,max_row=None,max_col=None):
        """It reads excel worksheet and returns it as a DataFrame."""

        idbook,page = sheet

        frame = DataFrame()

        if page is None:
            idsheet = 0
        elif isinstance(page,str):
            scores = []
            for sheetname in self.books[idbook].sheetnames:
                scores.append(SequenceMatcher(None,sheetname,page).ratio())
            idsheet = scores.index(max(scores))
        elif isinstance(page,int):
            idsheet = page
        else:
            logging.critical(f"Expected sheet[1] is either none, str or int, but the input type is {type(sheet[1])}.")

        sheetname = self.books[idbook].sheetnames[idsheet]

        frame.sheetname = sheetname

        rows = self.books[idbook][sheetname].iter_rows(
            min_row=min_row,min_col=min_col,
            max_row=max_row,max_col=max_col,
            values_only=True)

        rows = [row for row in list(rows) if any(row)]

        frame.set_headers(colnum=len(rows[0]),init=True)

        frame.hrows = rows[:hrows]

        frame.set_rows(rows[hrows:])

        return frame

    def merge(self,idframes=None,idcols=None):
        """It merges all the frames as a single DataFrame under the Excel class."""

        if idframes is None:
            idframes = range(len(self.frames))
        elif isinstance(idframes,int):
            idframes = (idframes,)

        for idframe in idframes:

            frame = self.frames[idframe]

            if idcols is None:

                idcols = []

                for header in self._headers:
                    scores = []
                    for header_read in frame._headers:
                        score = SequenceMatcher(None,header,header_read).ratio() if isinstance(header_read,str) else 0
                        scores.append(score)
                    idcols.append(scores.index(max(scores)))

            columns = frame.columns(cols=idcols)

            self.set_running(*columns,cols=range(len(idcols)))

    def write(self,filepath,title):

        wb = opxl.Workbook()

        sheet = wb.active

        if title is not None:
            sheet.title = title

        for line in running:
            sheet.append(line)

        wb.save(filepath)

    def close(self,idbooks=None):

        if idbooks is None:
            idbooks = range(len(self.books))
        elif isinstance(idbooks,int):
            idbooks = (idbooks,)

        for idbook in idbooks:
            self.books[idbook]._archive.close()

class IrrText(DataFrame):

    def __init__(self,filepath,**kwargs):

        super().__init__(**kwargs)

        if filepath is not None:
            self.filepath = self.get_abspath(filepath,homeFlag=False)

    def set_batch(self,filepaths):

        self.filepaths = filepaths

    def read(self,skiprows=0,headerline=None,comment="--",endline="/",endfile="END"):

        # While looping inside the file it does not read lines:
        # - starting with comment phrase, e.g., comment = "--"
        # - after the end of line phrase, e.g., endline = "/"
        # - after the end of file keyword e.g., endfile = "END"

        if headerline is None:
            headerline = skiprows-1
        elif headerline<skiprows:
            headerline = headerline
        else:
            headerline = skiprows-1

        _running = []

        with open(self.filepath,"r") as text:

            for line in text:

                line = line.split('\n')[0].strip()

                line = line.strip(endline)

                line = line.strip()
                line = line.strip("\t")
                line = line.strip()

                if line=="":
                    continue

                if comment is not None:
                    if line[:len(comment)] == comment:
                        continue

                if endfile is not None:
                    if line[:len(endfile)] == endfile:
                        break

                _running.append([line])

        self.title = []

        for _ in range(skiprows):
            self.title.append(_running.pop(0))

        num_cols = len(_running[0])

        if skiprows==0:
            self.set_headers(num_cols=num_cols,init=False)
        elif skiprows!=0:
            self.set_headers(headers=self.title[headerline],init=False)

        nparray = np.array(_running).T

        self._running = [np.asarray(column) for column in nparray]

        self.running = [np.asarray(column) for column in self._running]

    def write(self):

        pass

class WSchedule(DataFrame):

    # KEYWORDS: DATES,COMPDATMD,COMPORD,WCONHIST,WCONINJH,WEFAC,WELOPEN 

    headers    = ["DATE","KEYWORD","DETAILS",]

    dates      = " {} / "#.format(date)
    welspecs   = " '{}'\t1*\t2* / "
    compdatop  = " '{}'\t1*\t{}\t{}\tMD\t{}\t2*\t0.14 / "#.format(wellname,top,bottom,optype)
    compdatsh  = " '{}'\t1*\t{}\t{}\tMD\t{} / "#.format(wellname,top,bottom,optype)
    compord    = " '{}'\tINPUT\t/ "#.format(wellname)
    prodhist   = " '{}'\tOPEN\tORAT\t{}\t{}\t{} / "#.format(wellname,oilrate,waterrate,gasrate)
    injhist    = " '{}'\tWATER\tOPEN\t{}\t7*\tRATE / "#.format(wellname,waterrate)
    wefac      = " '{}'\t{} / "#.format(wellname,efficiency)
    welopen    = " '{}'\tSHUT\t3* / "#.format(wellname)

    def __init__(self):

        pass

    def read(self):

        pass

    def set_subheaders(self,header_index=None,header=None,regex=None,regex_builtin="INC_HEADERS",title="SUB-HEADERS"):

        nparray = np.array(self._running[header_index])

        if regex is None and regex_builtin=="INC_HEADERS":
            regex = r'^[A-Z]+$'                         #for strings with only capital letters no digits
        elif regex is None and regex_builtin=="INC_DATES":
            regex = r'^\d{1,2} [A-Za-z]{3} \d{2}\d{2}?$'   #for strings with [1 or 2 digits][space][3 capital letters][space][2 or 4 digits], e.g. DATES

        vmatch = np.vectorize(lambda x: bool(re.compile(regex).match(x)))

        match_index = vmatch(nparray)

        firstocc = np.argmax(match_index)

        lower = np.where(match_index)[0]
        upper = np.append(lower[1:],nparray.size)

        repeat_count = upper-lower-1

        match_content = nparray[match_index]

        nparray[firstocc:][~match_index[firstocc:]] = np.repeat(match_content,repeat_count)

        self._headers.insert(header_index,title)
        self._running.insert(header_index,np.asarray(nparray))

        for index,column in enumerate(self._running):
            self._running[index] = np.array(self._running[index][firstocc:][~match_index[firstocc:]])

        self.headers = self._headers
        self.running = [np.asarray(column) for column in self._running]

    def get_wells(self,wellname=None):

        pass

    def write(self):

        path = os.path.join(self.workdir,self.schedule_filename)

        with open(path,"w",encoding='utf-8') as wfile:

            welspec = schedule.running[1]=="WELSPECS"
            compdat = schedule.running[1]=="COMPDATMD"
            compord = schedule.running[1]=="COMPORD"
            prodhst = schedule.running[1]=="WCONHIST"
            injdhst = schedule.running[1]=="WCONINJH"
            wefffac = schedule.running[1]=="WEFAC"
            welopen = schedule.running[1]=="WELOPEN"

            for date in np.unique(schedule.running[0]):

                currentdate = schedule.running[0]==date

                currentcont = schedule.running[1][currentdate]

                wfile.write("\n\n")
                wfile.write("DATES\n")
                wfile.write(self.schedule_dates.format(date.strftime("%d %b %Y").upper()))
                wfile.write("\n")
                wfile.write("/\n\n")

                if any(currentcont=="WELSPECS"):
                    indices = np.logical_and(currentdate,welspec)
                    wfile.write("WELSPECS\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="COMPDATMD"):
                    indices = np.logical_and(currentdate,compdat)
                    wfile.write("COMPDATMD\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="COMPORD"):
                    indices = np.logical_and(currentdate,compord)
                    wfile.write("COMPORD\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="WCONHIST"):
                    indices = np.logical_and(currentdate,prodhst)
                    wfile.write("WCONHIST\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="WCONINJH"):
                    indices = np.logical_and(currentdate,injdhst)
                    wfile.write("WCONINJH\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="WEFAC"):
                    indices = np.logical_and(currentdate,wefffac)
                    wfile.write("WEFAC\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

                if any(currentcont=="WELOPEN"):
                    indices = np.logical_and(currentdate,welopen)
                    wfile.write("WELOPEN\n")
                    for detail in schedule.running[2][indices]:
                        wfile.write(detail)
                        wfile.write("\n")
                    wfile.write("/\n\n")

class VTKit(DataFrame):

    def __init__(self):

        pass

    def read(self,):

        pass

    def write(self,):

        pass

# Supporting String Classes

class Alphabet():

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

    def conbvert(self,language="aze",from_="cyril",to="latin"):

        from_lower = getattr(self,f"{language}_{from_}_lower")
        from_upper = getattr(self,f"{language}_{from_}_upper")

        to_lower = getattr(self,f"{language}_{to}_lower")
        to_upper = getattr(self,f"{language}_{to}_upper")

        for from_letter,to_letter in zip(from_lower,to_lower):
            self.string.replace(from_letter,to_letter)

        for from_letter,to_letter in zip(from_upper,to_upper):
            self.string.replace(from_letter,to_letter)

def isnumber(string):

    try:
        float(string)
        return True
    except ValueError:
        return False

if __name__ == "__main__":

    import unittest

    from tests import textiotest

    unittest.main(textiotest)

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