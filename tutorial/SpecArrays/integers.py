import numpy as np

import _setup

from arrays import integers

a = integers([1,2,3,4,5,6,-99_999,"01.,5"],null=-99_999)
b = np.array([1,2,3,4,5,6,-10000,-10000])

c = integers([True,False,False])
d = integers(True)

x = a.view(np.ndarray).astype('float64')

# print(a.issorted)
# print(b)
# print(a.dtype)
# print(b.dtype)

# print(a+b)
# print(a*b)
# print(a-b)
# print(a/b)
# print(a//b)

# print(a==-99999)

# print(None==None)