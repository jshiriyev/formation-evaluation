import numpy

class Decluster():

	def __init__(self,xmin,xmax,ymin,ymax):
		"""Initializes the exterior boundaries of data."""
		self.xmin = xmin
		self.xmax = xmax
		self.ymin = ymin
		self.ymax = ymax

	def nodes(self,nx,ny):
		"""Returns 1D array for x and y axis grid nodes (boundaries)."""
		xnodes = numpy.linspace(self.xmin,self.xmax,nx+1)
		ynodes = numpy.linspace(self.ymin,self.ymax,ny+1)
		return xnodes,ynodes

	def centers(self,nx,ny):
		"""Returns 1D array for x and y axis of grid centers."""
		xdelta = (self.xmax-self.xmin)/nx
		ydelta = (self.ymax-self.ymin)/ny

		xcenters = numpy.arange(self.xmin+xdelta/2,self.xmax,xdelta)
		ycenters = numpy.arange(self.ymin+ydelta/2,self.ymax,ydelta)
		return xcenters,ycenters

	def deltas(self,nx,ny):
		"""Returns the size of grid in x and y directions."""
		xdelta = (self.xmax-self.xmin)/nx
		ydelta = (self.ymax-self.ymin)/ny
		return xdelta,ydelta

	def size(self,nx,ny):
		"""Returns the area of grid."""
		xdelta,ydelta = self.deltas(nx,ny)
		return xdelta*ydelta

	def mean(self,nx,ny,X,Y,Z,returnFlag=False):
		"""if returnFlag is True, the number of empty cells are returned too.

		X 	: X-axis values of the data, flat array is expected
		Y 	: Y-axis values of the data, flat array is expected
		Z 	: Property values of the data, flat array is expected
		"""
		clusterMean = numpy.zeros((nx,ny))

		xnodes,ynodes = self.nodes(nx,ny)

		emptyClusterCount = 0

		for i in range(nx):

			for j in range(ny):

				Xcond = numpy.logical_and(X>xnodes[i],xnodes[i+1]>X)
				Ycond = numpy.logical_and(Y>ynodes[j],ynodes[j+1]>Y)
				Scond = numpy.logical_and(Xcond,Ycond)

				if Z[Scond].size==0:
					clusterMean[j,i] = numpy.nan
					emptyClusterCount += 1
				else:
					clusterMean[j,i] = Z[Scond].mean()

		if returnFlag:
			return clusterMean,emptyClusterCount

		return clusterMean