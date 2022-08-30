import calendar
import datetime

from dateutil import parser
from dateutil import relativedelta

import re

import numpy as np

def pytype(string):

    for attempt in (float,dateutil.parser.parse):

        try:
            attempt(string)
        except ValueError:
            continue

        return attempt

    return str

def str2int_(string:str,none_str:str="",none_int:int=-99_999,regex:str=None) -> int:
    """It returns integer converted from string."""

    # common expression for int type is r"[-+]?\d+\b"

    if string==none_str:
        return none_int

    if regex is None:
        return int(string)

    match = re.search(regex,string)

    if match is None:
        return none_int

    string = match.group()
            
    return int(string)
        
str2int = np.vectorize(str2int_,otypes=[int],excluded=["none_str","none_int","regex"])

def str2float_(string:str,none_str:str="",none_float:float=np.nan,sep_decimal:str=".",sep_thousand:str=",",regex:str=None) -> float:
    """It returns float after removing thousand separator and setting decimal separator as full stop."""

    # common regular expression for float type is f"[-+]?(?:\\d*\\{sep_thousand}*\\d*\\{sep_decimal}\\d+|\\d+)"

    if string.count(sep_decimal)>1:
        raise ValueError(f"String contains more than one {sep_decimal=}, {string}")

    if string.count(sep_thousand)>0:
        string = string.replace(sep_thousand,"")

    if sep_decimal!=".":
        string = string.replace(sep_decimal,".")

    if string==none_str:
        return none_float

    if regex is None:
        return float(string)

    match = re.search(regex,string)

    if match is None:
        return none_float

    string = match.group()
    
    return float(string)

str2float = np.vectorize(str2float_,otypes=[float],excluded=["none_str","none_float","sep_decimal","sep_thousand","regex"])

def starsplit(string_list,default=1.0):
    """It returns star splitted list repeating post-star pre-star times."""

    float_list = []

    for string_value in string_list:

        if "*" in string_value:

            if string_value.endswith("*"):
                mult = string_value.rstrip("*")
                mult,val = int(mult),default
            else:
                mult,val = string_value.split("*",maxsplit=1)
                mult,val = int(mult),float(val)

            for i in range(mult):
                float_list.append(val)

        else:
            float_list.append(float(string_value))

    return float_list

def isnumber(string_):
    try:
        float(string_)
    except ValueError:
        return False
    else:
        return True

def str2str_(string:str,none_str:str="",regex:str=None,fstring:str=None) -> str:

    fstring = "{:s}" if fstring is None else fstring

    if regex is None:
        if string==none_str:
            return fstring.format(none_str)
        else:
            return fstring.format(string)

    else:
        match = re.search(regex,string)

        if match is None:
            return fstring.format(none_str)
        else:
            return fstring.format(match.group())

str2str = np.vectorize(str2str_,otypes=[str],excluded=["none_str","regex","fstring"])

def str2datetime64_(string:str,none_str:str="",none_datetime64:np.datetime64=np.datetime64('NaT'),regex:str=None) -> np.datetime64:

    if regex is None:
        if string==none_str:
            return none_datetime64
        else:
            return np.datetime64(parser.parse(string))
    else:
        match = re.search(regex,string)

        if match is None:
            return none_datetime64
        else:
            return np.datetime64(match.group())

str2datetime64 = np.vectorize(str2datetime64_,otypes=[np.datetime64],excluded=["none_str","none_datetime64","regex"])

def datetime_adddelta_(dtcurr:datetime.datetime,days:float=0.,hours:float=0.,minutes:float=0.,seconds:float=0.) -> datetime.datetime:

    if dtcurr is None:
        return
        
    dtcurr += relativedelta.relativedelta(days=days,hours=hours,minutes=minutes,seconds=seconds)

    return dtcurr

datetime_adddelta = np.vectorize(datetime_adddelta_,otypes=['datetime64[s]'])

def datetime_addmonths_(dtcurr:datetime.datetime,delta:float) -> datetime.datetime:

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

datetime_addmonths = np.vectorize(datetime_addmonths_,otypes=['datetime64[s]'])

def datetime_addyears_(dtcurr:datetime.datetime,delta:float) -> datetime.datetime:

    if dtcurr is None:
        return

    delta_year = int(delta//1)

    delta_year_fraction = delta%1

    dtcurr += relativedelta.relativedelta(years=delta_year)

    if delta_year_fraction==0:
        return dtcurr
    else:
        return datetime_addmonths_(dtcurr,delta_year_fraction*12)

datetime_addyears = np.vectorize(datetime_addyears_,otypes=['datetime64[s]'])