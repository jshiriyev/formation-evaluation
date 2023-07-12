import numpy

class CornerPoint():

	def __init__(self,grdecl):

		self.SPECGRID = grdecl['SPECGRID']

		self.COORD = grdecl['COORD']
		self.ZCORN = grdecl['ZCORN']

	@property
	def dimensions(self):

		return tuple([int(x) for x in self.SPECGRID[0].split()[:3]])

	@property
	def zcorn(self):

		Nx,Ny,Nz = self.dimensions

		indices = numpy.zeros((Nx*Ny,8),dtype=int)

		column0 = numpy.arange(Nx*2,step=2,dtype=int)

		column0 = numpy.tile(column0,Ny)

		indices[:,0] = column0+numpy.arange(Ny,dtype=int).repeat(Nx)*Nx*4
		indices[:,1] = indices[:,0]+1
		indices[:,2] = indices[:,0]+Nx*2
		indices[:,3] = indices[:,2]+1
		indices[:,4] = indices[:,0]+Nx*Ny*4
		indices[:,5] = indices[:,4]+1
		indices[:,6] = indices[:,2]+Nx*Ny*4
		indices[:,7] = indices[:,6]+1

		indices = numpy.tile(indices,(Nz,1))

		kvalues = numpy.arange(Nz,dtype=int).repeat(Nx*Ny)*Nx*Ny*8

		indices += kvalues.reshape((-1,1))

		return self.ZCORN[indices]

class HexaHedron():

	def __init__(self,r1,r2,r3,r4,r5,r6,r7,r8):

		self.r1 = numpy.array(r1)
		self.r2 = numpy.array(r2)
		self.r3 = numpy.array(r3)
		self.r4 = numpy.array(r4)
		self.r5 = numpy.array(r5)
		self.r6 = numpy.array(r6)
		self.r7 = numpy.array(r7)
		self.r8 = numpy.array(r8)

	@property
	def normal1(self):
		v1 = self.r4-self.r1
		v2 = self.r2-self.r1
		return numpy.cross(v1,v2)

	@property
	def normal2(self):
		v1 = self.r2-self.r1
		v2 = self.r5-self.r1
		return numpy.cross(v1,v2)

	@property
	def normal3(self):
		v1 = self.r3-self.r2
		v2 = self.r6-self.r2
		return numpy.cross(v1,v2)

	@property
	def normal4(self):
		v1 = self.r8-self.r4
		v2 = self.r3-self.r4
		return numpy.cross(v1,v2)

	@property
	def normal5(self):
		v1 = self.r5-self.r1
		v2 = self.r4-self.r1
		return numpy.cross(v1,v2)

	@property
	def normal6(self):
		v1 = self.r6-self.r5
		v2 = self.r8-self.r5
		return numpy.cross(v1,v2)

	def unormal(self,face):

		normal = getattr(self,f"normal{face}")

		magnitude = numpy.linalg.norm(normal,2,axis=1)

		return normal/magnitude.reshape((-1,1))

	@property
	def center(self):

		return 1/8*(
			self.r1+self.r2+self.r3+self.r4+
			self.r5+self.r6+self.r7+self.r8)

	@property
	def center1(self):
		return 1/4*(self.r1+self.r2+self.r3+self.r4)

	@property
	def center2(self):
		return 1/4*(self.r1+self.r2+self.r5+self.r6)

	@property
	def center3(self):
		return 1/4*(self.r2+self.r3+self.r6+self.r7)

	@property
	def center4(self):
		return 1/4*(self.r3+self.r4+self.r7+self.r8)

	@property
	def center5(self):
		return 1/4*(self.r1+self.r4+self.r5+self.r8)

	@property
	def center6(self):
		return 1/4*(self.r5+self.r6+self.r7+self.r8)

	@property
	def area1(self):
		
		A1 = self.areaTriangle(self.r1,self.r4,self.r2)
		A2 = self.areaTriangle(self.r3,self.r2,self.r4)
		
		return A1+A2

	@property
	def area2(self):

		A1 = self.areaTriangle(self.r1,self.r2,self.r5)
		A2 = self.areaTriangle(self.r6,self.r5,self.r2)
		
		return A1+A2

	@property
	def area3(self):

		A1 = self.areaTriangle(self.r2,self.r3,self.r6)
		A2 = self.areaTriangle(self.r7,self.r6,self.r3)
		
		return A1+A2

	@property
	def area4(self):
		
		A1 = self.areaTriangle(self.r4,self.r8,self.r3)
		A2 = self.areaTriangle(self.r7,self.r3,self.r8)
		
		return A1+A2

	@property
	def area5(self):
		
		A1 = self.areaTriangle(self.r4,self.r1,self.r8)
		A2 = self.areaTriangle(self.r5,self.r8,self.r1)
		
		return A1+A2

	@property
	def area6(self):
		
		A1 = self.areaTriangle(self.r5,self.r6,self.r8)
		A2 = self.areaTriangle(self.r7,self.r8,self.r6)
		
		return A1+A2
	
	@property
	def volume(self):

		center = self.center

		v1 = numpy.sum((self.center1-center)*self.unormal(1),axis=1)*self.area1
		v2 = numpy.sum((self.center2-center)*self.unormal(2),axis=1)*self.area2
		v3 = numpy.sum((self.center3-center)*self.unormal(3),axis=1)*self.area3
		v4 = numpy.sum((self.center4-center)*self.unormal(4),axis=1)*self.area4
		v5 = numpy.sum((self.center5-center)*self.unormal(5),axis=1)*self.area5
		v6 = numpy.sum((self.center6-center)*self.unormal(6),axis=1)*self.area6

		return 1/3*(v1+v2+v3+v4+v5+v6)

	@staticmethod
	def areaTriangle(r1,r2,r3):

		AB,AC = r2-r1,r3-r1

		ABmag = numpy.linalg.norm(AB,2,axis=1)
		ACmag = numpy.linalg.norm(AC,2,axis=1)

		cos_theta = numpy.sum(AB*AC,axis=1)/(ABmag*ACmag)

		sin_theta = numpy.sqrt(1-cos_theta**2)

		return 1/2*ABmag*ACmag*sin_theta

if __name__ == "__main__":

	cells = Hexahedron(
		((-5,-5,5),(5,-5,5)),
		((5,-5,5),(15,-5,5)),
		((5,-5,-5),(15,-5,-5)),
		((-5,-5,-5),(5,-5,-5)),
		((-5,5,5),(5,5,5)),
		((5,5,5),(15,5,5)),
		((5,5,-5),(15,5,-5)),
		((-5,5,-5),(5,5,-5)),
	)

	# print(cells.unormal1)

	# print(cells.center)

	# print(cells.center1)
	# print(cells.center2)
	# print(cells.center3)
	# print(cells.center4)
	# print(cells.center5)
	# print(cells.center6)

	print(cells.volume)