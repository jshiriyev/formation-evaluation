import datetime

from dateutil import parser

import re

import numpy

class dates(numpy.ndarray):

    def __new__(cls,values,null=None):

        null = numpy.datetime64('NaT') if null is None else numpy.datetime64(null)

        values = iterable(values)

        obj = numpy.asarray(values,dtype='datetime64[D]').view(cls)

        obj._null = null

        return obj

    def __array_finalize__(self,obj):

        if obj is None: return

        self._null = getattr(obj,'_null',numpy.datetime64('NaT'))

    def __repr__(self):

        parent = super().__repr__()

        child = parent.replace('NaT',str(self.null))

        return re.sub(r"\s+"," ",child)

    def __str__(self):

        parent = super().__str__()

        child = parent.replace('NaT',str(self.null))

        return re.sub(r"\s+"," ",child)

    def tolist(self):

        return

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
                text = val.strftime("%Y-%m-%d")
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

    @property
    def null(self):

        return self._null

    @property
    def isvalid(self):
        """It return boolean array True for float and False for null."""
        return ~numpy.isnan(self.view(numpy.ndarray))

    @property
    def isnull(self):
        """It return numpy bool array, True for null and False for float."""
        return numpy.isnan(self.view(numpy.ndarray))

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

def iterable(values):

    vals = []

    for value in values:

        if isinstance(value,int):
            value = datetime.date.fromtimestamp(value)
        elif isinstance(value,float):
            value = datetime.date.fromtimestamp(value)
        elif isinstance(value,str):
            value = strtodate(value)
        elif isinstance(value,datetime.datetime):
            value = value.date()
        elif isinstance(value,datetime.date):
            value = value
        else:
            value = None

        vals.append(value)

    return vals

def strtodate(value):

    if value.lower() == "now" or value.lower() == "today":
        value = datetime.date.today()

    elif value.lower() == "yesterday":
        value = numpy.datetime64(datetime.date.today())
        value -= numpy.timedelta64(1,'D')
        value = value.tolist()

    elif value.lower() == "tomorrow":
        value = numpy.datetime64(datetime.date.today())
        value += numpy.timedelta64(1,'D')
        value = value.tolist()

    else:

        try:
            value = parser.parse(string)
        except parser.ParserError:
            value = None
        else:
            value = value.date()

    return value
