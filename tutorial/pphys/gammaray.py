import matplotlib.pyplot as plt

import numpy

import _setup

from pphys import gammaray

values = numpy.linspace(0,1,100)

gr = gammaray(values)

index = gr.get_shaleindex()

plt.plot(index,gr.get_shalevolume(model='linear'),label='linear')
plt.plot(index,gr.get_shalevolume(model='larionov_oldrocks'),label='larionov_oldrocks')
plt.plot(index,gr.get_shalevolume(model='clavier'),label='clavier')
plt.plot(index,gr.get_shalevolume(model='bateman'),label='bateman')
plt.plot(index,gr.get_shalevolume(model='stieber'),label='stieber')
plt.plot(index,gr.get_shalevolume(model='larionov_tertiary'),label='larionov_tertiary')

plt.xlim((0,1))
plt.ylim((0,1))

plt.xlabel('index')
plt.ylabel('volume')

plt.legend()

plt.show()
