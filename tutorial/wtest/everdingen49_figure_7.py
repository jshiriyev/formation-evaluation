import numpy

import matplotlib.pyplot as plt

from borepy.wtest import everdingen1949

tD1 = numpy.logspace(2,4,2000)
tD2 = numpy.logspace(3,5,2000)
tD3 = numpy.logspace(4,6,2000)

pwD1 = everdingen1949.pressure(tD1)
pwD2 = everdingen1949.pressure(tD2)
pwD3 = everdingen1949.pressure(tD3)

plt.semilogx(tD1,pwD1)
plt.grid()

plt.show()

plt.semilogx(tD2,pwD2)
plt.grid()

plt.show()

plt.semilogx(tD3,pwD3)
plt.grid()

plt.show()