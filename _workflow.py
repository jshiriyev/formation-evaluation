from . import cores
from . import wlogs

class WorkFlow():

    def __init__(self,lasfile=None,**kwargs):

        if lasfile is None:
            self.lasfile = LasFile(**kwargs)
        elif isinstance(lasfile,str):
            self.lasfile = loadlas(lasfile,**kwargs)
        elif isinstance(lasfile,LasFile):
            self.lasfile = lasfile

    def set_bwv(self,PHI,SW):

        porosity = self[PHI].vals

        saturation = self[SW].vals

        BWV = porosity*saturation

        depth = self.lasfile.depth

        info = 'Bulk water volume.'

        self.add_curve(vals=BWV,depth=depth,head='BWV',unit='-',info=info)

    def __getattr__(self,key):

        return getattr(self.lasfile,key)

    def __setitem__(self,head,curve):

        self.lasfile[head] = curve

    def __getitem__(self,head):

        return self.lasfile[head]

    def __call__(self,**kwargs):
        """It is calling the interpretation method for the specified curve(s)."""

        if len(kwargs) != 1:
            raise "Number of optional arguments must be one specifying method and head dictionary."

        method,heads = kwargs.popitem()

        if not isinstance(heads,dict):
            raise "Heads must be dictionary!"

        curves = {}

        for head,curve in heads.items():
            curves[head] = self[curve]

        if method is None:
            return
        elif method.lower() == "sonic":
            return sonic(**curves)
        elif method.lower() == "spotential":
            return spotential(**curves)
        elif method.lower() == "laterolog":
            return laterolog(**curves)
        elif method.lower() == "induction":
            return induction(**curves)
        elif method.lower() == "gammaray":
            return gammaray(**curves)
        elif method.lower() == "density":
            return density(**curves)
        elif method.lower() == "neutron":
            return neutron(**curves)
        elif method.lower() == "nmr":
            return nmr(**curves)
        elif method.lower() == "density-neutron":
            return denneu(**curves)
        elif method.lower() == "sonic-density":
            return sonden(**curves)
        elif method.lower() == "sonic-neutron":
            return sonneu(**curves)
        elif method.lower() == "mn-plot":
            return mnplot(**curves)
        elif method.lower() == "mid-plot":
            return midplot(**curves)
        elif method.lower() == "rhomaa-umaa":
            return rhoumaa(**curves)
        elif method.lower() == "pickett":
            return pickett(**curves)
        elif method.lower() == "hingle":
            return hingle(**curves)

    @staticmethod
    def archie(m=2,a=1,Rw=0.01,n=2):

        archie = {}

        archie["m"] = m
        archie["a"] = a
        archie["Rw"] = Rw
        archie["n"] = n

        return archie
