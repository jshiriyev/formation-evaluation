import datetime

import numpy

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

        datetime_adddelta = numpy.vectorize(_datetime_adddelta,otypes=['datetime64[s]'])

        datetime_addmonths = numpy.vectorize(_datetime_addmonths,otypes=['datetime64[s]'])

        datetime_addyears = numpy.vectorize(_datetime_addyears,otypes=['datetime64[s]'])

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