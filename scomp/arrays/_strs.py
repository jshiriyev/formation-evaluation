import numpy

def _strtype(string:str):

    for attempt in (float,parser.parse):

        try:
            typedstring = attempt(string)
        except:
            continue

        return type(typedstring)

    return str

strtype = lambda array: [_strtype(value) for value in array]

def _str2int(string:str,none_str:str="",none_int:int=-99_999,regex:str=None) -> int:
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
        
str2int = numpy.vectorize(_str2int,otypes=[int],excluded=["none_str","none_int","regex"])

def _str2float(string:str,none_str:str="",none_float:float=numpy.nan,sep_decimal:str=".",sep_thousand:str=",",regex:str=None) -> float:
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

str2float = numpy.vectorize(_str2float,otypes=[float],excluded=["none_str","none_float","sep_decimal","sep_thousand","regex"])

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

def _str2str(string:str,none_str:str="",regex:str=None,fstring:str=None) -> str:

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

str2str = numpy.vectorize(_str2str,otypes=[str],excluded=["none_str","regex","fstring"])

def _str2datetime64(string:str,none_str:str="",none_datetime64:numpy.datetime64=numpy.datetime64('NaT'),unit_code:str="D",regex:str=None) -> numpy.datetime64:

    if regex is not None:
        match = re.search(regex,string)

        if match is None:
            return none_datetime64

        string = match.group()

    if string==none_str:
        return none_datetime64

    elif string=="now":
        now = numpy.datetime64(datetime.datetime.now(),unit_code)
        return now

    elif string=="today":
        today = numpy.datetime64(datetime.datetime.today(),unit_code)
        return today

    elif string=="yesterday":
        today = numpy.datetime64(datetime.datetime.today(),unit_code)
        return today-numpy.timedelta64(1,'D')

    elif string=="tomorrow":
        today = numpy.datetime64(datetime.datetime.today(),unit_code)
        return today+numpy.timedelta64(1,'D')

    try:
        return numpy.datetime64(parser.parse(string),unit_code)

    except parser.ParserError:
        return none_datetime64

str2datetime64 = numpy.vectorize(_str2datetime64,otypes=[numpy.datetime64],excluded=["none_str","none_datetime64","unit_code","regex"])

class strs(numpy.ndarray): # HOW TO ADD SOME FUNCTIONALITY TO STRING ARRAY

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