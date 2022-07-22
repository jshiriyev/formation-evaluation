import datetime

from dateutil import parser

import re

import numpy as np

def str2int(
    string: str,
    strnone: str = "",
    intnone: int = -99_999,
    regex: str = None) -> int:
    """It returns integer converted from string."""

    # common expression for int type is r"[-+]?\d+\b"

    if regex is None:
        if string==strnone:
            return intnone
        else:
            return int(string)

    else:
        match = re.search(regex,string)

        if match is None:
            return intnone
        else:
            return int(match.group())
        
str2int = np.vectorize(str2int,otypes=[int],excluded=["strnone","intnone","regex"])

# print(str2int(np.array(["john 1","sabrina 2","tarum 5 nohan","conor"]),intnone=0,regexFlag=True))

def str2float(
    string: str,
    strnone: str = "",
    floatnone: float = np.nan,
    sep_decimal: str = ".",
    sep_thousand: str = ",",
    regex: str = None) -> float:
    """It returns float after removing thousand separator and setting decimal separator as full stop."""

    # common regular expression for float type is f"[-+]?(?:\\d*\\{sep_thousand}*\\d*\\{sep_decimal}\\d+|\\d+)"

    if regex is None:
        if string==strnone:
            return floatnone
        elif string.count(sep_decimal)>1:
            raise ValueError(f"String contains more than one {sep_decimal=}, {string}")
        else:
            if string.count(sep_thousand)>0:
                string = string.replace(sep_thousand,"")
            if sep_decimal!=".":
                string = string.replace(sep_decimal,".")
            return float(string)

    else:
        match = re.search(regex,string)

        if match is None:
            return floatnone
        else:
            return float(match.group())

str2float = np.vectorize(str2float,otypes=[float],excluded=["strnone","floatnone","sep_decimal","sep_thousand","regex"])

def str2datetime(
    string: str,
    strnone: str = "",
    datetimenone: np.datetime64 = np.datetime64('NaT'),
    regex: str = None) -> np.datetime64:

    if regex is None:
        if string==strnone:
            return datetimenone
        else:
            return np.datetime64(parser.parse(string))
    else:
        match = re.search(regex,string)

        if match is None:
            return datetimenone
        else:
            return np.datetime64(match.group())

str2datetime = np.vectorize(str2datetime,otypes=[np.datetime64],excluded=["strnone","datetimenone","regex"])

def int2str(
    number: int,
    intnone: int = -99_999,
    strnone: str = "",
    fstring: str = None) -> str:

    if number==intnone:
        return strnone
    else:
        fstring = "{:,d}" if fstring is None else fstring
        return fstring.format(number)

int2str = np.vectorize(int2str,otypes=[str],excluded=["intnone","strnone","fstring"])

def float2str(
    number: float,
    floatnone: float = np.nan,
    strnone: str = "",
    fstring: str = None) -> str:

    if number==floatnone:
        number = strnone
    else:
        fstring = "{:f}" if fstring is None else fstring
        return fstring.format(number)

float2str = np.vectorize(float2str,otypes=[str],excluded=["floatnone","strnone","fstring"])

def str2str(
    string: str,
    strnone: str = "",
    regex: str = None,
    fstring: str = None) -> str:

    fstring = "{:s}" if fstring is None else fstring

    if regex is None:
        if string==strnone:
            return fstring.format(strnone)
        else:
            return fstring.format(string)

    else:
        match = re.search(regex,string)

        if match is None:
            return fstring.format(strnone)
        else:
            return fstring.format(match.group())

str2str = np.vectorize(str2str,otypes=[str],excluded=["strnone","regex","fstring"])

def datetime2str(
    datetime_: datetime.date,
    datetimenone: datetime.date = None,
    strnone: str = "",
    fstring: str = None) -> str:

    if isinstance(datetimenone,np.datetime64):
        datetimenone = datetimenone.tolist()

    if datetime_ == datetimenone:
        return strnone
    else:
        fstring = "%d-%b-%Y" if fstring is None else fstring
        return datetime_.strftime(fstring)

datetime2str = np.vectorize(datetime2str,otypes=[str],excluded=["datetimenone","strnone","fstring"])

# dtl = [datetime.datetime.today(),datetime.datetime.today()]
# dtn = np.array(dtl,dtype=np.datetime64)

# print(datetime2str(dtl))
# print(datetime2str(dtn))

def starsplit(text,default=1.0):
    """It returns star splitted list repeating post-star pre-star times."""

    string_list - text.split(" ")

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

def starsplit_numpy(array):
    """It returns star splitted array repeating post-star pre-star times."""

    ints = np.ones(array.shape,dtype=int)

    flts = np.empty(array.shape,dtype=float)

    # array = np.char.split(array,sep="*",maxsplit=1)

    # for i,pylist in enumerate(array):

    #     if len(pylist)==1:
    #         flts[i] = float(pylist[0])
    #     else:
    #         ints[i],flts[i] = int(pylist[0]),float(pylist[1])
    for i,string in enumerate(array):

        row = string.split("*",maxsplit=1)

        if len(row)==1:
            flts[i] = float(row[0])
        else:
            ints[i],flts[i] = int(row[0]),float(row[1])

    return np.repeat(flts,ints)

def starsplit_npvect_(string):
    """It returns integer and floating number in star multiplied string."""
    
    row = string.split("*",maxsplit=1)

    if len(row)==1:
        return 1,float(row[0])
    else:
        return int(row[0]),float(row[1])

starsplit_npvect = np.vectorize(starsplit_npvect_,signature='()->(),()')