class Curve():# INITIALIZATION MUST BE SIMPLIFIED TO: head=vals
    """It is a numpy array of shape (N,) with additional attributes of head, unit and info."""

    """INITIALIZATION"""

    def __init__(self,vals,head=None,unit=None,info=None,size=None,dtype=None):
        """Initializes a column with vals of numpy array (N,) and additional attributes."""

        """
        Initialization can be done by sending int, float, str, datetime, numpy as standalone or
        in a list, tuple or numpy.ndarray
        
        The argument "size" is optional and dicates the size of 1 dimensional numpy array.
        The argument "dtype" is optional and can be any type in {int, float, str, datetime64}

        """

        self.nones = nones()

        super().__setattr__("vals",array1d(vals,size))

        self._astype(dtype)

        self._valshead(head)
        self._valsunit(unit)
        self._valsinfo(info)

    def _valsarr(self,vals):
        """Sets the vals of column."""

        super().__setattr__("vals",array1d(vals))

        self._astype()

        self._valsunit()

    def _astype(self,dtype=None):
        """It changes the dtype of the column and alters the None values accordingly."""

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if dtype is None:
            pass
        elif not isinstance(dtype,numpy.dtype):
            raise TypeError(f"dtype must be numpy.dtype, not type={type(dtype)}")
        elif dtype.type is numpy.object_:
            raise TypeError(f"Unsupported numpy.dtype, {dtype=}")
        elif self.dtype==dtype:
            return self

        if dtype is None:
            dtype = self.dtype

        if dtype.type is numpy.dtype('int').type:
            none = self.nones.int
        elif dtype.type is numpy.dtype('float').type:
            none = self.nones.float
        elif dtype.type is numpy.dtype('str').type:
            none = self.nones.str
        elif dtype.type is numpy.dtype('datetime64').type:
            none = self.nones.datetime64
        else:
            raise TypeError(f"Unexpected numpy.dtype, {dtype=}")

        vals_arr = self.vals.astype(numpy.object_)

        try:
            vals_arr[self.isnone] = none
            vals_arr = vals_arr.astype(dtype=dtype)
        except ValueError:
            vals_arr[self.isnone] = self.nones.str
            vals_arr = vals_arr.astype(dtype='str')

        object.__setattr__(self,"vals",vals_arr)

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

        if self.dtype.type is numpy.dtype('float').type:
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

    """REPRESENTATION"""

    def _valstr(self,num=None):
        """It outputs column.vals. If num is not defined it edites numpy.ndarray.__str__()."""

        if num is None:

            vals_str = self.vals.__str__()

            if self.vals.dtype.type is numpy.int32:
                vals_lst = re.findall(r"[-+]?[0-9]+",vals_str)
                vals_str = re.sub(r"[-+]?[0-9]+","{}",vals_str)
            elif self.vals.dtype.type is numpy.float64:
                vals_lst = re.findall(r"[-+]?(?:\d*\.\d+|\d+)",vals_str)
                vals_str = re.sub(r"[-+]?(?:\d*\.\d+|\d+)","{}",vals_str)
            elif self.vals.dtype.type is numpy.str_:
                vals_lst = re.findall(r"\'(.*?)\'",vals_str)
                vals_str = re.sub(r"\'(.*?)\'","\'{}\'",vals_str)
            elif self.vals.dtype.type is numpy.datetime64:
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
                part1,part2 = int(numpy.ceil(num/2)),int(numpy.floor(num/2))
                fstring = "[{}...{}]".format("{},"*part1,",{}"*part2)

            if self.vals.dtype.type is numpy.int32:
                vals_str = fstring.format(*["{:d}"]*part1,*["{:d}"]*part2)
            elif self.vals.dtype.type is numpy.float64:
                vals_str = fstring.format(*["{:g}"]*part1,*["{:g}"]*part2)
            elif self.vals.dtype.type is numpy.str_:
                vals_str = fstring.format(*["'{:s}'"]*part1,*["'{:s}'"]*part2)
            elif self.vals.dtype.type is numpy.datetime64:
                vals_str = fstring.format(*["'{}'"]*part1,*["'{}'"]*part2)

            return vals_str.format(*self.vals[:part1],*self.vals[-part2:])

    def __repr__(self):
        """Console representation of column."""

        return f'column(head="{self.head}", unit="{self.unit}", info="{self.info}", vals={self._valstr(2)})'

    def __str__(self):
        """Print representation of column."""

        text = "{}\n"*4

        head = f"head\t: {self.head}"
        unit = f"unit\t: {self.unit}"
        info = f"info\t: {self.info}"
        vals = f"vals\t: {self._valstr(2)}"

        return text.format(head,unit,info,vals)

    """COMPARISON"""

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
                return numpy.abs(self.vals-other.vals)<tol*numpy.maximum(numpy.abs(self.vals),numpy.abs(other.vals))
                #numpy.allclose(self.vals,other.vals,rtol=1e-10,atol=1e-10)
            else:
                return self.vals==other.vals
        else:
            return self.vals==other

    def __ne__(self,other,tol=1e-12):
        """Implementing '!=' operator."""
        
        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
                return numpy.abs(self.vals-other.vals)>tol*numpy.maximum(numpy.abs(self.vals),numpy.abs(other.vals))
            else:
                return self.vals!=other.vals
        else:
            return self.vals!=other

    def __bool__(self):

        if self.vals.dtype.type is numpy.object_:
            return self.vals.any()
        elif self.vals.dtype.type is numpy.int32:
            return self.vals.any()
        elif self.vals.dtype.type is numpy.float64:
            return not numpy.all(numpy.isnan(self.vals))
        elif self.vals.dtype.type is numpy.str_:
            return self.vals.any()
        elif self.vals.dtype.type is numpy.datetime64:
            return not numpy.all(numpy.isnat(self.vals))

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

    """SEARCH METHODS"""

    def min(self):
        """It returns none-minimum value of column."""

        if self.vals.dtype.type is numpy.int32:
            return self.vals[~self.isnone].min()
        elif self.vals.dtype.type is numpy.float64:
            return numpy.nanmin(self.vals)
        elif self.vals.dtype.type is numpy.str_:
            return min(self.vals[~self.isnone],key=len)
        elif self.vals.dtype.type is numpy.datetime64:
            return numpy.nanmin(self.vals)

    def max(self):
        """It returns none-maximum value of column."""

        if self.vals.dtype.type is numpy.int32:
            return self.vals[~self.isnone].max()
        elif self.vals.dtype.type is numpy.float64:
            return numpy.nanmax(self.vals)
        elif self.vals.dtype.type is numpy.str_:
            return max(self.vals[~self.isnone],key=len)
        elif self.vals.dtype.type is numpy.datetime64:
            return numpy.nanmax(self.vals)

    """CONTAINER METHODS"""

    def __setitem__(self,key,vals):

        self.vals[key] = vals

    def __delitem__(self,key):

        return numpy.delete(self.vals,key)

    def __iter__(self):

        return iter(self.vals)

    def __len__(self):

        return len(self.vals)

    def __getitem__(self,key):

        datacolumn = copy.deepcopy(self)

        datacolumn.vals = self.vals[key]

        return datacolumn

    """CONVERSION METHODS"""

    def astype(self,dtype=None):

        datacolumn = copy.deepcopy(self)

        datacolumn._astype(dtype)

        return datacolumn

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

    def convert(self,unit):
        """It converts the vals to the new unit."""

        if self.unit==unit:
            return self

        datacolumn = copy.deepcopy(self)

        if self.dtype.type is not numpy.dtype('float').type:
            datacolumn = datacolumn.astype('float')
        else:
            ureg = pint.UnitRegistry()
            ureg.Quantity(datacolumn.vals,datacolumn.unit).ito(unit)

        datacolumn.unit = unit

        return datacolumn

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

    def fromstring(self,dtype,regex=None):

        datacolumn = copy.deepcopy(self)

        # line = re.sub(r"[^\w]","",line) # cleans non-alphanumerics, keeps 0-9, A-Z, a-z, or underscore.

        if isinstance(dtype,str):
            dtype = numpy.dtype(dtype)

        if dtype.type is numpy.dtype('int').type:
            dnone = self.nones.todict("str","int")
            regex = r"[-+]?\d+\b" if regex is None else regex
            datacolumn.vals = str2int(datacolumn.vals,regex=regex,**dnone)
        elif dtype.type is numpy.dtype('float').type:
            dnone = self.nones.todict("str","float")
            regex = r"[-+]?[0-9]*\.?[0-9]+" if regex is None else regex
            datacolumn.vals = str2float(datacolumn.vals,regex=regex,**dnone)
            datacolumn._valsunit()
        elif dtype.type is numpy.dtype('str').type:
            dnone = self.nones.todict("str")
            datacolumn.vals = str2str(datacolumn.vals,regex=regex,**dnone)
        elif dtype.type is numpy.dtype('datetime64').type:
            dnone = self.nones.todict("str","datetime64")
            datacolumn.vals = str2datetime64(datacolumn.vals,regex=regex,**dnone)
        else:
            raise TypeError("dtype can be either int, float, str or datetime64")

        return datacolumn

    def tostring(self,fstring=None,upper=False,lower=False,zfill=None):
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
            
            if isinstance(val,float):
                if fstring is None:
                    text = '{:g}'.format(val)
                else:
                    text = fstring_inner.format(val)
            elif isinstance(val,datetime.datetime):
                if fstring is None:
                    text = val.strftime("%Y-%m-%d || %H:%M:%S")
                else:
                    text = val.strftime(fstring_inner[1:-1])
            elif isinstance(val,datetime.date):
                if fstring is None:
                    text = val.strftime("%Y-%m-%d")
                else:
                    text = val.strftime(fstring_inner[1:-1])
            else:
                text = fstring_inner.format(val)

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

    """SHIFTING"""
    
    def shift(self,delta,deltaunit=None):
        """Shifting the entries depending on its dtype."""

        datacolumn = copy.deepcopy(self)

        if datacolumn.dtype.type is numpy.dtype('int').type:
            delta_column = column(delta,dtype='int')
            vals_shifted = datacolumn.vals+delta_column.vals
        elif datacolumn.dtype.type is numpy.dtype('float').type:
            delta_column = column(delta,dtype='float',unit=deltaunit)
            delta_column = delta_column.convert(datacolumn.unit)
            vals_shifted = datacolumn.vals+delta_column.vals
        elif datacolumn.dtype.type is numpy.dtype('str').type:
            delta_column = any2column(phrases=' ',repeats=delta,dtype='str')
            vals_shifted = numpy.char.add(delta_column.vals,datacolumn)
        elif datacolumn.dtype.type is numpy.dtype('datetime64').type:
            vals_shifted = self._add_deltatime(delta,deltaunit)

        datacolumn.vals = vals_shifted

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

    """MATHEMATICAL OPERATIONS"""

    def __add__(self,other):
        """Implementing '+' operator."""

        curnt = copy.deepcopy(self)

        if not isinstance(other,column):
            other = column(other)

        if curnt.dtype.type is numpy.dtype('int').type:
            if not other.dtype.type is numpy.dtype('int').type:
                other = other.astype('int')
            curnt.vals += other.vals
        elif curnt.dtype.type is numpy.dtype('float').type:
            if not other.dtype.type is numpy.dtype('float').type:
                other = other.astype('float')
            other = other.convert(curnt.unit)
            curnt.vals += other.vals
        elif curnt.dtype.type is numpy.dtype('str').type:
            if not other.dtype.type is numpy.dtype('str').type:
                other = other.astype('str')
            curnt.vals = numpy.char.add(curnt.vals,other.vals)
        elif curnt.dtype.type is numpy.dtype('datetime64').type:
            if not other.dtype.type is numpy.dtype('float').type:
                raise TypeError(f"Only floats with delta time unit is supported.")
            elif other.unit=="dimensionless":
                raise TypeError(f"Only floats with delta time unit is supported.")
            else:
                unrg = pint.UnitRegistry()
                unit = unrg.Unit(other.unit).__str__()
                curnt = curnt.shift(other.vals,deltaunit=unit)

        return curnt

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

    def __floordiv__(self,other):
        """Implementing '//' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
            # ureg = pint.UnitRegistry()
            # unit = ureg.Unit(f"{self.unit}/({other.unit})").__str__()

            if other.nondim and self.nondim:
                unit = "dimensionless"
            elif not other.nondim and self.nondim:
                unit = f"1/{other.unit}"
            elif other.nondim and not self.nondim:
                unit = self.unit
            else:
                unit = f"{self.unit}/({other.unit})"

            datacolumn.vals = self.vals//other.vals
            datacolumn._valsunit(unit)

        else:
            datacolumn.vals = self.vals//other
            
        return datacolumn

    def __mod__(self,other):
        """Implementing '%' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
        #     ureg = pint.UnitRegistry()
        #     unit = ureg.Unit(f"{self.unit}/({other.unit})").__str__()
        #     return column(self.vals%other.vals,unit=unit)
            if other.nondim:
                datacolumn.vals = self.vals%other.vals
            else:
                raise TypeError(f"unsupported operand type for dimensional column arrays.")
        else:
            datacolumn.vals = self.vals%other
            
        return datacolumn

    def __mul__(self,other):
        """Implementing '*' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
            # ur = pint.UnitRegistry()
            # unit = ur.Unit(f"{self.unit}*{other.unit}").__str__()

            if other.nondim:
                unit = self.unit
            elif self.nondim:
                unit = other.unit
            else:
                unit = f"{self.unit}*{other.unit}"

            datacolumn.vals = self.vals*other.vals
            datacolumn._valsunit(unit)
        else:
            datacolumn.vals = self.vals*other

        return datacolumn

    def __pow__(self,other):
        """Implementing '**' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,int) or isinstance(other,float):
            # ureg = pint.UnitRegistry()
            # unit = ureg.Unit(f"{self.unit}^{other}").__str__()
            datacolumn.vals = self.vals**other
            datacolumn._valsunit(f"({self.unit})**{other}")
        else:
            raise TypeError(f"unsupported operand type for non-int or non-float entries.")

        return datacolumn

    def __sub__(self,other):
        """Implementing '-' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
            if self.unit!=other.unit:
                other = other.convert(self.unit)
            datacolumn.vals = self.vals-other.vals
        else:
            datacolumn.vals = self.vals-other
        
        return datacolumn

    def __truediv__(self,other):
        """Implementing '/' operator."""

        datacolumn = copy.deepcopy(self)

        if isinstance(other,column):
            # ur = pint.UnitRegistry()
            # unit = ur.Unit(f"{self.unit}/({other.unit})").__str__()

            if other.nondim and self.nondim:
                unit = "dimensionless"
            elif not other.nondim and self.nondim:
                unit = f"1/{other.unit}"
            elif other.nondim and not self.nondim:
                unit = self.unit
            else:
                unit = f"{self.unit}/({other.unit})"

            datacolumn.vals = self.vals/other.vals
            datacolumn._valsunit(unit)
        else:
            datacolumn.vals = self.vals/other
        
        return datacolumn

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

    """APPENDING"""

    def append(self,other):

        if not isinstance(other,column):
            other = column(other)

        if self.dtype.type is numpy.dtype('int').type:
            if not other.dtype.type is numpy.dtype('int').type:
                other = other.astype('int')
        elif self.dtype.type is numpy.dtype('float').type:
            if not other.dtype.type is numpy.dtype('float').type:
                other = other.astype('float')
            other = other.convert(self.unit)
        elif self.dtype.type is numpy.dtype('str').type:
            if not other.dtype.type is numpy.dtype('str').type:
                other = other.astype('str')
        elif self.dtype.type is numpy.dtype('datetime64').type:
            if not other.dtype.type is numpy.dtype('datetime64').type:
                other = other.astype('datetime64')
                
        dataarray = numpy.append(self.vals,other.vals)
        
        super().__setattr__("vals",dataarray)

    """PLOTTING"""

    def histogram(self,axis,logscale=False):

        show = True if axis is None else False

        if axis is None:
            axis = pyplot.figure().add_subplot()

        yaxis = self.vals

        if logscale:
            yaxis = numpy.log10(yaxis[numpy.nonzero(yaxis)[0]])

        if logscale:
            xlabel = "log10(nonzero-{}) [{}]".format(self.info,self.unit)
        else:
            xlabel = "{} [{}]".format(self.info,self.unit)

        axis.hist(yaxis,density=True,bins=30)  # density=False would make counts
        axis.set_ylabel("Probability")
        axis.set_xlabel(xlabel)

        if show:
            pyplot.show()

    """GENERAL PROPERTIES"""

    @property
    def dtype(self):
        """Return dtype of column.vals."""

        if self.vals.dtype.type is numpy.object_:
            dataarray = self.vals[~self.isnone]

            if dataarray.size==0:
                datatype = numpy.dtype('float64')
            elif isinstance(dataarray[0],int):
                datatype = numpy.dtype('float64')
            elif isinstance(dataarray[0],str):
                datatype = numpy.dtype('str_')
            elif isinstance(dataarray[0],datetime.datetime):
                datatype = numpy.dtype('datetime64[s]')
            elif isinstance(dataarray[0],datetime.date):
                datatype = numpy.dtype('datetime64[D]')
            else:
                datatype = numpy.array([dataarray[0]]).dtype

        else:
            datatype = self.vals.dtype

        return datatype

    @property
    def size(self):
        """It returns the size of array in the column."""
        return len(self.vals)
    
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

        elif self.dtype.type is numpy.dtype("int").type:
            bool_arr = self.vals==self.nones.int

        elif self.dtype.type is numpy.dtype("float").type:
            bool_arr = numpy.isnan(self.vals)
            if not numpy.isnan(self.nones.float):
                bool_arr = numpy.logical_or(bool_arr,self.vals==self.nones.float)

        elif self.dtype.type is numpy.dtype("str").type:
            bool_arr = self.vals == self.nones.str

        elif self.dtype.type is numpy.dtype("datetime64").type:
            bool_arr = numpy.isnat(self.vals)
            if not numpy.isnat(self.nones.datetime64):
                bool_arr = numpy.logical_or(bool_arr,self.vals==self.nones.datetime64)

        else:
            raise TypeError(f"Unidentified problem with column dtype={self.vals.dtype.type}")

        return bool_arr

    @property
    def issorted(self):

        return numpy.all(self.vals[:-1]<self.vals[1:])
    
    @property
    def nondim(self):
        """It checks whether column has unit or not."""

        if self.vals.dtype.type is numpy.float64:
            return self.unit=="dimensionless"
        else:
            return True
    
    """DATE-TIME PROPERTIES"""

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