from ._items import Zone

from ._zonesurface import Surface

class Formation():
    """It is a collection of surfaces"""

    def __init__(self):

        self.repo = {}

    def __setitem__(self,name,top):

        zone = Zone(name=name)

        zone.top = top

        self.repo[name] = zone

    def __getitem__(self,name):

        return self.repo[name]

    def tolist(self,prop):

        tops,props = [],[]

        for _,zone in self.repo.items():

            props.append(getattr(zone,prop))

            tops.append(zone.top)

        tops = numpy.array(tops)

        indices = numpy.argsort(tops)

        _props = []

        for index in indices:
            _props.append(props[index])

        return _props

    def view(self,axis=None):

        show = True if axis is None else False

        if axis is None:
            axis = pyplot.figure().add_subplot()

        tops = numpy.array(self.tolist("top"))

        depths = (tops[1:]+tops[:-1])/2

        axis.hlines(y=tops,xmin=0,xmax=1,color='k')

        axis.invert_yaxis()

        names = self.tolist("name")
        colors = self.tolist("color")
        hatches = self.tolist("hatch")

        for index,depth in enumerate(depths):

            axis.annotate(names[index],(0.5,depth),
                horizontalalignment='center',
                verticalalignment='center',
                backgroundcolor='white',)

            top,bottom = tops[index:index+2]

            axis.fill_between((0,1),top,y2=bottom,facecolor=colors[index],hatch=hatches[index])

        pyplot.setp(axis.get_xticklabels(),visible=False)
        pyplot.setp(axis.get_xticklines(),visible=False)

        if show:
            pyplot.show()

    @property
    def names(self):

        return self._names

    @property
    def tops(self):

        return self._tops