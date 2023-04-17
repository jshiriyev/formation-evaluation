import numpy

class ResInit():

	def __init__(self,DWOC,DGOC,gradw=0.433,grado=0.346,gradg=0.043,peow=0,peog=0):
		"""
		DWOC 	: Depth of Water-Oil-Contact
		DGOC 	: Depth of Gas-Oil-Contact

		gradw 	: water hydrostatic gradient, psi/ft
		grado 	: oil hydrostatic gradient, psi/ft
		gradg 	: gas hydrostatic gradient, psi/ft

		peow 	: capillary entry pressure for oil-water
		peog 	: capillary entry pressure for oil-gas
		"""

		self.DWOC = DWOC
		self.DGOC = DGOC

		self.gradw = gradw
		self.grado = grado
		self.gradg = gradg

		self.peow = peow
		self.peog = peog

	def waterpressure(self,depth):
		"""pressure of water phase at input depth"""
		return self.pwwoc+self.gradw*(depth-self.DWOC)

	def oilpressure(self,depth):
		"""pressure of oleic phase at input depth"""
		return self.pwwoc+self.peow+self.grado*(depth-self.DWOC)

	def gaspressure(self,depth):
		"""pressure of gas phase at input depth"""
		return self.pogoc+self.peog+self.gradg*(depth-self.DGOC)

	@property
	def pwwoc(self):
		"""water pressure at water-oil-contact"""
		return 14.7+self.gradw*self.DWOC

	@property
	def pwgoc(self):
		"""water pressure at gas-oil-contact"""
		return self.pwwoc+(self.DGOC-self.DWOC)*self.gradw

	@property
	def powoc(self):
		"""oil pressure at water-oil-contact"""
		return self.pwwoc+self.peow
	
	@property
	def pogoc(self):
		"""oil pressure at gas-oil-contact"""
		return self.oilpressure(self.DGOC)

	@property
	def pggoc(self):
		return self.gaspressure(self.DGOC)

	@property
	def FWL(self):
		"""free-water-level"""
		return self.DWOC+self.peow/(self.gradw-self.grado)

	def Sw(self,depth,pcow):
		"""
		pcow 	: oil-water capillary pressure model
		"""

		depth = numpy.array(depth).flatten()

		Sw = numpy.ones(depth.shape)

		pw = self.waterpressure(depth[depth<self.DWOC])
		po = self.oilpressure(depth[depth<self.DWOC])

		Sw[depth<self.DWOC] = pcow.idrainage(po-pw)

		return Sw

	def saturations(self,depth,pcow,pcog=None):
		"""
		pcow 	: oil-water capillary pressure model
		pcog 	: oil-gas capillary pressure model
		"""

		depth = numpy.array(depth).flatten()

		Sw = numpy.ones(depth.shape)
		So = numpy.zeros(depth.shape)

		pw = self.waterpressure(depth[depth<self.DWOC])
		po = self.oilpressure(depth[depth<self.DWOC])

		Sw[depth<self.DWOC] = pcow.idrainage(po-pw)

		So[depth<self.DWOC] = 1-Sw[depth<self.DWOC]

		if pcog is None:
			return Sw,So

		Sg = numpy.zeros(depth.shape)

		pl = self.oilpressure(depth[depth<self.DGOC])
		pg = self.gaspressure(depth[depth<self.DGOC])

		Sg[depth<self.DGOC] = pcog.idrainage(pg-pl)

		Sl = pcog.idrainage(pg-pl)

		So[depth<self.DGOC] = Sl-Sw[depth<self.DGOC]

		return Sw,So,Sg

	def Sg(self,depth,pcog):
		"""
		pcog 	: oil-gas capillary pressure model
		"""

		depth = numpy.array(depth).flatten()

		Sg = numpy.zeros(depth.shape)

		pl = self.oilpressure(depth[depth<self.DGOC])
		pg = self.gaspressure(depth[depth<self.DGOC])

		Sg[depth<self.DGOC] = pcog.idrainage(pg-pl)

		return Sg