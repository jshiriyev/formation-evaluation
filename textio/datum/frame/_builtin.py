class Frame():

    def __init__(self,_list):

        self._list = _list

    def __str__(self):

        return str(self._list)

    def __repr__(self):

        return repr(self._list)

    def __getitem__(self,key):

        _frame = self._list[key]

        if isinstance(_frame,list):
            return Frame(_frame)
        else:
            return _frame

    def __getattr__(self,key):

        return getattr(self._list,key)

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

    def __len__(self):

        return len(self._list)

    def __iter__(self):

        return iter(self._list)

if __name__ == "__main__":

    fr = Frame([[1,2],[3,4],[None,None],[5,6]])

    fr = fr.drop()
    fr = fr.transpose()

    for line in fr:
        print(line)