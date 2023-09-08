import numpy

class gammaray():

    def __init__(self,values,depths=None,grmin=None,grmax=None):
        """Initializes gamma-ray values and depths for shale volume calculations.
        If depths values are provided, they must be the same size as values."""
        self.values = values
        self.depths = depths

        self.grmin = numpy.nanmin(values) if grmin is None else grmin
        self.grmax = numpy.nanmax(values) if grmax is None else grmax

    def value2index(self,value):
        """Calculates shale index based on the gamma-ray values."""
        return (value-self.grmin)/(self.grmax-self.grmin)

    def index2value(self,index):
        """Calculates gamma-ray values based on the shale index."""
        return index*(self.grmax-self.grmin)+self.grmin

    def shalevolume(self,model="linear",factor=None):
        """Calculates shale volume based on gamma ray values and selected model."""
        return getattr(self,f"{model}")(self.value2index(self.values),factor=factor)

    def cut(self,percent=40,model="linear",factor=None):
        """Calculates gamma ray values based on the given volume percent and model."""
        return self.index2value(getattr(self,f"{model}")(None,volume=percent/100,factor=factor))

    def netthickness(self,**kwargs):
        """Calculates net-thickness where gamma-ray values are less than cut values.
        Cut values are calculated based on given percent and model."""

        node_above = numpy.roll(self.depths,1)
        node_below = numpy.roll(self.depths,-1)

        thickness = (node_below-node_above)/2

        thickness[0] = (self.depths[1]-self.depths[0])/2
        thickness[-1] = (self.depths[-1]-self.depths[-2])/2

        return numpy.sum(thickness[self.values<self.cut(**kwargs)])

    def netgrossratio(self,**kwargs):
        """Calculates net-to-gross-ratio based on given percent and model."""
        return self.netthickness(**kwargs)/self.height

    @property
    def height(self):
        """Calculates the total height of gamma ray logged section."""
        return max(self.depths)-min(self.depths)

    @property
    def vsh(self):
        return self.shalevolume

    @staticmethod
    def linear(index,volume=None,**kwargs):
        if volume is None:
            return index
        elif index is None:
            return volume

    @staticmethod
    def larionov_oldrocks(index,volume=None,**kwargs):
        if volume is None:
            return 0.33*(2**(2*index)-1)
        elif index is None:
            return numpy.log2(volume/0.33+1)/2

    @staticmethod
    def clavier(index,volume=None,**kwargs):
        if volume is None:
            return 1.7-numpy.sqrt(3.38-(0.7+index)**2)
        elif index is None:
            return numpy.sqrt(3.38-(1.7-volume)**2)-0.7

    @staticmethod
    def bateman(index,volume=None,factor=1.2):
        if volume is None:
            return index**(index+factor)
        elif index is None:
            return #could not calculate inverse yet

    @staticmethod
    def stieber(index,volume=None,factor=3):
        if volume is None:
            return index/(index+factor*(1-index))
        elif index is None:
            return volume*factor/(1+volume*(factor-1))

    @staticmethod
    def larionov_tertiary(index,volume=None,**kwargs):
        if volume is None:
            return 0.083*(2**(3.7*index)-1)
        elif index is None:
            return numpy.log2(volume/0.083+1)/3.7

class spotential():

    def __init__(self):

        pass