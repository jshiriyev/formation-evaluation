import numpy

from scipy.optimize import root_scalar

class dispersed():
	"""Dispersed shale is an inexact term used to describe clay overgrowths on the
	matrix material (for example, sand grains). These clay particles reduce porosity
	and permeability within the pore structure of the sandstone."""
	
	def __init__(self,archie,phinsh=0.35,phidsh=0.1):
		"""Dispersed shaly sand model for calculation of effective and total properties."""
		self._archie = archie

		self.phinsh = phinsh	# apparent neutron porosity in the shale
		self.phidsh = phidsh 	# apparent density porosity in the shale

	def phie_bateman(self,phin,phid):
		"""Calculates the effective porosity."""
		return (self.phinsh*phid-self.phidsh*phin)/(self.phinsh-self.phidsh)

	def vshale_bateman(self,phin,phid):
		"""Calculates the shale content in a dispersed shale model."""
		return (phin-phid)/(self.phinsh-self.phidsh)

	def qvalue_dewitte(self,phis,phid):
		"""Calculates integranular space filled with clay"""
		return (phis-phid)/phis

	def sw_dewitte(self,phiim,qvalue,rwater,rshale,rtotal):
		"""Calculates water saturation (equivalent of Swe) based on de Witte's (1950) model,
		full equation.

		phiim 	: intermatrix porosity, which includes all the space occupied by fluids and
				  dispersed shale, can be obtained directly from a sonic log
		qvalue 	: the fraction of the intermatrix porosity occupied by the dispersed shale
		rwater 	: formation water resistivity
		rshale 	: the resistivity of the dispersed shale
		rtotal 	: true formation resistivity

		sw 		: the water saturation in the fraction of true effective formation porosity
		"""
		swn_clean = (self._archie.a*rwater)/(phiim**self._archie.m*rtotal)

		term1 = (qvalue*(rshale-rwater)/(2*rshale))**2
		term2 = qvalue*(rshale+rwater)/(2*rshale)

		return ((swn_clean+term1)**(1/2)-term2)/(1-qvalue)

	def sw_dewitte_simplified(self,phiim,qvalue,rwater,rtotal):
		"""Calculates water saturation (equivalent of Swe) based on de Witte's (1950) model
		assuming that the resistivity of dispersed shale is much larger than the formation
		water resistivity simplifying the equation to neglect it.

		phiim 	: intermatrix porosity, which includes all the space occupied by fluids and
				  dispersed shale, can be obtained directly from a sonic log
		qvalue 	: the fraction of the intermatrix porosity occupied by the dispersed shale
		rwater 	: formation water resistivity
		rtotal 	: true formation resistivity

		sw 		: the water saturation in the fraction of true effective formation porosity
		"""
		swn_clean = (self._archie.a*rwater)/(phiim**self._archie.m*rtotal)

		return ((swn_clean+(qvalue/2)**2)**(1/2)-qvalue/2)/(1-qvalue)

	def sim_dewitte(self,sw_dewitte,qvalue):
		"""Calculates the fraction of the intermatrix porosity occupied by the formation-water,
		dispersed-shale mixture."""
		return qvalue+sw_dewitte*(1-qvalue)

	def swt_bateman(self,phit,vshale,rwater,rshale,rtotal):
		"""Calculates total water saturation based on dispersed shale model."""

		size = phit.size

		saturation = numpy.zeros(size)

		vshale = set_value_iterable(vshale,size)
		rwater = set_value_iterable(rwater,size)
		rshale = set_value_iterable(rshale,size)
		rtotal = set_value_iterable(rtotal,size)

		zipped = zip(phit,vshale,rwater,rshale,rtotal)

		for index,(port,vsh,rw,rsh,rt) in enumerate(zipped):

			solver = root_scalar(
				dispersed.swt_bateman_forward,
				method = 'newton', x0 = 1,
				fprime = dispersed.swt_bateman_derivative,
				args = (port,vsh,rw,rsh,rt,
					self._archie.a,
					self._archie.m,
					self._archie.n,
					),
				)

			saturation[index] = solver.root

		return saturation

	def swe_bateman(self,swt,phie,phit):
		"""Calculates effective saturation from total saturation."""
		return 1-phit/phie*(1-swt)

	def bwt_bateman(self,phit,swt):
		"""Calculates bulk water total volume"""
		return phit*swt

	def bwb_bateman(self,phit,phie):
		"""Calculates bulk water bound"""
		return phit-phie

	@staticmethod
	def swt_bateman_forward(swt,port,vsh,rw,rsh,rt,a,m,n):
		"""Implementing forward saturation equation for each depth point
		based on the dispersed shale model, A*(Sw)**n+B*(Sw)+C = 0"""
		return (port**m)/(a*rw)*swt**n+port*vsh/a*(1/rsh-1/rw)*swt-1/rt

	@staticmethod
	def swt_bateman_derivative(swt,port,vsh,rw,rsh,rt,a,m,n):
		"""Implementing derivative of forward saturation equation for each
		depth point based on the dispersed shale model"""
		return n*(port**m)/(a*rw)*swt**(n-1)+port*vsh/a*(1/rsh-1/rw)

	@property
	def archie(self):
		return self._archie

def set_value_iterable(entry,size):

	try:
		iter(entry)
	except TypeError:
		entry = [entry for _ in range(size)]

	return entry