# DO NOT TOUCH REPEAT, IT'S WORKING PERFECTLY FINE!

import math

from ._flatten import flatten

def repeat(vals,times:int=None,size:int=None,flat:bool=True):
    """Returns list with specified length.

    times   : how many times to repeat the list. If None, size must be specified.
    size    : The length of flat list to be created by repeating.
    flat    : If vals is not flat, it will be flattened.

    If vals has zero length, vals itself will be returned.
    """

    if not flat:
        vals = flatten(vals)

    if isinstance(vals,numpy.ndarray):
        vals = vals.tolist()

    if len(vals)==0:
        return vals

    if times is None:
        size = len(vals) if size is None else size
        times = math.ceil(size/len(vals))

    if size is None:
        return (vals*times)

    return (vals*times)[:size]

if __name__ == "__main__":

    a = repeat([1,2,3,[1,2]],flat=False)

    print(a)

    a = repeat([1,2,3,[1,2]],size=7,flat=True)

    print(a)

    a = repeat([1,2,3,[1,2]],size=7,flat=False)

    print(a)

    a = repeat([1,2,3,[1,2]],times=2,flat=False)

    print(a)