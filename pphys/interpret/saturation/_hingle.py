from dataclasses import dataclass

import numpy

from borepy.utils._wrappers import trim

class hingle():

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

    def set_axis(self,axis=None):

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        self.axis = axis

    def show(self):

        pyplot.show()

    @trim
    def saturation(self):
        return