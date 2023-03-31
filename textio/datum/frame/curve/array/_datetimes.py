import datetime

import numpy

"""
For numpy.datetime64, the issue with following deltatime units
has been solved:

Y: year,
M: month,

For numpy.datetime64, following deltatime units
have no inherent issue:

W: week,
D: day,
h: hour,
m: minute,
s: second,
"""

class datetimes(numpy.ndarray): # HOW TO ADD SOME FUNCTIONALITY TO NUMPY DATETIME64 ARRAY

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

        datetime_adddelta = numpy.vectorize(_datetime_adddelta,otypes=['datetime64[s]'])

        datetime_addmonths = numpy.vectorize(_datetime_addmonths,otypes=['datetime64[s]'])

        datetime_addyears = numpy.vectorize(_datetime_addyears,otypes=['datetime64[s]'])

    def min(self):

        return numpy.nanmin(self.vals)

    def max(self):

        return numpy.nanmax(self.vals)

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
            
            if fstring is None:
                text = val.strftime("%Y-%m-%d || %H:%M:%S")
            else:
                text = val.strftime(fstring_inner[1:-1])

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

def _adddelta(dtcurr:datetime.datetime,days:float=0.,hours:float=0.,minutes:float=0.,seconds:float=0.) -> datetime.datetime:

    if dtcurr is None:
        return
        
    dtcurr += relativedelta.relativedelta(days=days,hours=hours,minutes=minutes,seconds=seconds)

    return dtcurr

def _addmonths(dtcurr:datetime.datetime,delta:float) -> datetime.datetime:

    if dtcurr is None:
        return

    delta_month = int(delta//1)

    delta_month_fraction = delta%1

    dtcurr += relativedelta.relativedelta(months=delta_month)

    if delta_month_fraction==0:
        return dtcurr

    mrange = calendar.monthrange(dtcurr.year,dtcurr.month)[1]

    delta_day = delta_month_fraction*mrange

    dttemp = dtcurr+relativedelta.relativedelta(days=delta_day)

    month_diff = (dttemp.year-dtcurr.year)*12+dttemp.month-dtcurr.month

    if month_diff<2:
        return dttemp

    dtcurr += relativedelta.relativedelta(months=1)
    
    return datetime.datetime(dtcurr.year,dtcurr.month,dtcurr.day,23,59,59) #,999999

def _addyears(dtcurr:datetime.datetime,delta:float) -> datetime.datetime:

    if dtcurr is None:
        return

    delta_year = int(delta//1)

    delta_year_fraction = delta%1

    dtcurr += relativedelta.relativedelta(years=delta_year)

    if delta_year_fraction==0:
        return dtcurr
    else:
        return _datetime_addmonths(dtcurr,delta_year_fraction*12)