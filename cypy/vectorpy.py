import re

import numpy as np

"""
 1. String to Integer
 2. String to Float
 3. String to Datetime
 4. Integer to String
 5. Float to String
 6. Datetime to String

13. Edit strings
14. Edit datetime (shifting)
"""

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
            raise ValueError(f"String contains more than one comma and dot, {string}")
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

def str2int(
    string: str,
    strnone: str = "",
    intnone: int = -99_999,
    regex: str = None) -> int:

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

def str2date(string:str):

    pass

def float2str(number,floatnone:float=np.nan,strnone:str="",fstring=None) -> str:

    if fstring is None:
        fstring = "{:f}"

    if number==floatnone:
        number = strnone

    return fstring.format(number)

def int2str(number,intnone=-9999,strnone="",fstring=None,roundflag=False):

    if fstring is None:
        fstring = "{:d}"

    pystring = []

    for number in pyfloat:

        if roundflag:
            number = round(number)

        pystring.append(fstring.format(number))

    return pystring

def date2str(pydatetime):

    pass

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