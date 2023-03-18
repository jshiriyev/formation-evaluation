import numpy

from ._linear import linear

class udist():
    """Data uniformly distributed in one dimensional space."""

    def __init__(self,vals,start=0,stop=None,step=1.0,null=None,unit=None,ptype=None):
        """Initialization of uniformly distributed data."""

        self.array = linear.array(
            vals,null=null,unit=unit,ptype=ptype)

        self.start,self.step = start,step

        if stop is None:
            
            self.stop = (self.array.size-1)*self.step+self.start
            
            return

        self.stop = stop

        if (self.stop-self.start)/self.step+1 != self.array.size:
            raise f"depth.size and vals.size does not match!"

    @property
    def depth(self):

        return numpy.linspace(self.start,self.stop,self.array.size)
    

    @property
    def height(self):

        depth = self.depth

        total = depth.max()-depth.min()

        node_head = numpy.roll(depth,1)
        node_foot = numpy.roll(depth,-1)

        thickness = (node_foot-node_head)/2

        thickness[ 0] = (depth[ 1]-depth[ 0])/2
        thickness[-1] = (depth[-1]-depth[-2])/2

        null = numpy.sum(thickness[self.array.isnull])

        return {'total': total, 'null': null, 'valid': total-null,}