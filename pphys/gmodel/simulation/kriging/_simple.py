import numpy

from scipy.stats import norm

from gmodel.utils._spatial import Spatial

from gmodel.gstats._variogram import Variogram

class Simple():

    @staticmethod
    def simple(obsdata:Spatial,estdata:Spatial,mean:float=None):

        if mean is None:
            self.mean = obsdata.mean()
        else:
            self.mean = mean
        
        "perc -> percentile, perc=0.5 gives mean values"

        self.distance = estdata.distmat(obsdata)
        
        _,self.covariance = SpatProp.get_varmodel(
            self.distance,self.obs.type,
            self.obs.sill,self.obs.range,
            self.obs.nugget)

        self.lambdas = numpy.linalg.solve(self.obs.covariance,self.covariance)
        
        calc_diff_arr = self.obs.reshape((-1,1))-self.mean
        calc_prop_mat = self.lambdas*(calc_diff_arr)
        calc_vars_mat = self.lambdas*self.covariance
        
        estimate = self.mean+calc_prop_mat.sum(axis=0)
        variance = self.obs.sill-calc_vars_mat.sum(axis=0)

        return estimate,variance

    @staticmethod
    def percentile(estimate,variance,perc=0.5):
        """perc -> percentile, perc=0.5 gives mean values"""
        return estimate+norm.ppf(perc)*numpy.sqrt(variance)