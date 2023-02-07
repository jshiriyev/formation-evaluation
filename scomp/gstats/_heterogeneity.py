from ._dykstraparson import dykstraparson
from ._lorenz import lorenz

def varcoeff(values):

    return values.std()/values.mean()