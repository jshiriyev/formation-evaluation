import numpy

from scipy.optimize import root_scalar

class dispersed_shale():
	"""Dispersed shaly sand model for calculation of effective and total properties."""

	def __init__(self,archie,phinsh=0.35,phidsh=0.1):

		self._archie = archie

		self.phinsh = phinsh
		self.phidsh = phidsh

	def phie(self,phin,phid,phincorr,phidcorr,vshale=None):
		"""Calculates the effective porosity (phie) and recalculates shale volume for shaly zones."""

		phi_effective = ((phincorr**2+phidcorr**2)/2)**(1/2)

		shalypoints = phincorr>phidcorr

		phi_effective[shalypoints] = 
			(phidcorr[shalypoints]*self.phinsh-phincorr[shalypoints]*self.phidsh)/(self.phinsh-self.phidsh)

		phi_effective[phi_effective>1] = 1
		phi_effective[phi_effective<0] = 0

		if vshale is None:
			return phi_effective

		vshale[shalypoints] = (phin[shalypoints]-phid[shalypoints])/(self.phinsh-self.phidsh)

		vshale[shalypoints][vshale[shalypoints]>1] = 1
		vshale[shalypoints][vshale[shalypoints]<0] = 0

		return phi_effective,vshale

	def phit(self,phin,phid):
		"""Calculates the total porosity (phit)."""
		return (phin+phid)/2

	def swt(self,phit,vshale,rwater,rshale,rtotal):
		"""Calculates total water saturation based on dispersed shale model."""
		saturation = numpy.zeros(phie.shape)

		for index,(port,vsh,rw,rsh,rt) in enumerate(zip(phit,vshale,rwater,rshale,rtotal)):

			solver = root_scalar(
				dispersed_shale.swt_forward,
				method = 'newton', x0 = 1,
				fprime = dispersed_shale.swt_derivative,
				args = (port,vsh,rw,rsh,rt,
					self._archie.a,
					self._archie.m,
					self._archie.n,
					),
				)

			saturation[index] = solver.root

		return saturation

	def swe(self,phie,phit,swe):
		"""Calculates effective porosity from total saturation."""

		sw_effective = 1-phit/phie*(1-swt)

		sw_effective[sw_effective>1] = 1
		sw_effective[sw_effective<0] = 0

		return sw_effective

	def bwt(self,phit,swt):
		"""Calculates bulk water total volume"""
		return phit*swt

	def bwb(self,phit,phie):
		"""Calculates bulk water bound"""
		return phit-phie

	@staticmethod
	def swt_forward(swt,port,vsh,rw,rsh,rt,a,m,n):
		"""Implementing forward saturation equation for each depth point
		based on the dispersed shale model, A*(Sw)**n+B*(Sw)+C = 0"""
		return (port**m)/(a*rw)*swt**n+port*vsh/a*(1/rsh-1/rw)*swt-1/rt

	@staticmethod
	def swt_derivative(sw,port,vsh,rw,rsh,rt,a,m,n):
		"""Implementing derivative of forward saturation equation for each
		depth point based on the dispersed shale model"""
		return n*(port**m)/(a*rw)*swt**(n-1)+port*vsh/a*(1/rsh-1/rw)

	@property
	def archie(self):
		return self._archie

class dispersed_clay():

	def __init__(self,archie):
		"""de Witte (1950) model"""
		self._archie = archie

	def qvalue(self,phis,phid):
		"""Calculates integranular space filled with clay"""
		return (phis-phid)/phis

	def sw(self,phiim,qvalue,rwater,rshale,rtotal):
		"""
		phiim 	: intermatrix porosity, which includes all the space occupied by fluids and dispersed shale
		qvalue 	: the fraction of the intermatrix porosity occupied by the dispersed shale
		rwater 	: formation water resistivity
		rshale 	: the resistivity of the dispersed shale
		rtotal 	: true formation resistivity

		sw 		: the water saturation in the fraction of true effective formation porosity
		"""
		swn_clean = (self._archie.a*rwater)/(phiim**self._archie.m*rtotal)

		term1 = (qvalue*(rshale-rwater)/(2*rshale))**2
		term2 = qvalue*(rshale+rwater)/(2*rshale)

		saturation = ((swn_clean+term1)**(1/2)-term2)/(1-qvalue)

		saturation[saturation>1] = 1
		saturation[saturation<0] = 0

		return saturation

	def sw_simplified(self,phiim,qvalue,rwater,rshale,rtotal):
		"""Calculates the water saturation assuming that the resistivity of
		dispersed shale is much larger than the formation water resistivity.

		phiim 	: intermatrix porosity, which includes all the space occupied by fluids and dispersed shale
		qvalue 	: the fraction of the intermatrix porosity occupied by the dispersed shale
		rwater 	: formation water resistivity
		rshale 	: the resistivity of the dispersed shale
		rtotal 	: true formation resistivity

		sw 		: the water saturation in the fraction of true effective formation porosity
		"""
		swn_clean = (self._archie.a*rwater)/(phiim**self._archie.m*rtotal)

		saturation = ((swn_clean+(qvalue/2)**2)**(1/2)-qvalue/2)/(1-qvalue)

		saturation[saturation>1] = 1
		saturation[saturation<0] = 0

		return saturation

	@property
	def archie(self):
		return self._archie