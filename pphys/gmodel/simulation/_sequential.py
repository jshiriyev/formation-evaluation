import numpy

from gmodel.utils._spatial import Spatial

from gmodel.gstats._variogram import Variogram

from gmodel.gstats._kriging import Kriging

class Sequential():

    @staticmethod
    def gaussian(estimate,variance):

        perc = numpy.random.rand(self.x.size)

        return Kriging.percentile(estimate,variance,perc=perc)

    @staticmethod
    def sequential():

        pass