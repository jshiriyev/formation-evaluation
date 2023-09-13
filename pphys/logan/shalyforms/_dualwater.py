import numpy

from scipy.optimize import root_scalar

from borepy.pphys.logan._wrappers import trim

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

	@trim
	def swbound_woodhouse(self,phit,vshale,phishale):
		"""Returns bound water saturation based on:

		phit 		: total porosity,
		vshale 		: shale volume
		phishale 	: shale porosity, some weighted average of the
					  neutron and density porosity of shale"""

		return vshale*phishale/phit

	@trim
	def swbound_gr(self,gammaray,phit,M=0.0015,B=-0.1):
		"""Returns bound water saturation based Gamma-Ray logs."""
		return M*(gammaray/phit)+B

	@trim
	def swbound_dn(self,phit,phit_CL,vdc,vdc_CL):
		"""Returns bound water saturation based on Density-Neutron cross-plot.
		dry clay (DC), wet clay (CL)"""
		return (phit_CL/phit)*(vdc/vdc_CL)

	@trim
	def swbound_sp(self):
		"""Returns bound water saturation based on Spontaneous Potential log."""
		return

	@trim
	def swbound_res(self):
		"""Returns bound water saturation based on resistivity log."""
		return

	@trim
	def swbound_sd(self):
		"""Returns bound water saturation based on Sonic-Density cross-plot."""
		return 

	def rwbound(self,rshale,phishale):
		"""Calculates bound water resistivity based on:
		rshale 		: shale resistivity, and
		phishale 	: shale porosity, some weighted average of the
					  neutron and density porosity of shale"""
		return rshale*phishale**2

	@trim
	def swt(self,phit,swbound,rwbound,rwater,rtotal):
		"""Calculates total water saturation based on dual-water model.
		
		phit 	: total porosity

		swbound	: bound water saturation
		rwbound	: bound water resistivity
		rwater	: formation water resistivity
		rtotal	: true formation resistivity

		"""
		size = phit.size

		saturation = numpy.zeros(size)

		swbound = set_value_iterable(swbound,size)
		rwbound = set_value_iterable(rwbound,size)
		rwater = set_value_iterable(rwater,size)
		rtotal = set_value_iterable(rtotal,size)

		zipped = zip(phit,swbound,rwbound,rwater,rtotal)

		for index,(por,swb,rwb,rw,rt) in enumerate(zipped):

			solver = root_scalar(
				dualwater.swt_forward,
				method = 'newton', x0 = 1,
				fprime = dualwater.swt_derivative,
				args = (por,swb,rwb,rw,rt,
					self._archie.a,
					self._archie.m,
					self._archie.n,
					),
				)

			saturation[index] = solver.root

		return saturation

	@trim
	def swe(self,swt,swbound):
		"""Calculates effective water saturation."""
		return (swt-swbound)/(1-swbound)

	@trim
	def phie(self,phit,swbound):
		"""Calculates the effective porosity."""
		return phit*(1-swbound)

	def bwb(self,phit,swbound):
		"""Calculates bulk water bound"""
		return phit*swbound

	def bwt(self,phit,swt):
		"""Calculates bulk water total volume."""
		return phit*swt

	@staticmethod
	def swt_forward(swt,por,swb,rwb,rw,rt,a,m,n):
		"""Implementing forward saturation equation for each depth point
		based on the dual-water model, A*(Swt)**n+B*(Swt)**(n-1)+C = 0"""
		return swt**n-swb*(1-rw/rwb)*swt**(n-1)-(a/por**m)*(rw/rt)
		
	@staticmethod
	def swt_derivative(swt,por,swb,rwb,rw,rt,a,m,n):
		"""Implementing derivative of forward saturation equation for each
		depth point based on the dual-water model"""
		return n*swt**(n-1)-(n-1)*swb*(1-rw/rwb)*swt**(n-2)

	@property
	def archie(self):
		return self._archie

def set_value_iterable(entry,size):

	try:
		iter(entry)
	except TypeError:
		entry = [entry for _ in range(size)]

	return entry	