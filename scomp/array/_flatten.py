import numpy

def flatten(vals,_list=None):
    """Returns a flat list."""

    _list = [] if _list is None else _list

    if type(vals).__module__ == numpy.__name__:
        flatten(vals.tolist(),_list)
    elif isinstance(vals,str):
        _list.append(vals)
    elif hasattr(vals,"__iter__"):
        [flatten(val,_list) for val in list(vals)]
    else:
        _list.append(vals)

    return _list