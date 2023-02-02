

def pop(kwargs,key,default=None):

    try:
        return kwargs.pop(key)
    except KeyError:
        return default

class Bundle():
    """It stores equal-size one-dimensional numpy arrays in a list."""

    """INITIALIZATION"""
    def __init__(self,*args,**kwargs):
        """Initializes frame with headers & running and parent class DirBase."""

        super().__setattr__("running",[])

        self._setup(*args)

        for key,vals in kwargs.items():
            self.__setitem__(key,vals)

    def _setup(self,*args):

        for arg in args:

            if not isinstance(arg,column):
                raise TypeError(f"Argument/s need/s to be column type only!")

            if self.shape[1]!=0 and self.shape[0]!=arg.size:
                raise ValueError(f"Attached column size is not the same as of dataframe.")

            if arg.head in self.heads:
                self.running[self._index(arg.head)[0]] = arg
            else:
                self.running.append(arg)

    def _append(self,*args):

        if len(args)==0:
            return
        elif len(set([len(arg) for arg in args]))!=1:
            raise ValueError("columns have variable lenghts.")

        if self.shape[1]==0:
            self._setup(*args)
        elif self.shape[1]!=len(args):
            raise ValueError("Number of columns does not match columns in dataframe.")
        else:
            [datacolumn.append(arg) for datacolumn,arg in zip(self.running,args)]

    """REPRESENTATION"""

    def __repr__(self):

        return self.__str__(limit=10,comment="")

    def __str__(self,limit:int=20,comment=None,**kwargs):
        """It prints to the console limited number of rows with headers."""

        upper = int(numpy.ceil(limit/2))
        lower = int(numpy.floor(limit/2))

        if self.shape[0]>limit:
            rows = list(range(upper))
            rows.extend(list(range(-lower,0,1)))
        else:
            rows = list(range(self.shape[0]))

        if comment is None:
            comment = ""

        dataframe = copy.deepcopy(self)

        running = [datacolumn.tostring(**kwargs) for datacolumn in dataframe.running]

        object.__setattr__(dataframe,'running',running)

        dataframe = dataframe[rows]

        headcount = [len(head) for head in dataframe.heads]
        bodycount = [datacolumn.maxchar() for datacolumn in dataframe.running]
        charcount = [max(hc,bc) for (hc,bc) in zip(headcount,bodycount)]

        # print(headcount,bodycount,charcount)

        bspaces = " "*len(comment)

        fstring = " ".join(["{{:>{}s}}".format(cc) for cc in charcount])

        fstringH = "{}{}\n".format(comment,fstring)
        fstringB = "{}{}\n".format(bspaces,fstring)

        heads_str = fstringH.format(*dataframe.heads)
        lines_str = fstringH.format(*["-"*count for count in charcount])
        large_str = fstringH.format(*[".." for _ in charcount])

        vprint = numpy.vectorize(lambda *args: fstringB.format(*args))

        bodycols = vprint(*dataframe.running).tolist()

        if self.shape[0]>limit:
            [bodycols.insert(upper,large_str) for _ in range(3)]

        string = ""
        string += heads_str
        string += lines_str
        string += "".join(bodycols)

        return string

    """ATTRIBUTE ACCESS"""

    def __setattr__(self,key,vals):

        raise AttributeError(f"'frame' object has no attribute '{key}'.")

    """CONTAINER METHODS"""

    def pop(self,key):

        return self.running.pop(self._index(key)[0])

    def _index(self,*args):

        if len(args)==0:
            raise TypeError(f"Index expected at least 1 argument, got 0")

        if any([type(key) is not str for key in args]):
            raise TypeError(f"argument/s must be string!")

        if any([key not in self.heads for key in args]):
            raise ValueError(f"The dataframe does not have key specified in {args}.")

        return tuple([self.heads.index(key) for key in args])

    def __setitem__(self,key,vals):

        if not isinstance(key,str):
            raise TypeError(f"The key can be str, not type={type(key)}.")

        datacolumn = column(vals,head=key)

        self._setup(datacolumn)

    def __delitem__(self,key):

        if isinstance(key,str):
            self.pop(key)
            return

        if isinstance(key,list) or isinstance(key,tuple):

            if all([type(_key) is str for _key in key]):
                [self.pop(_key) for _key in key]
                return
            elif any([type(_key) is str for _key in key]):
                raise ValueError("Arguments can not contain non-string and string entries together.")
        
        dataframe = copy.deepcopy(self)
        object.__setattr__(dataframe,'running',
            [numpy.delete(datacolumn,key) for datacolumn in self.running])

        return dataframe
        
    def __iter__(self):

        return iter([row for row in zip(*self.running)])

    def __len__(self):

        return self.shape[0]

    def __getitem__(self,key):

        if isinstance(key,str):
            return self.running[self._index(key)[0]]

        if isinstance(key,list) or isinstance(key,tuple):

            if all([type(_key) is str for _key in key]):

                running = [self.running[i] for i in self._index(*key)]

                dataframe = copy.deepcopy(self)

                object.__setattr__(dataframe,'running',running)

                return dataframe

            elif any([type(_key) is str for _key in key]):
                
                raise ValueError("Arguments can not contain non-string and string entries together.")
        
        running = [datacolumn[key] for datacolumn in self.running]

        dataframe = copy.deepcopy(self)

        object.__setattr__(dataframe,'running',running)

        return dataframe

    """CONVERSION METHODS"""

    def str2col(self,key=None,delimiter=None,maxsplit=None):
        """Breaks the column into new columns by splitting based on delimiter and maxsplit."""

        idcolumn = self._index(key)[0]

        datacolumn = self.pop(key)

        if maxsplit is None:
            maxsplit = numpy.char.count(datacolumn,delimiter).max()

        heads = ["{}_{}".format(datacolumn.head,index) for index in range(maxsplit+1)]

        running = []

        for index,string in enumerate(datacolumn.vals):

            row = string.split(delimiter,maxsplit=maxsplit)

            if maxsplit+1>len(row):
                [row.append(datacolumn.nones.str) for _ in range(maxsplit+1-len(row))]

            running.append(row)

        running = numpy.array(running,dtype=str).T

        for index,(vals,head) in enumerate(zip(running,heads),start=idcolumn):
            datacolumn_new = datacolumn[:]
            datacolumn_new.vals = vals
            datacolumn_new.head = head
            self.running.insert(index,datacolumn_new)

    def col2str(self,heads=None,headnew=None,fstring=None):

        if heads is None:
            heads = self.heads

        dataarray = [self[head].vals for head in heads]

        if fstring is None:
            fstring = ("{} "*len(dataarray))[:-1]

        vprint = numpy.vectorize(lambda *args: fstring.format(*args))

        arrnew = vprint(*dataarray)

        if headnew is None:
            fstring = ("{}_"*len(dataarray))[:-1]
            headnew = fstring.format(*heads)

        return column(arrnew,head=headnew)

    def tostruct(self):
        """Returns numpy structure of dataframe."""

        datatype_string = [datacolumn.vals.dtype.str for datacolumn in self.running]

        datatypes = [datatype for datatype in zip(self.heads,datatype_string)]

        return numpy.array([row for row in self],datatypes)

    """ADVANCED METHODS"""
            
    def sort(self,heads,reverse=False,return_indices=False):
        """Returns sorted dataframe."""

        if not (isinstance(heads,list) or isinstance(heads,tuple)):
            raise TypeError("heads must be list or tuple.")

        match = numpy.argsort(self[heads].tostruct(),axis=0,order=heads)

        if reverse:
            match = numpy.flip(match)

        if return_indices:
            return match

        dataframe = copy.deepcopy(self)

        running = [datacolumn[match] for datacolumn in self.running]

        object.__setattr__(dataframe,'running',running)

        return dataframe

    def flip(self):

        dataframe = copy.deepcopy(self)

        running = [datacolumn.flip() for datacolumn in self.running]

        object.__setattr__(dataframe,'running',running)

    def filter(self,key,keywords=None,regex=None,return_indices=False):
        """Returns filtered dataframe based on keywords or regex."""

        datacolumn = self[key]

        match = datacolumn.filter(keywords,regex,return_indices=True)

        if return_indices:
            return match
        else:
            dataframe = copy.deepcopy(self)
            object.__setattr__(dataframe,'running',
                [datacolumn[match] for datacolumn in self.running])
            return dataframe

    def unique(self,heads):
        """Returns dataframe with unique entries of column/s.
        The number of columns will be equal to the length of heads."""

        if not (isinstance(heads,list) or isinstance(heads,tuple)):
            raise TypeError("heads must be list or tuple.")

        df = self[heads]

        npstruct = df.tostruct()

        npstruct = numpy.unique(npstruct,axis=0)

        dataframe = copy.deepcopy(self)

        object.__setattr__(dataframe,'running',[])

        for head in heads:

            datacolumn = copy.deepcopy(self[head])

            datacolumn.vals = npstruct[head]

            dataframe.running.append(datacolumn)

        return dataframe

    """PROPERTY METHODS"""

    @property
    def shape(self):

        if len(self.running)>0:
            return (max([len(datacolumn) for datacolumn in self.running]),len(self.running))
        else:
            return (0,0)

    @property
    def dtypes(self):

        return [datacolumn.vals.dtype for datacolumn in self.running]

    @property
    def types(self):

        return [datacolumn.vals.dtype.type for datacolumn in self.running]

    @property
    def heads(self):

        return [datacolumn.head for datacolumn in self.running]

    @property
    def units(self):

        return [datacolumn.unit for datacolumn in self.running]

    @property
    def infos(self):

        return [datacolumn.info for datacolumn in self.running]