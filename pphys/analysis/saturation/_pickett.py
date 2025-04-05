from dataclasses import dataclass

import numpy

from borepy.utils._wrappers import trim

class pickett():

    def __init__(self,PHI=None,RT=None):
        """Initialization of Pickett (porosity vs. resistivity)
        cross-plot that assists in water saturation calculation.

        PHI : las curve for porosity (y-axis).
        RT  : las curve for resistivity (x-axis).

        """

        self.PHI = PHI

        self.RT = RT

    def config(self,slope=None,intercept=None,**kwargs):
        """Configures the cross-plot settings

        slope           : slope of 100% water saturation line, negative of cementation exponent.
        intercept       : intercept of 100% water saturation line, multiplication of
                          tortuosity exponent and formation water resistivity.
        
        **kwargs        : archie parameters, keys are 'm', 'a', 'Rw' and 'n'. 
        """

        archie = {}

        for key,value in kwargs.items():
            archie[key] = value

        self.archie = archie

        if slope is None:
            slope = -1/self.archie['m']

        self.slope = slope

        if intercept is None:
            intercept = numpy.log10(self.archie['a']*self.archie['Rw'])/self.archie['m']

        self.intercept = intercept

    def set_axis(self,axis=None):

        if axis is None:
            figure,axis = pyplot.subplots(nrows=1,ncols=1)

        self.axis = axis

        xaxis = self.resistivity.vals
        yaxis = self.porosity.vals

        self.axis.scatter(xaxis,yaxis,s=2,c="k")

        self.axis.set_xscale('log')
        self.axis.set_yscale('log')

        xlim = numpy.array(self.axis.get_xlim())
        ylim = numpy.array(self.axis.get_ylim())

        self.xlim = numpy.floor(numpy.log10(xlim))+numpy.array([0,1])
        self.ylim = numpy.floor(numpy.log10(ylim))+numpy.array([0,1])

        self.axis.set_xlabel(f"Resistivity [{self.resistivity.unit}]")
        self.axis.set_ylabel(f"Porosity [{self.porosity.unit}]")

        self.axis.set_xlim(10**self.xlim)
        self.axis.set_ylim(10**self.ylim)

        fstring = 'x={:1.3f} y={:1.3f} m={:1.3f} b={:1.3f}'

        self.axis.format_coord = lambda x,y: fstring.format(x,y,-1/self.slope,self.intercept)

        self.lines = []

        self.canvas = self.axis.figure.canvas

    def set_lines(self,*args):
        """arguments must be water saturation percentage in a decreasing order!"""

        saturations = [100]

        [saturations.append(arg) for arg in args]

        base = self.slope*self.xlim+self.intercept

        for line in self.lines:

            line.remove()

        self.lines = []

        linewidth = 1.0

        alpha = 1.0

        X = 10**self.xlim

        n = self.archie['n']

        m = -1/self.slope

        for Sw in saturations:

            Sw = Sw/100

            Y = 10**(base-n/m*numpy.log10(Sw))

            line, = self.axis.plot(X,Y,linewidth=linewidth,color="blue",alpha=alpha)

            linewidth -= 0.1

            alpha -= 0.1

            self.lines.append(line)

        self.canvas.draw()

    def set_mouse(self):

        self.pressed = False
        self.start = False

        self.canvas.mpl_connect('button_press_event',self._mouse_press)
        self.canvas.mpl_connect('motion_notify_event',self._mouse_move)
        self.canvas.mpl_connect('button_release_event',self._mouse_release)

    def _mouse_press(self,event):

        if self.axis.get_navigate_mode()!= None: return
        if not event.inaxes: return
        if event.inaxes != self.axis: return

        if self.start: return

        if event.button is not MouseButton.LEFT: return

        self.pressed = True

    def _mouse_move(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if not self.pressed: return

        self.start = True

        x = numpy.log10(event.xdata)
        y = numpy.log10(event.ydata)

        self.intercept = y-self.slope*x

        self.set_lines()

    def _mouse_release(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if self.pressed:

            self.pressed = False
            self.start = False

            self.set_lines(50,20,10)

            return

    def show(self):

        pyplot.show()

    @trim
    def saturation(self):

        m = -1/self.slope

        aRw = 10**(m*self.intercept)

        n = self.archie['n']

        Rt = self.RES

        phi = self.PHI

        Sw = (aRw/Rt/phi**m)**(1/n)

        Sw[Sw>1] = 1

        info = 'Water saturation from Pickett Cross-Plot.'

        return Sw
        # return LasCurve(
        #     depth = self.depth,
        #     vals = Sw,
        #     head = 'SW',
        #     unit = '-',
        #     info = info)

    @property
    def depth(self):

        return self.PHI.depth