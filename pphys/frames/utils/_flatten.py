# DO NOT TOUCH FLATTEN, IT'S WORKING PERFECTLY FINE!

import numpy

def flatten(vals,prevlist=None):
    """Returns a flat list. Input vals can be of any type.
    If prevlist is defined, the result will be concatenated to it."""

    prevlist = [] if prevlist is None else prevlist

    if type(vals).__module__ == numpy.__name__:
        flatten(vals.tolist(),prevlist)
    elif isinstance(vals,str):
        prevlist.append(vals)
    elif hasattr(vals,"__iter__"):
        [flatten(val,prevlist) for val in list(vals)]
    else:
        prevlist.append(vals)

    return prevlist

if __name__ == "__main__":

    a = flatten([1,2,3,[4,5]])
    # a = flatten(numpy.array(5))

    print(a)