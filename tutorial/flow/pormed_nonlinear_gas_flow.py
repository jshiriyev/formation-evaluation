import numpy as np

from borepy.pormed import OnePhase

class Grids():

	def __init__(self,length,numtot,csa):

		self.length = length

		self.numtot = numtot

		self.csa = csa

		self.num = (numtot,1,1)

		self._index()

		self._size()

		self._area()

	def _index(self):

		idx = np.arange(self.numtot)

		self.index = np.tile(idx,(7,1)).T

		self.index[idx.reshape(-1,self.num[0])[:,1:].ravel(),1] -= 1
		self.index[idx.reshape(-1,self.num[0])[:,:-1].ravel(),2] += 1
		self.index[idx.reshape(self.num[2],-1)[:,self.num[0]:],3] -= self.num[0]
		self.index[idx.reshape(self.num[2],-1)[:,:-self.num[0]],4] += self.num[0]
		self.index[idx.reshape(self.num[2],-1)[1:,:],5] -= self.num[0]*self.num[1]
		self.index[idx.reshape(self.num[2],-1)[:-1,:],6] += self.num[0]*self.num[1]

	def _size(self):

		self.size = np.zeros((self.numtot,3))

		self.size[:,0] = self.length/self.num[0]
		self.size[:,1] = self.csa
		self.size[:,2] = 1

	def _area(self):

		self.area = np.zeros((self.numtot,3))

		self.area[:,0] = self.size[:,1]*self.size[:,2]
		self.area[:,1] = self.size[:,2]*self.size[:,0]
		self.area[:,2] = self.size[:,0]*self.size[:,1]

	def set_permeability(self,permeability,homogeneous=True,isotropic=True):

		self.permeability = np.zeros((self.numtot,3))

		if homogeneous and isotropic:
			
			self.permeability[:] = permeability

		elif homogeneous and not isotropic:

			self.permeability[:] = permeability

		elif not homogeneous and isotropic:

			self.permeability[:,0] = permeability
			self.permeability[:,1] = permeability
			self.permeability[:,2] = permeability

		else:

			self.permeability[:] = permeability

Pu = 200
Pd = 14.7

Nt = 3

dt = 1e-5

grids = Grids(length=1,numtot=4,csa=0.02)

grids.porosity = 0.2
grids.viscosity = 0.01

grids.pressure_initial = np.ones((grids.numtot,1))*14.7

grids.set_permeability(permeability=50,homogeneous=True,isotropic=True)

Tim = OnePhase.transmissibility(grids)

print(grids.size)

print(Tim)

# P = np.ones((grids.numtot,1))*14.7

# Ti = (1.06235016e-14/1.4503774389728e-7*60*60*24)*grids.permeability*grids.csa/grids.viscosity/(grids.length/grids.numtot)

# T = np.zeros((grids.numtot,grids.numtot))
# J = np.zeros((grids.numtot,grids.numtot))
# Q = np.zeros((grids.numtot,1))

# for i in range(grids.numtot):

# 	if i==0:
# 		J[i,i] = 2*Ti
# 		Q[i,0] = Pu*2*Ti
# 	else:
# 		T[i,i-1] = -Ti
# 		T[i,i] += Ti

# 	if i<4-1:
# 		T[i,i+1] = -Ti
# 		T[i,i] += Ti
# 	else:
# 		J[i,i] = 2*Ti
# 		Q[i,0] = Pd*2*Ti


# for j in range(Nt):

# 	Pk = P.copy()

# 	error = 1000

# 	k = 1

# 	while error>1e-6:

# 		A = np.eye(grids.numtot)*100/Pk

# 		D = T+J+A

# 		V = np.matmul(A,P)+Q

# 		F = -np.matmul(D,Pk)+V

# 		error = np.linalg.norm(F,2)

# 		Pk = np.linalg.solve(D,V)

# 		# print("\n\n")

# 		# print(f"iteration #{k}: {error=}")

# 		# print("\n",Pk)

# 		k += 1

# 	P = Pk.copy()


