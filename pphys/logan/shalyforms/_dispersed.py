import numpy

class dispersed():
	"""Dispersed shaly sand model for calculation of effective and total properties."""

	def __init__(self,archie,phinsh=0.35,phidsh=0.1):

		self.archie = archie

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

	def swe(self,phid,phis,phidcorr,phiim,rtotal,rwater):
		"""Calculates the effective saturation assuming that the resistivity of
		dispersed shale is much larger than the formation water resistivity."""

		phiim[phiim==0] = 0.0001

		phidcorr[phidcorr==0] = 0.0001

		q = (phid-phis)/phidcorr

		q[q==1] = 0.9999

		sw_effective = (((self.archie.a*rwater)/(phiim**2*rtotal)+q**2/4)**(1/2)-q/2)/(1-q)

		sw_effective[sw_effective>1] = 1
		sw_effective[sw_effective<0] = 0

		return sw_effective

	def swt(self,phie,phit,swe):
		"""Calculates total porosity from effective saturation."""

		sw_total = 1-phie/phit*(1-swe)

		sw_total[sw_total>1] = 1
		sw_total[sw_total<0] = 0

		return sw_total

	def bwt(self,phit,swt):
		"""Calculates bulk water total volume"""
		return phit*swt

	def bwb(self,phit,phie):
		"""Calculates bulk water bound"""
		return phit-phie