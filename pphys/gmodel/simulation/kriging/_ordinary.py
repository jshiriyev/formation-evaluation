import sys

if __name__ == "__main__":
	sys.path.append(r'C:\Users\3876yl\Documents\gmodel')

import numpy

from scipy.stats import norm

from utils._spatial import Spatial

from gmodel.gstats.variogram._theoretical import Theoretical

class Ordinary():

	def __init__(self,obs:Spatial,var:Theoretical):

		self._obs = obs

		self._var = var

	def estimate(self,est:Spatial):
		"""Returns the best estimated values and varitation for est data."""

		sol = numpy.linalg.solve(
			self._lefthandside(),
			self._righthandside(est)
			)

		lamda,beta = sol[:-1,:],sol[-1,:]

		pmat = lamda*self._obs.reshape((-1,1))

		vmat = lamda*self.__crhs

		est = pmat.sum(axis=0)

		var = self._var.sill-beta-vmat.sum(axis=0)

		return est,var

	def __call__(self,est:Spatial,frac=0.5):
		"""Returns percentile for the estimated values
		If frac is 0.5, it returns the best estimate."""

		est,var = self.estimate(est)

		return est+norm.ppf(frac)*numpy.sqrt(var)

	def _distmat(self,est:Spatial=None):
		"""Constructs distance matrix for est (m,) and obs (n,) data.
		Returned matrix shape is (m,n)."""
		est = self._obs if est is None else est
		return est.get_distmat(self._obs)

	def _varmat(self,est:Spatial=None):
		"""Constructs variogram matrix for est (m,) and obs (n,) data.
		Returned matrix shape is (m,n)."""
		return self._var(self._distmat(est))

	def _covmat(self,est:Spatial=None):
		"""Constructs covariance matrix for est (m,) and obs (n,) data.
		Returned matrix shape is (m,n)."""
		return self._var.sill-self._varmat(est)

	def _lefthandside(self):
		"""Constructs the left-hand-side matrix for ordinary kriging calculations."""

		cmat = self._covmat()

		cmat = self._colappend(cmat)
		cmat = self._rowappend(cmat)

		cmat[-1,-1] = 0

		return cmat

	def _righthandside(self,est:Spatial):
		"""Constructs the right-hand-side matrix for ordinary kriging calculations."""

		self.__crhs = self._covmat(est)

		return self._rowappend(self.__crhs)

	@staticmethod
	def _colappend(mat):
		return numpy.append(mat,numpy.ones(mat.shape[0]).reshape((-1,1)),axis=1)

	@staticmethod
	def _rowappend(mat):
		return numpy.append(mat,numpy.ones(mat.shape[1]).reshape((1,-1)),axis=0)

if __name__ == "__main__":

	yobs = numpy.array([30,50,20])
	dobs = numpy.array([2.,4.,6.])

	dest = numpy.array([3.,5.,8.])

	dest = Spatial(None,dest)

	class var():

		def __init__(self):

			self.sill = 100
			self.vrange = 10
			self.nugget = 0

		def __call__(self,bins):

			return 100-100*numpy.exp(-0.3*bins)

	obs = Spatial(yobs,dobs)

	krig = Ordinary(obs,var())

	est,err = krig.estimate(dest)

	print(est)

	print(err)

	print(krig(dest,frac=0.5))

