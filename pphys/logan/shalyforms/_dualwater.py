import numpy

from scipy.optimize import root_scalar

class dualwater():
	"""The dual water model proposes that two distinct waters can be found in the pore space.
	Close to the surface of the grains, bound water of resistivity RwB is encountered. This
	water is fresher (more resistive) than the remaining water farther away from the grain surface.
	
	This far water of resistivity RwF is more saline (less resistive) than the bound water
	and is free to move in the pores. The model suggests that the amount of bound water is
	directly related to the clay content of the formation. Therefore, as clay volume increases,
	the portion of the total porosity occupied by bound water increases."""

	def __init__(self,archie):

		self._archie = archie

	def vshale(self,phin,phid):
		"""Calculates the shale volume."""
		return (phin-phid)/(self.phinsh-self.phidsh)

	def swbound(self,phit,vshale,phishale):
		"""Calculates bound water saturation based on total porosity, phit, shale volume, vshale, and
		shale porosity, phishale (some weighted average of the neutron and density porosity of shale)."""
		return vshale*phishale/phit

	def phie(self,phit,swbound):
		"""Calculates the effective porosity."""
		return phit*(1-swbound)

	def rwbound(self,rshale,phishale):
		"""Calculates bound water resistivity based on shale resistivity, rshale, and
		shale porosity, phishale (some weighted average of the neutron and density porosity of shale)."""
		return rshale*phishale**2

	def swt(self,phit,swbound,rwbound,rwater,rtotal):
		"""Calculates total water saturation based on dual-water model.
		
		phit 	: total porosity

		swbound	: bound water saturation
		rwbound	: bound water resistivity
		rwater	: formation water resistivity
		rtotal	: true formation resistivity

		"""
		saturation = numpy.zeros(phit.shape)

		for index,(port,sb,rb,rw,rt) in enumerate(zip(phit,swbound,rwbound,rwater,rtotal)):

			solver = root_scalar(
				dispersed_shale.swt_forward,
				method = 'newton', x0 = 1,
				fprime = dispersed_shale.swt_derivative,
				args = (port,sb,rb,rw,rt,
					self._archie.a,
					self._archie.m,
					self._archie.n,
					),
				)

			saturation[index] = solver.root

		return saturation

	def swe(self,swt,swbound):
		"""Calculates effective water saturation."""
		return (swt-swbound)/(1-swbound)

	@staticmethod
	def swt_forward(swt,port,sb,rb,rw,rt,a,m,n):
		"""Implementing forward saturation equation for each depth point
		based on the dual-water model, A*(Swt)**n+B*(Swt)**(n-1)+C = 0"""
		return swt**n-sb*(1-rw/rb)*swt**(n-1)-(a/port**m)*(rw/rt)
		
	@staticmethod
	def swt_derivative(swt,port,sb,rb,rw,rt,a,m,n):
		"""Implementing derivative of forward saturation equation for each
		depth point based on the dual-water model"""
		return n*swt**(n-1)-(n-1)*sb*(1-rw/rb)*swt**(n-2)

	@property
	def archie(self):
		return self._archie
	