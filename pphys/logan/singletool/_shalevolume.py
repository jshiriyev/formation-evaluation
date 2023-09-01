class gammaray():

    def __init__(self,total,potassium=None,thorium=None,uranium=None):

        self.total = total

        if potassium is not None:
            self.potassium = potassium

        if thorium is not None:
            self.thorium = thorium

        if uranium is not None:
            self.uranium = utanium

    def config(self):

        pass

    def shaleindex(values,grmin=None,grmax=None):

        if grmin is None:
            grmin = numpy.nanmin(values)

        if grmax is None:
            grmax = numpy.nanmax(values)

        return (values-grmin)/(grmax-grmin)

    def shalevolume(values,model="linear",factor=None,grmin=None,grmax=None):

        if grmin is None:
            grmin = numpy.nanmin(values)

        if grmax is None:
            grmax = numpy.nanmax(values)

        index = (values-grmin)/(grmax-grmin)

        if model == "linear":
            volume = index
        elif factor is None:
            volume = getattr(gammaray,f"{model}")(index)
        else:
            volume = getattr(gammaray,f"{model}")(index,factor=factor)

        return volume

    def cut(values,percent=40,model="linear",factor=None,grmin=None,grmax=None):

        if model == "linear":
            index = percent/100
        elif factor is None:
            index = getattr(gammaray,f"_{model}")(None,volume=percent/100)
        else:
            index = getattr(gammaray,f"_{model}")(None,volume=percent/100,factor=factor)

        if grmin is None:
            grmin = numpy.nanmin(values)

        if grmax is None:
            grmax = numpy.nanmax(values)

        return index*(grmax-grmin)+grmin

    def netthickness(depth,values,percent,**kwargs):

        grcut = gammaray.get_cut(percent,**kwargs)

        node_top = numpy.roll(depth,1)
        node_bottom = numpy.roll(depth,-1)

        thickness = (node_bottom-node_top)/2

        thickness[0] = (depth[1]-depth[0])/2
        thickness[-1] = (depth[-1]-depth[-2])/2

        return numpy.sum(thickness[values<grcut])

    def netgrossratio(depth,*args,**kwargs):

        height = max(depth)-min(depth)

        return gammaray.netthickness(depth,*args,**kwargs)/height

    def set_axis(self,axis=None):

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        self.axis = axis

    def show(self):

        pyplot.show()

    def larionov_oldrocks(index,volume=None):
        if volume is None:
            return 0.33*(2**(2*index)-1)
        elif index is None:
            return numpy.log2(volume/0.33+1)/2

    def clavier(index,volume=None):
        if volume is None:
            return 1.7-numpy.sqrt(3.38-(0.7+index)**2)
        elif index is None:
            return numpy.sqrt(3.38-(1.7-volume)**2)-0.7

    def bateman(index,volume=None,factor=1.2):
        if volume is None:
            return index**(index+factor)
        elif index is None:
            return #could not calculate inverse yet

    def stieber(index,volume=None,factor=3):
        if volume is None:
            return index/(index+factor*(1-index))
        elif index is None:
            return volume*factor/(1+volume*(factor-1))

    def larionov_tertiary(index,volume=None):
        if volume is None:
            return 0.083*(2**(3.7*index)-1)
        elif index is None:
            return numpy.log2(volume/0.083+1)/3.7

class spotential():

    def __init__(self):

        pass