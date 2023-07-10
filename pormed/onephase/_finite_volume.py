import numpy

class cells():

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
	def unormal1(self):
		v1 = self.r4-self.r1
		v2 = self.r2-self.r1
		v3 = numpy.cross(v1,v2)
		return v3/numpy.linalg.norm(v3,2,axis=1)

	@property
	def unormal2(self):
		v1 = self.r2-self.r1
		v2 = self.r5-self.r1
		v3 = numpy.cross(v1,v2)
		return v3/numpy.linalg.norm(v3,2,axis=1)

	@property
	def unormal3(self):
		v1 = self.r3-self.r2
		v2 = self.r6-self.r2
		v3 = numpy.cross(v1,v2)
		return v3/numpy.linalg.norm(v3,2,axis=1)

	@property
	def unormal4(self):
		v1 = self.r8-self.r4
		v2 = self.r3-self.r4
		v3 = numpy.cross(v1,v2)
		return v3/numpy.linalg.norm(v3,2,axis=1)

	@property
	def unormal5(self):
		v1 = self.r5-self.r1
		v2 = self.r4-self.r1
		v3 = numpy.cross(v1,v2)
		return v3/numpy.linalg.norm(v3,2,axis=1)

	@property
	def unormal6(self):
		v1 = self.r6-self.r5
		v2 = self.r8-self.r5
		v3 = numpy.cross(v1,v2)
		return v3/numpy.linalg.norm(v3,2,axis=1)

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
	def center(self):

		return 1/8*(
			self.r1+self.r2+self.r3+self.r4+
			self.r5+self.r6+self.r7+self.r8)

	@property
	def area1(self):
		return 100

	@property
	def area2(self):
		return 100

	@property
	def area3(self):
		return 100

	@property
	def area4(self):
		return 100

	@property
	def area5(self):
		return 100

	@property
	def area6(self):
		return 100
	
	@property
	def volume(self):

		center = self.center

		v1 = numpy.sum((self.center1-center)*self.unormal1,axis=1)*self.area1
		v2 = numpy.sum((self.center2-center)*self.unormal2,axis=1)*self.area2
		v3 = numpy.sum((self.center3-center)*self.unormal3,axis=1)*self.area3
		v4 = numpy.sum((self.center4-center)*self.unormal4,axis=1)*self.area4
		v5 = numpy.sum((self.center5-center)*self.unormal5,axis=1)*self.area5
		v6 = numpy.sum((self.center6-center)*self.unormal6,axis=1)*self.area6

		return 1/3*(v1+v2+v3+v4+v5+v6)

if __name__ == "__main__":

	cell = cells(
		((-5,-5,5),),
		((5,-5,5),),
		((5,-5,-5),),
		((-5,-5,-5),),
		((-5,5,5),),
		((5,5,5),),
		((5,5,-5),),
		((-5,5,-5),),
	)

	# print(cell.unormal1)

	# print(cell.center)

	# print(cell.center1)
	# print(cell.center2)
	# print(cell.center3)
	# print(cell.center4)
	# print(cell.center5)
	# print(cell.center6)

	print(cell.volume)