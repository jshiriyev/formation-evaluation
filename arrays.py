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

def flatten(vals,_list=None):

    _list = [] if _list is None else _list

    if type(vals).__module__ == numpy.__name__:
        flatten(vals.tolist(),_list)
    elif isinstance(vals,str):
        _list.append(vals)
    elif hasattr(vals,"__iter__"):
        [flatten(val,_list) for val in list(vals)]
    else:
        _list.append(vals)

    return _list

def array(vals):

    if vals is None:
        _array = numpy.array([numpy.nan])
    elif type(vals).__module__=="numpy":
        _array = vals.flatten()
    elif isinstance(vals,str):
        _array = numpy.array([vals])
    elif isinstance(vals,datetime.datetime):
        _array = numpy.array([vals]).astype('datetime64[s]')
    elif isinstance(vals,datetime.date):
        _array = numpy.array([vals]).astype('datetime64[D]')
    elif hasattr(vals,"__iter__"):
        _array = [flatten(val) for val in list(vals)]
        if len(_array) == 0:
            _array = numpy.array(_array)
        else:
            _array = numpy.concatenate(_array)
    else:
        _array = numpy.array([vals])


        # # arg in vals, the first one
        # if arg is None:
        #     return
        # elif isinstance(arg,int):
        #     return numpy.dtype(type(arg))
        # elif isinstance(arg,float):
        #     return numpy.dtype(type(arg))
        # elif isinstance(arg,str):
        #     arg = _key2column.todatetime(arg)
        #     if arg is None:
        #         return numpy.str_(arg).dtype
        #     else:
        #         return numpy.dtype('datetime64[s]')
        # elif isinstance(arg,datetime.datetime):
        #     return numpy.dtype('datetime64[s]')
        # elif isinstance(arg,datetime.date):
        #     return numpy.dtype('datetime64[D]')
        # elif isinstance(arg,numpy.datetime64):
        #     return arg.dtype
        # else:
        #     return

    return _array

def arange(*args,**kwargs):
    """Generating column by defining dtype and sending the keywords for array creating methods."""
    """It is a special function that takes input and returns linearly spaced data for
    integers, floats, string, datetime"""

    #start stop size

    if len(args)==0:
        pass
    elif len(args)==1:
        kwargs['stop'], = args
    elif len(args)==2:
        kwargs['start'],kwargs['stop'] = args
    elif len(args)==3:
        kwargs['start'],kwargs['stop'],kwargs['size'] = args
    elif len(args)==4:
        kwargs['start'],kwargs['stop'],kwargs['size'],kwargs['dtype'] = args
    else:
        raise TypeError("Arguments are too many!")

    dtype = kwargs.get('dtype')

    if dtype is None:
        dtype = _key2column.get_dtype(args)
    elif isinstance(dtype,str):
        dtype = numpy.dtype(dtype)

    if dtype.type is numpy.dtype('int').type:    
        _array = arrinteger(*args,**kwargs)
    elif dtype.type is numpy.dtype('float').type:
        _array = arrfloat(*args,**kwargs)
    elif dtype.type is numpy.dtype('str').type:
        _array = arrstring(*args,**kwargs)
    elif dtype.type is numpy.dtype('datetime64').type:
        _array = arrdatetime(*args,**kwargs)
    else:
        raise ValueError(f"dtype.type is not int, float, str or datetime64, given {dtype.type=}")

    return _array

def repeat(times,size=None):

    pass

def iterator(*args,size=None):

    arrs = [array1d(arg) for arg in args]

    if size is None:
        size = len(max(arrs,key=len))

    for index,_array in enumerate(arrs):
        repeat_count = int(numpy.ceil(size/_array.size))
        arrs[index] = numpy.tile(_array,repeat_count)[:size]

    return zip(*arrs)
    
class integers(numpy.ndarray):
    """It is a flat subclass of numpy.ndarray that
    includes not-an-integer (none) entries."""

    def __new__(cls,variable,none=None):

        none = -99_999 if none is None else none

        iterable = integers._iterable(variable,none)

        obj = numpy.asarray(iterable).view(cls)

        obj.none = int(none)

        return obj

    def __array_finalize__(self,obj):

        if obj is None: return

        self.none = getattr(obj,'none',-99_999)

    def __add__(self,other):

        none = getattr(other,'none',self.none)

        other = integers(other,none)

        subclass = copy.deepcopy(self)

        lhs_valid = numpy.logical_and(self.isvalid,other.isvalid)
        rhs_valid = other.isvalid if other.size==1 else lhs_valid

        subclass[lhs_valid] += other[rhs_valid]

        subclass[~lhs_valid] = self.none

        return subclass

    def shift(self,delta):

        pass

    @property
    def isvalid(self):
        """It return boolean array True for integer and False for none."""
        return numpy.asarray(self!=self.none)
    
    @property
    def isnone(self):
        """It return boolean array True for none and False for integer."""
        return numpy.asarray(self==self.none)

    @property
    def issorted(self):

        return

    @staticmethod
    def _iterable(variable,none):

        none = int(none)

        iterable = []

        for value in flatten(variable):

            try:
                value = float(value)
            except TypeError:
                value = none
            except ValueError:
                value = none

            iterable.append(int(value))

        return iterable

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

class floats(numpy.ndarray): # HOW TO BEHAVE LIKE NUMPY ARRAY WHILE CORRECTLY FUNCTIONING WITH DIFFERET NAN

    def __init__(self,vals,none=None):

        if none is None:
            self._none = float('nan')
        elif isinstance(none,float):
            self._none = none
        else:
            raise TypeError("none must be float type!")

        self._setvals(vals)

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

    def _iterable(self,vals):

        _vals = []

        for _val in flatten(vals):

            try:
                val = float(_val)
            except ValueError:
                val = self._none

            _vals.append(val)

        self._vals = _vals

    def _arange(*args,size=None,dtype=None):

        if len(args)==0:
            return
        elif len(args)==1:
            _array = array1d(args[0],size)

        if dtype is None:
            return _array
        else:
            return _array.astype(dtype)

class strings(numpy.ndarray): # HOW TO ADD SOME FUNCTIONALITY TO STRING ARRAY

    def __init__(self,vals,none=None):

        if none is None:
            self._none = ''
        elif isinstance(none,str):
            self._none = none
        else:
            raise TypeError("none must be str type!")

        self._setvals(vals)

    def _iterable(self,vals):

        _vals = []

        for _val in flatten(vals):

            try:
                val = str(_val)
            except ValueError:
                val = self._none

            _vals.append(val)

        self._vals = _vals

    def _arange(*args,start='A',stop=None,step=1,size=None,dtype=None):

        kwargs = setargs(*args,**kwargs)

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
            _array = numpy.array(list(itertools.islice(excel_column_headers(),stop_index)))[start_index:stop_index]
            _array = _array[::step]
        else:
            _array = numpy.array(list(itertools.islice(excel_column_headers(),start_index+size*step)))[start_index:]
            _array = _array[::step]

        if dtype is not None:
            return _array.astype(dtype)
        else:
            return _array
    
    def _build_string_from_phrases(*args,phrases=None,repeats=None,size=None,dtype=None):

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if len(args)==0:
            if phrases is None:
                phrases = " "
            if repeats is None:
                repeats = 1

            iterator = _any2column.toiterator(phrases,repeats,size=size)

            _array = numpy.array(["".join([name]*num) for name,num in iterator])

        elif len(args)==1:
            _array = array1d(args[0],size)
        else:
            raise TypeError("Number of arguments can not be larger than 1!")

        if dtype is None:
            return _array
        else:
            return _array.astype(dtype)

class datetimes(numpy.ndarray): # HOW TO ADD SOME FUNCTIONALITY TO NUMPY DATETIME64 ARRAY
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

    def __init__(self,none=None):

        if none is None:
            self._none = numpy.datetime64('NaT')
        elif isinstance(none,datetime.datetime):
            self._none = numpy.datetime64(none).astype('datetime64[s]')
        elif isinstance(none,datetime.date):
            self._none = numpy.datetime64(none).astype('datetime64[D]')
        else:
            raise TypeError("none must be datetime type!")

        self._none = numpy.datetime64('NaT') if none is None else none

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

    def add(self,delta,unit='month'):

        pass

    def shift(self):

        pass

    def toeom(self):

        pass

    def tobom(self):

        pass

    def _arange(*args,start=None,stop="today",step=1,size=None,dtype=None,step_unit='M'):

        kwargs = setargs(*args,**kwargs)

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

    def _build_datetime64_from_list(*args,year=2000,month=1,day=-1,hour=0,minute=0,second=0,size=None,dtype=None):

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

            _array = array1d(args[0],size)

            if dtype is None:
                return _array
            
            try:
                return _array.astype(dtype)
            except ValueError:
                array_date = [parser.parse(dt) for dt in _array]
                return numpy.array(array_date,dtype=dtype)

    @property
    def year(self):
        
        return

    @property
    def month(self):

        return

    @property
    def monthrange(self):

        return

    @property
    def nextmonthrange(self):
        
        return
    
    @property
    def prevmonthrange(self):
        
        return

    @property
    def day(self):
        
        return

if __name__ == "__main__":

    import unittest

    # from test import test_array_flatten as test
    # from test import test_array_array as test
    # from test import test_array_arange as test
    # from test import test_array_repeat as test
    # from test import test_array_iterator as test
    from test import test_array_integers as test
    # from test import test_array_floats as test
    # from test import test_array_strings as test
    # from test import test_array_datetimes as test

    unittest.main(test)