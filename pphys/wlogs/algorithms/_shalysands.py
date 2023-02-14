from matplotlib import pyplot

import numpy

class shalysands():

	def __init__(self,gamma,density,neutron):

		self.gamma = gamma

		self.density = density
		self.neutron = neutron

	def shalevolume(self,gmin=None,gmax=None,Vsh=None):

		if Vsh is not None:
			self.Vsh = Vsh
			return

		if gmin is None:
			gmin = numpy.nanmin(self.gamma)

		if gmax is None:
			gmax = numpy.nanmax(self.gamma)

		self.Vsh = (self.gamma-gmin)/(gmax-gmin)

		self.Vsh[self.Vsh>1] = 1
		self.Vsh[self.Vsh<0] = 0

	def densityporosity(self,rhomatrix=2.65,rhofluid=1.0,phiD=None,phiDshale=0):

		if phiD is None:
			phiD = (rhomatrix-self.density)/(rhomatrix-rhofluid)

		self.phiD = phiD

		self.phiDshale = phiDshale

		self.phiDcor = self.phiD-self.Vsh*phiDshale

		self.phiDcor[self.phiDcor<0] = 0

	def neutronporosity(self,phiN=None,phiNshale=0):

		if phiN is None:
			self.phiN = self.neutron
		else:
			self.phiN = phiN

		self.phiNshale = phiNshale

		self.phiNcor = self.phiN-self.Vsh*phiNshale

		self.phiNcor[self.phiNcor<0] = 0

	def sonicporosity(self,DTcomp,DTfluid=189,DTmatrix=55.5):

		self.phiS = (DTcomp-DTmatrix)/(DTfluid-DTmatrix)

		self.phiS[self.phiS<0] = 0

	def effectiveporosity(self):

		# cond1 = self.phiNcor<self.phiDcor

		self.phiE = numpy.sqrt((self.phiNcor**2+self.phiDcor**2)/2)

		cond2 = self.phiNcor>self.phiDcor

		phiDcor = self.phiDcor[cond2]
		phiNcor = self.phiNcor[cond2]

		self.phiE[cond2] = (phiDcor*self.phiNshale-phiNcor*self.phiDshale)/(self.phiNshale-self.phiDshale)

		self.phiE[self.phiE<0] = 0

		phiD = self.phiD[cond2]
		phiN = self.phiN[cond2]

		self.Vsh[cond2] = (phiN-phiD)/(self.phiNshale-self.phiDshale)

		self.Vsh[self.Vsh>1] = 1
		self.Vsh[self.Vsh<0] = 0

	def totalporosity(self):

		self.phiT = (self.phiN+self.phiD)/2

	def totalsaturation(self,Rt,a,Rw,Rsh):

		self.SwT = numpy.zeros(self.phiE.shape)

		phiim = self.phiS

		q = (self.phiD-self.phiS)/self.phiDcor

		SwE = (((a*Rw)/(phiim**2*Rt)+q**2/4)**(1/2)-q/2)/(1-q)

		self.SwE = SwE

		# Vsh = self.Vsh.copy()

		# Vsh[self.Vsh==1] = 0.999

		# # term1 = (a*Rw)/(self.phiT**2*Rt)
		# # term2 = 

		# SwT = ((a*Rw/self.phiT**2+Vsh**2/4)**(1/2)-Vsh/2)/(1-Vsh)

		# self.SwT = SwT

		# self.BWV = self.SwT*self.phiT

		# a1 = self.phiT**2/(1-Vsh)/a/Rw
		# a2 = Vsh/Rsh
		# a3 = -1/Rt

		# for index,_ in enumerate(self.phiE):
			
		# 	out = numpy.roots([a1[index],a2[index],a3[index]])

		# 	swt = max(out)

		# 	swt = 1 if swt>1 else swt

		# 	self.SwT[index] = swt

		# self.BWV = self.SwT*self.phiT

		# phiEmVsh = self.phiE**m*(1-self.Vsh)

		# cond = phiEmVsh>0

		# Vsh = self.Vsh[cond]

		# Rt = Rt[cond]

		# Swn = (1/Rt-Vsh/Rsh)*(a*Rw)/(phiEmVsh[cond])

		# Swn[Swn>1] = 1
		# Swn[Swn<0] = 0

		# self.SwT[cond] = (Swn)**(1/n)

		# self.SwT[self.SwT<0] = 0
		# self.SwT[self.SwT>1] = 1

		# term1 = (a*Rw)/(Rt*self.phiT**m)

		# term2 = Rw/RwB*(1-self.phiE/self.phiT)**2

		# self.SwT = (term1-term2)**(1/n)

	# def effectivesaturation(self):

	# 	self.SwE = numpy.zeros(self.phiE.shape)

	# 	phiT = self.phiT[self.phiE>0]
	# 	phiE = self.phiE[self.phiE>0]

	# 	SwT = self.SwT[self.phiE>0]

	# 	self.SwE[self.phiE>0] = 1-phiT/phiE*(1-SwT)

	# 	self.SwE[self.SwE<0] = 0

	@property
	def BNDWV(self):

		return self.phiT-self.phiE