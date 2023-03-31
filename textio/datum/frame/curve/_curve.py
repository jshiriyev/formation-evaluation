import datetime

import re

from ._linear import linear

class curve():
    """It is a numpy array of shape (N,) stored in vals

    head: vals is linear array defined with vals, null, unit, ptype
    info: string statement

    """

    """INITIALIZATION"""

    def __init__(self,*args,**kwargs):
        """Initializes a column with vals of numpy array (N,) and additional attributes."""

        """
        Initialization can be done by sending int, float, str, datetime, numpy as standalone or
        in a list, tuple or numpy.ndarray
        
        The argument "ptype" is optional and can be any type in {int, float, str,
        datetime.time, datetime.date or datetime.datetime}

        """

        if len(args)>0:
            raise ValueError("No positional argument is accepted!")

        for head,vals in kwargs.items():
            break

        null = kwargs.get("null")
        unit = kwargs.get("unit")
        ptype = kwargs.get("ptype")

        if ptype is None:
            self.ptype = linear.ptype(vals)
        else:
            self.ptype = ptype

        self.array = linear.array(vals,null=null,unit=unit,ptype=self.ptype)

        self._valshead(head)

        info = kwargs.get("info")
        
        self._info = "" if info is None else info

    def _valshead(self,head=None):
        """Sets the head of column."""

        if head is None:
            if hasattr(self,"head"):
                return
            else:
                super().__setattr__("head","HEAD")
        else:
            super().__setattr__("head",re.sub(r"[^\w]","",str(head)))

    """REPRESENTATION"""

    def _valstr(self,num=None):
        """It outputs column.vals. If num is not defined it edites numpy.ndarray.__str__()."""

        if num is None:

            vals_str = self.array.__str__()

            if self.ptype is int:
                vals_lst = re.findall(r"[-+]?[0-9]+",vals_str)
                vals_str = re.sub(r"[-+]?[0-9]+","{}",vals_str)
            elif self.ptype is float:
                vals_lst = re.findall(r"[-+]?(?:\d*\.\d+|\d+)",vals_str)
                vals_str = re.sub(r"[-+]?(?:\d*\.\d+|\d+)","{}",vals_str)
            elif self.ptype is str:
                vals_lst = re.findall(r"\'(.*?)\'",vals_str)
                vals_str = re.sub(r"\'(.*?)\'","\'{}\'",vals_str)
            elif self.ptype is datetime.datetime:
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

            if self.array.size==0:
                part1,part2 = 0,0
                fstring = "[]"
            elif self.array.size==1:
                part1,part2 = 1,0
                fstring = "[{}]"
            elif self.array.size==2:
                part1,part2 = 1,1
                fstring = "[{},{}]"
            else:
                part1,part2 = int(num//2+1),int(num//2)
                fstring = "[{}...{}]".format("{},"*part1,",{}"*part2)

            if self.ptype is int:
                vals_str = fstring.format(*["{:d}"]*part1,*["{:d}"]*part2)
            elif self.ptype is float:
                vals_str = fstring.format(*["{:g}"]*part1,*["{:g}"]*part2)
            elif self.ptype is str:
                vals_str = fstring.format(*["'{:s}'"]*part1,*["'{:s}'"]*part2)
            elif self.ptype is datetime.datetime:
                vals_str = fstring.format(*["'{}'"]*part1,*["'{}'"]*part2)

            return vals_str.format(*self.array[:part1],*self.array[-part2:])

    def __repr__(self):
        """Console representation of column."""

        return f'curve(head="{self.head}", info="{self.info}", array={self._valstr(2)})'

    def __str__(self):
        """Print representation of column."""

        text = "{}\n"*4

        head = f"head\t: {self.head}"
        unit = f"unit\t: {self.unit}"
        info = f"info\t: {self.info}"
        vals = f"vals\t: {self._valstr(2)}"

        return text.format(head,unit,info,vals)

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

    def __getattr__(self,key):

        return getattr(self.array,key)

    def __setitem__(self,key,value):

        self.array[key] = value

    def __getitem__(self,key):

        return self.array[key]

    """PLOTTING"""

    def histogram(self,axis,logscale=False):

        show = True if axis is None else False

        if axis is None:
            axis = pyplot.figure().add_subplot()

        yaxis = self.array

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

    @property
    def info(self):
        return self._info
    