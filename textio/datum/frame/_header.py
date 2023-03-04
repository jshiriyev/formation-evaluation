from .special._ints import ints
from .special._floats import floats
from .special._strs import strs
from .special._dates import dates
from .special._datetimes import datetimes

class Header():
    """It is a table of params, columns are fields."""

    def __init__(self,**kwargs):
        """Parameters should be predefined, all entries must be string.
        
        kwarg example is {param:field}

        param   : name of the parameter
        field   : string or list of strings
        
        """

        # if len(kwargs)==0:
        #     raise ValueError("At least one field is required.")

        params = []
        fields = []

        fsizes = []

        for param,field in kwargs.items():

            params.append(param)

            if isinstance(field,list) or isinstance(field,tuple):
                field = [str(data) for data in field]
            else:
                field = [str(field)]

            fields.append(field)
            fsizes.append(len(field))

        if len(set(fsizes))>1:
            raise ValueError("The lengths of field are not equal!")

        super().__setattr__("params",params)
        super().__setattr__("fields",fields)

    def extend(self,row):

        if len(self.params)!=len(row):
            raise ValueError("The lengths of 'fields' and 'row' are not equal!")

        if isinstance(row,list) or isinstance(row,tuple):
            toextend = header(**dict(zip(self.params,row)))
        elif isinstance(row,dict):
            toextend = header(**row)
        elif isinstance(row,header):
            toextend = row

        for param,field in toextend.items():
            self.fields[self.params.index(param)].extend(field)

    def __setattr__(self,key,vals):

        raise AttributeError(f"'Header' object has no attribute '{key}'.")

    def __getattr__(self,param):

        field = self.fields[self.params.index(param)]

        _field = [] # it may actually return numbers too.

        for value in field:

            try:
                _field.append(float(value))
            except ValueError:
                _field.append(value)

        if len(_field)==1:

            _field, = _field

        return _field

    def __getitem__(self,key):

        if not isinstance(key,str):
            raise TypeError("key must be string!")

        for row in self:
            if row[0].lower()==key.lower():
                break
        
        return Header(**dict(zip(self.params,row)))

    def __repr__(self,fstring=None,comment=None):

        return self.__str__(fstring=fstring,comment=comment)

    def __str__(self,fstring=None,comment=None,skip=False):

        if len(self)==1:
            return repr(tuple(self.fields))

        if comment is None:
            comment = ""

        underline = []

        fstringFlag = True if fstring is None else False

        if fstringFlag:
            fstring = comment

        for param,field in zip(self.params,self.fields):

            field_ = list(field)
            field_.append(param)

            count_ = max([len(value) for value in field_])

            if fstringFlag:
                fstring += f"{{:<{count_}}}   "
            
            if fstringFlag:
                underline.append("-"*count_)
            else:
                underline.append("-"*len(param))

        fstring += "\n"

        text = ""

        if not skip:
            text += fstring.format(*[parm.capitalize() for parm in self.params])
            text += fstring.format(*underline)
        
        for row in self:
            text += fstring.format(*row)

        return text

    def __iter__(self):

        return iter([row for row in zip(*self.fields)])

    def __len__(self):

        if isinstance(self.fields[0],str):
            return 1
        else:
            return len(self.fields[0])

    def items(self):

        return iter([(p,f) for p,f in zip(self.params,self.fields)])