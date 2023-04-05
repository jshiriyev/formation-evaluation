from matplotlib import pyplot

import numpy

class Cuboid():

    """
    For rectangular parallelepiped, dimensions is a tuple
    with three entries for sizes in x,y,z direction.
    """

    def __init__(self,lengths,**kwargs):

        super().__init__(**kwargs)

        self.lengths = lengths

        self.edge_vertices = numpy.zeros((8,3))

        self.edge_vertices[0,:] = (0,0,0)
        self.edge_vertices[1,:] = (self.lengths[0],0,0)
        self.edge_vertices[2,:] = (self.lengths[0],self.lengths[1],0)
        self.edge_vertices[3,:] = (0,self.lengths[1],0)

        self.edge_vertices[4,:] = (0,0,self.lengths[2])
        self.edge_vertices[5,:] = (self.lengths[0],0,self.lengths[2])
        self.edge_vertices[6,:] = (self.lengths[0],self.lengths[1],self.lengths[2])
        self.edge_vertices[7,:] = (0,self.lengths[1],self.lengths[2])

        indices = numpy.empty((12,2),dtype=int)

        indices[:,0] = (0,1,2,3,0,1,2,3,4,5,6,7)
        indices[:,1] = (1,2,3,0,4,5,6,7,5,6,7,4)
        
        x_aspects = self.edge_vertices[:,0][indices]
        y_aspects = self.edge_vertices[:,1][indices]
        z_aspects = self.edge_vertices[:,2][indices]

        self.boundaries = []

        for x_aspect,y_aspect,z_aspect in zip(x_aspects,y_aspects,z_aspects):
            self.boundaries.append(numpy.array([x_aspect,y_aspect,z_aspect]))

        self.gridFlag = False

    def grid(self,grid_num):

        """
        self.grid_num        : number of grids in x, y, z directions
        self.grid_numtot     : number of totla grids 
        self.grid_indices    : connectivity map containing index of all grids and their neighbours.
        self.grid_sizes      : size of grids in all directions.
        self.grid_areas      : area of all faces
        self.grid_volumes    : volume of grids
        self.grid_centers    : coordinates of the center of grids
        """
        
        self.grid_num = grid_num

        self.grid_numtot = numpy.prod(self.grid_num)

        idx = numpy.arange(self.grid_numtot)
        
        self.grid_indices = numpy.tile(idx,(7,1)).T

        self.grid_indices[idx.reshape(-1,self.grid_num[0])[:,1:].ravel(),1] -= 1
        self.grid_indices[idx.reshape(-1,self.grid_num[0])[:,:-1].ravel(),2] += 1
        self.grid_indices[idx.reshape(self.grid_num[2],-1)[:,self.grid_num[0]:],3] -= self.grid_num[0]
        self.grid_indices[idx.reshape(self.grid_num[2],-1)[:,:-self.grid_num[0]],4] += self.grid_num[0]
        self.grid_indices[idx.reshape(self.grid_num[2],-1)[1:,:],5] -= self.grid_num[0]*self.grid_num[1]
        self.grid_indices[idx.reshape(self.grid_num[2],-1)[:-1,:],6] += self.grid_num[0]*self.grid_num[1]

        self.grid_hasxmin = ~(self.grid_indices[:,0]==self.grid_indices[:,1])
        self.grid_hasxmax = ~(self.grid_indices[:,0]==self.grid_indices[:,2])
        self.grid_hasymin = ~(self.grid_indices[:,0]==self.grid_indices[:,3])
        self.grid_hasymax = ~(self.grid_indices[:,0]==self.grid_indices[:,4])
        self.grid_haszmin = ~(self.grid_indices[:,0]==self.grid_indices[:,5])
        self.grid_haszmax = ~(self.grid_indices[:,0]==self.grid_indices[:,6])

        self.grid_xnodes = numpy.linspace(0,self.lengths[0],self.grid_num[0]+1)
        self.grid_ynodes = numpy.linspace(0,self.lengths[1],self.grid_num[1]+1)
        self.grid_znodes = numpy.linspace(0,self.lengths[2],self.grid_num[2]+1)
        
        xsize = self.grid_xnodes[1:]-self.grid_xnodes[:-1]
        ysize = self.grid_ynodes[1:]-self.grid_ynodes[:-1]
        zsize = self.grid_znodes[1:]-self.grid_znodes[:-1]
        
        self.grid_sizes = numpy.zeros((self.grid_numtot,3))
        self.grid_sizes[:,0] = numpy.tile(xsize,self.grid_num[1]*self.grid_num[2])
        self.grid_sizes[:,1] = numpy.tile(ysize.repeat(self.grid_num[0]),self.grid_num[2])
        self.grid_sizes[:,2] = zsize.repeat(self.grid_num[0]*self.grid_num[1])

        self.grid_areas = numpy.zeros((self.grid_numtot,3))
        self.grid_areas[:,0] = self.grid_sizes[:,1]*self.grid_sizes[:,2]
        self.grid_areas[:,1] = self.grid_sizes[:,2]*self.grid_sizes[:,0]
        self.grid_areas[:,2] = self.grid_sizes[:,0]*self.grid_sizes[:,1]

        self.grid_volumes = numpy.prod(self.grid_sizes,axis=1)

        xcenter = self.grid_xnodes[:-1]+xsize/2
        ycenter = self.grid_ynodes[:-1]+ysize/2
        zcenter = self.grid_znodes[:-1]+zsize/2
        
        self.grid_centers = numpy.zeros((self.grid_numtot,3))
        self.grid_centers[:,0] = numpy.tile(xcenter,self.grid_num[1]*self.grid_num[2])
        self.grid_centers[:,1] = numpy.tile(ycenter.repeat(self.grid_num[0]),self.grid_num[2])
        self.grid_centers[:,2] = zcenter.repeat(self.grid_num[0]*self.grid_num[1])

        self.gridFlag = True

    def plot(self):

        pass

class OneDimCuboid():

    def __init__(self,length,numtot,csa):

        self.length = length

        self.numtot = numtot

        self.csa = csa

        self.num = (numtot,1,1)

        self._index()

        self._size()

        self._area()

    def _index(self):

        idx = numpy.arange(self.numtot)

        self.index = numpy.tile(idx,(7,1)).T

        self.index[idx.reshape(-1,self.num[0])[:,1:].ravel(),1] -= 1
        self.index[idx.reshape(-1,self.num[0])[:,:-1].ravel(),2] += 1
        self.index[idx.reshape(self.num[2],-1)[:,self.num[0]:],3] -= self.num[0]
        self.index[idx.reshape(self.num[2],-1)[:,:-self.num[0]],4] += self.num[0]
        self.index[idx.reshape(self.num[2],-1)[1:,:],5] -= self.num[0]*self.num[1]
        self.index[idx.reshape(self.num[2],-1)[:-1,:],6] += self.num[0]*self.num[1]

    def _size(self):

        self.size = numpy.zeros((self.numtot,3))

        self.size[:,0] = self.length/self.num[0]
        self.size[:,1] = self.csa
        self.size[:,2] = 1

        self.xaxis = numpy.linspace(0,self.length,self.numtot,endpoint=False)+self.size[:,0]/2

    def _area(self):

        self.area = numpy.zeros((self.numtot,6))

        self.area[:,0] = self.size[:,1]*self.size[:,2]
        self.area[:,1] = self.size[:,1]*self.size[:,2]
        self.area[:,2] = self.size[:,2]*self.size[:,0]
        self.area[:,3] = self.size[:,2]*self.size[:,0]
        self.area[:,4] = self.size[:,0]*self.size[:,1]
        self.area[:,5] = self.size[:,0]*self.size[:,1]

    def set_permeability(self,permeability,homogeneous=True,isotropic=True):

        self.permeability = numpy.zeros((self.numtot,3))

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

class RectRectGrid():
    """It is a 2D object in 3D space."""

    def __init__(self,length=1,width=1,height=1,centroid=None):
        """Initialization of rectangle in 3D domain.
        If centroid is not defined, left-bottom vertex will be assigned to (0,0) point."""

        super().__setattr__('length',length)
        super().__setattr__('width',width)
        super().__setattr__('height',height)

        if centroid is None:
            centroid = (length/2,width/2)

        super().__setattr__('centroid',numpy.array(centroid))

        self._vertices()

    def _vertices(self):

        vertices = numpy.zeros((4,2),dtype='float64')

        vertices[0,:] = self.centroid+(-self.length/2,-self.width/2)
        vertices[1,:] = self.centroid+(-self.length/2,+self.width/2)
        vertices[2,:] = self.centroid+(+self.length/2,+self.width/2)
        vertices[3,:] = self.centroid+(+self.length/2,-self.width/2)

        super().__setattr__('vertices',vertices)

        indices = numpy.array((0,1,2,3,0),dtype='int32')

        super().__setattr__('indices',indices)

    def mesh(self,number,**kwargs):

        self._initialize(number)

        xdelta = kwargs.get('xdelta')
        ydelta = kwargs.get('ydelta')
        zdelta = kwargs.get('zdelta')

        self._delta(xdelta,ydelta,zdelta)

        self._center()

        self._area()

        self._volume()

    def _initialize(self,number):
        """It initializes grids:

        number: must be a tuple or list (number of x grids, number of y grids)"""

        super().__setattr__('number',number)

        super().__setattr__('count',numpy.prod(self.number))

        self._cmap()

        hasxmin = ~(self.cmap[:,0]==self.cmap[:,1])
        hasxmax = ~(self.cmap[:,0]==self.cmap[:,2])

        hasymin = ~(self.cmap[:,0]==self.cmap[:,3])
        hasymax = ~(self.cmap[:,0]==self.cmap[:,4])

        super().__setattr__('hasxmin',hasxmin)
        super().__setattr__('hasxmax',hasxmax)
        super().__setattr__('hasymin',hasymin)
        super().__setattr__('hasymax',hasymax)

    def _cmap(self):

        indices = numpy.arange(self.count)
        
        cmap = numpy.tile(indices,(5,1)).T

        cmap[indices.reshape(-1,self.xnumber)[:,1:].ravel(),1] -= 1
        cmap[indices.reshape(-1,self.xnumber)[:,:-1].ravel(),2] += 1

        cmap[indices.reshape(1,-1)[:,self.xnumber:],3] -= self.xnumber
        cmap[indices.reshape(1,-1)[:,:-self.xnumber],4] += self.xnumber

        super().__setattr__('cmap',cmap)

    def _delta(self,xdelta=None,ydelta=None,zdelta=None):

        if xdelta is None:
            xdelta = self.length/self.xnumber

        if ydelta is None:
            ydelta = self.width/self.ynumber

        if zdelta is None:
            zdelta = self.height

        delta = numpy.zeros((self.count,3),dtype='float64')

        xdelta = numpy.array(xdelta).flatten()
        ydelta = numpy.array(ydelta).flatten()

        if xdelta.size == 1:
            delta[:,0] = xdelta
        elif xdelta.size == self.xnumber:
            delta[:,0] = numpy.tile(xdelta,self.ynumber)
        else:
            raise ValueError

        if ydelta.size == 1:
            delta[:,1] = ydelta
        elif ydelta.size == self.ynumber:
            delta[:,1] = ydelta.repeat(self.xnumber)
        else:
            raise ValueError

        delta[:,2] = zdelta
        
        super().__setattr__('delta',delta)

    def _center(self):

        xdelta = self.xdelta[:self.xnumber]
        ydelta = self.ydelta[::self.xnumber]

        xcenter = numpy.cumsum(xdelta)-xdelta/2
        ycenter = numpy.cumsum(ydelta)-ydelta/2

        zcenter = self.height/2

        center = numpy.zeros((self.count,3),dtype='float64')

        xcenter = numpy.array(xcenter).flatten()
        ycenter = numpy.array(ycenter).flatten()

        if xcenter.size==1:
            center[:,0] = xcenter
        elif xcenter.size==self.xnumber:
            center[:,0] = numpy.tile(xcenter,self.ynumber)
        else:
            raise ValueError("xcenter")

        if ycenter.size==1:
            center[:,1] = ycenter
        elif ycenter.size == self.ynumber:
            center[:,1] = ycenter.repeat(self.xnumber)
        else:
            raise ValueError("ycenter")

        center[:,2] = zcenter

        super().__setattr__('center',center)

    def _area(self):

        area = numpy.zeros((self.count,3))

        area[:,0] = self.zdelta*self.ydelta
        area[:,1] = self.xdelta*self.zdelta
        area[:,2] = self.ydelta*self.xdelta

        super().__setattr__('area',area)

    def _volume(self):

        volume = numpy.prod(self.delta,axis=1)

        super().__setattr__('volume',volume)

    def view(self,axis=None,vertices=True,bounds=True,edges=True,centers=True):

        show = True if axis is None else False

        if axis is None:
            axis = pyplot.figure().add_subplot()

        if vertices:
            axis.scatter(*self.vertices.T)

        if bounds:
            axis.plot(*self.vertices[self.indices].T,color='grey')

        if edges:
            xdelta = self.xdelta[:self.xnumber]
            ydelta = self.ydelta[::self.xnumber]
            
            xinner = numpy.cumsum(xdelta)[:-1]
            yinner = numpy.cumsum(ydelta)[:-1]

            axis.vlines(x=xinner,ymin=0,ymax=self.width,linestyle="--")
            axis.hlines(y=yinner,xmin=0,xmax=self.length,linestyle="--")

        if centers:
            axis.scatter(*self.center.T[:2,:])

        axis.set_box_aspect(self.width/self.length)

        if show:
            pyplot.show()

    def __setattr__(self,key,value):

        raise AttributeError(f'RectGrid does not have attribute {key}')

    @property
    def xnumber(self):

        return self.number[0]

    @property
    def ynumber(self):

        return self.number[1]

    @property
    def znumber(self):

        return 1
    
    @property
    def xcenter(self):

        return self.center[:,0]

    @property
    def ycenter(self):

        return self.center[:,1]

    @property
    def zcenter(self):

        return self.center[:,2]

    @property
    def xdelta(self):

        return self.delta[:,0]

    @property
    def ydelta(self):

        return self.delta[:,1]

    @property
    def zdelta(self):

        return self.delta[:,2]
    