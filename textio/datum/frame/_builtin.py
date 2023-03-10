class Frame():
    """One or Two dimensional list"""

    def __init__(self,_list):
        """Initialization of 1 or 2 dimensional lists."""

        self._list = _list

    def __str__(self):

        return str(self._list)

    def __repr__(self):

        return repr(self._list)

    def __setitem__(self,key,value):

        self._list.__setitem__(key,value)

    def __getitem__(self,key):

        _frame = self._list[key]

        if isinstance(_frame,list):
            return Frame(_frame)
        else:
            return _frame

    def __getattr__(self,key):

        return getattr(self._list,key)

    def ndims(self):

        return _ndims(self._list)

    def tofloat(self):

        ndims = self.ndims()

        if ndims == 1:
            _frame = _tofloat(self._list)
        elif ndims == 2:
            _frame = [_tofloat(_list) for _list in self._list]
        else:
            raise ValueError(f"Can not do {ndims} dimensional conversion for now.")

        return Frame(_frame)

    def tolist(self):

        return self._list

    def transpose(self):
        """From row wise to column wise data or vice versa."""

        _frame = []

        try:
            _list0 = self._list[0]
        except IndexError:
            return self

        if isinstance(_list0,str):
            numcols = 1
        else:
            try:
                numcols = len(_list0)
            except TypeError:
                numcols = 1

        for index in range(numcols):

            if numcols == 1:
                row = [[item] for item in self._list]
            else:
                row = [_list[index] for _list in self._list]

            _frame.append(row)

        return Frame(_frame)

    def drop(self):
        """Drop lists with all None."""

        _frame = []

        for _list in self._list:

            if not isinstance(_list,list):
                if _list is not None:
                    _frame.append(_list)

            elif _list.count(None)<len(_list):
                _frame.append(_list)

        return Frame(_frame)

    def merge(self,refill=False):

        if not refill:
            return Frame([" ".join(column) for column in self.transpose()])

        for i,row in enumerate(self._list):

            for j,col in enumerate(row):

                if j>1:
                    self._list[i][j] = self._list[i][j-1] if col is None else col.strip()
                else:
                    self._list[i][j] = "" if col is None else col.strip()

        _list = [" ".join(column) for column in self.transpose()]

        return Frame(_list)

    def __len__(self):

        return len(self._list)

    def __iter__(self):

        return (Frame(l) if _isnested(l) else l for l in self._list)

def _ndims(_list,_dims=1):

    if _isnested(_list):
        return _ndims(_list[0],_dims=_dims+1)
    else:
        return _dims

def _isnested(_list):

    try:
        list0 = _list[0]
    except IndexError:
        return False
    except TypeError:
        return False

    if isinstance(list0,list):
        return True

    return False

def _tofloat(_list):

    _new_list = []

    for value in _list:

        try:
            value = float(value)
        except TypeError:
            value = None
        except ValueError:
            value = None

        _new_list.append(value)

    return _new_list


if __name__ == "__main__":

    fr = Frame([[1,2],[3,4],[None,None],[5,6]])

    fr = fr.drop()
    fr = fr.transpose()

    for line in fr:
        for a in line:
            print(a)
            print(type(a))

    print(fr)

    print(fr.ndims())