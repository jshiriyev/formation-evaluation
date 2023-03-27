import numpy

class dispersed():
	"""Dispersed shaly sand model for calculation of effective and total properties."""

	def __init__(self):
		"""
		Requirements:

		input 1	: Gamma-ray or shale volume
		input 2	: Bulk density or density porosity
		input 3	: Neutron porosity
		input 4	: Acoustic transit time
		input 5	: True resistivity of the formation
		
		"""
		pass

	def shalevolume(self,gamma=None,vsh=None,gmin=None,gmax=None):
		"""Calculates shale volume, vsh. If vsh is not None, it skips the calculations.
		
		vsh 	: pre calculated shale volume
		gamma 	: Gamma-Ray Log response
		gmin 	: Gamma-Ray value in clean formations
		gmax 	: Gamma-Ray value in shales
		"""

		if vsh is not None:
			self.vsh = vsh
		
		else:
			self.gamma = gamma

			if gmin is None:
				gmin = numpy.nanmin(self.gamma)

			if gmax is None:
				gmax = numpy.nanmax(self.gamma)

			self.vsh = (self.gamma-gmin)/(gmax-gmin)

		self.vsh[self.vsh>1] = 1
		self.vsh[self.vsh<0] = 0

	def densityporosity(self,rhob=None,phid=None,rhom=2.65,rhof=1.0,phidsh=0.1):
		"""Sets density porosity and calculates shale corrected density porosity.

		phid 	: Density Porosity
		rhob 	: Bulk Density
		rhom 	: Matrix Density
		rhof 	: Fluid Density
		phidsh 	: density porosity at shale

		phidcor : shale corrected density porosity
		
		"""

		if phid is None:
			self.rhob = rhob
			self.phid = (rhom-self.rhob)/(rhom-rhof)
		else:
			self.phid = phid

		self.phid[self.phid>1] = 1
		self.phid[self.phid<0] = 0

		self.phidsh = phidsh

		self.phidcor = self.phid-self.vsh*phidsh

		self.phidcor[self.phidcor>1] = 1
		self.phidcor[self.phidcor<0] = 0

	def neutronporosity(self,phin,phinsh=0.35):
		"""Sets the neutron porosity and calculates shale corrected neutron porosity.
		
		phin 	: neutron porosity
		phinsh 	: neutron porosity at shale

		phincor : shale corrected neutron porosity

		"""

		self.phin = phin

		self.phin[self.phin>1] = 1
		self.phin[self.phin<0] = 0

		self.phinsh = phinsh

		self.phincor = self.phin-self.vsh*self.phinsh

		self.phincor[self.phincor>1] = 1
		self.phincor[self.phincor<0] = 0

	def sonicporosity(self,dt,dtf=189,dtm=55.5):
		"""Sets the acoustic transit time and calculates sonic porosity.
		
		dt 		: acoustic transit time
		dtf 	: acoustic transit time for fluids
		dtm 	: acoustic transit time for matrix

		phis 	: sonic porosity

		"""

		self.dt = dt

		self.phis = (self.dt-dtm)/(dtf-dtm)

		self.phis[self.phis>1] = 1
		self.phis[self.phis<0] = 0

	def effectiveporosity(self):
		"""Calculates the effective porosity for all depths and recalculates shale volume for shaly zones.
		
		phie 	: effective porosity

		"""

		self.phie = ((self.phincor**2+self.phidcor**2)/2)**(1/2)

		shalypoints = self.phincor>self.phidcor

		phidcor = self.phidcor[shalypoints]
		phincor = self.phincor[shalypoints]

		self.phie[shalypoints] = (phidcor*self.phinsh-phincor*self.phidsh)/(self.phinsh-self.phidsh)

		self.phie[self.phie>1] = 1
		self.phie[self.phie<0] = 0

		phid = self.phid[shalypoints]
		phin = self.phin[shalypoints]

		self.vsh[shalypoints] = (phin-phid)/(self.phinsh-self.phidsh)

		self.vsh[self.vsh>1] = 1
		self.vsh[self.vsh<0] = 0

	def totalporosity(self):
		"""Calculates the total porosity.
		
		phit 	: total porosity

		"""

		self.phit = (self.phin+self.phid)/2

	def effectivesaturation(self,rt,rw,a=1):
		"""Calculates the effective saturation assuming that the resistivity of
		dispersed shale is much larger than the formation water resistivity."""

		phiim = self.phis.copy()

		phiim[phiim==0] = 0.0001

		phidcor = self.phidcor.copy()

		phidcor[phidcor==0] = 0.0001

		q = (self.phid-self.phis)/phidcor

		q[q==1] = 0.9999

		self.swe = (((a*rw)/(phiim**2*rt)+q**2/4)**(1/2)-q/2)/(1-q)

		self.swe[self.swe>1] = 1
		self.swe[self.swe<0] = 0

	def totalsaturation(self):
		"""Calculates total porosity from effective saturation."""

		self.swt = 1-self.phie/self.phit*(1-self.swe)

		self.swt[self.swt>1] = 1
		self.swt[self.swt<0] = 0

	def bulkwatertotal(self):
		"""Calculates bulk water volume"""

		self.bwt = self.phit*self.swt

	def bulkwaterbound(self):
		"""Calculates bound water volume"""

		self.bwb = self.phit-self.phie