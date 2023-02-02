from borepy.scomp.array._curve import Curve

def pop(kwargs,key,default=None):

    try:
        return kwargs.pop(key)
    except KeyError:
        return default

class LasCurve(Curve):
    """The major difference between Column and LasCurve is the depth attribute
    of LasCurve."""

    def __init__(self,**kwargs):
        """Initialization of LasCurve."""

        super().__init__(
            vals = pop(kwargs,"vals"),
            head = pop(kwargs,"head"),
            unit = pop(kwargs,"unit"),
            info = pop(kwargs,"info"),
            size = pop(kwargs,"size"),
            dtype = pop(kwargs,"dtype"))

        depth = kwargs.pop("depth")

        if not isinstance(depth,column):
            depth = column(
                vals = depth,
                head = "DEPT",
                unit = pop(kwargs,"dunit","m"),
                info = "")

        self.depth = depth

        if self.depth.size != self.vals.size:
            raise f"depth.size and vals.size does not match!"

        self.setattrs(**kwargs)

    def setattrs(self,**kwargs):

        for key,value in kwargs.items():
            setattr(self,key,value)

    @property
    def height(self):

        depth = self.depth

        total = depth.max()-depth.min()

        node_head = numpy.roll(depth,1)
        node_foot = numpy.roll(depth,-1)

        thickness = (node_foot-node_head)/2

        thickness[ 0] = (depth[ 1].vals[0]-depth[ 0].vals[0])/2
        thickness[-1] = (depth[-1].vals[0]-depth[-2].vals[0])/2

        null = numpy.sum(thickness[self.isnone])

        return {'total': total, 'null': null, 'valid': total-null,}