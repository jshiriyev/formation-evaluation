from matplotlib import pyplot as plt

from matplotlib.backend_bases import MouseButton

import numpy

class pickett():

    def __init__(self,axis):

        self.set_archie_coeffs()
        self.set_axis(axis)
        self.set_water_lines(50,20,10)
        self.set_mouse_connection()

    def set_archie_coeffs(self,a=1,m=2,n=2,Rw=0.01):

        self.archie_a = a
        self.archie_m = m
        self.archie_n = n
        self.archie_Rw = Rw

        self.slope = self.archie_m

        self.intercept = self.archie_a*self.archie_Rw

    def set_axis(self,axis=None):

        if axis is None:
            figure,axis = plt.subplots(nrows=1,ncols=1)

        self.axis = axis

        self.xlim = numpy.array([-0.5,2])
        self.ylim = numpy.array([2,-1])

        self.axis.invert_yaxis()

        self.axis.set_xlabel("x-axis")
        self.axis.set_ylabel("y-axis")

        self.axis.set_xlim(self.xlim)
        self.axis.set_ylim(self.ylim)

        self.lines = []

        self.canvas = self.axis.figure.canvas

    def set_water_lines(self,*args):
        """arguments must be water saturation percentage in a decreasing order!"""

        saturations = [100]

        [saturations.append(arg) for arg in args]

        base = self.slope*self.xlim+self.intercept

        for line in self.lines:

            line.remove()

        self.lines = []

        linewidth = 1.0

        alpha = 1.0

        for saturation in saturations:

            yvals = base+self.archie_n*numpy.log10(saturation/100)

            line, = self.axis.plot(self.xlim,yvals,linewidth=linewidth,color="blue",alpha=alpha)

            linewidth -= 0.1

            alpha -= 0.1

            self.lines.append(line)

        self.canvas.draw()

    def set_mouse_connection(self):

        self.pressed = False
        self.start = False

        self.canvas.mpl_connect('button_press_event',self.mouse_press)
        self.canvas.mpl_connect('motion_notify_event',self.mouse_move)
        self.canvas.mpl_connect('button_release_event',self.mouse_release)

    def saturations(self):

        pass

    def mouse_press(self,event):

        if self.axis.get_navigate_mode()!= None: return
        if not event.inaxes: return
        if event.inaxes != self.axis: return

        if self.start: return

        if event.button is not MouseButton.LEFT: return

        self.pressed = True

    def mouse_move(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if not self.pressed: return

        self.start = True

        self.intercept = event.ydata-self.slope*event.xdata

        self.set_water_lines()

    def mouse_release(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if self.pressed:

            self.pressed = False
            self.start = False

            self.set_water_lines(50,20,10)

            return

model = numpy.array([
    (0.310, -0.687), (0.407, -0.355), (0.455, -0.142), (0.504, 0.061), (0.552, 0.238), 
    (0.601,  0.380), (0.698,  0.549), (0.746,  0.581), (0.795, 0.587), (0.859, 0.567), 
    (0.956,  0.511), (1.053,  0.473), (1.150,  0.489), (1.199, 0.523), (1.296, 0.640), 
    (1.393,  0.812), (1.490,  0.981), (1.587,  1.189), (1.684, 1.386), (1.781, 1.572), 
    (1.878, 1.766)])

obser = numpy.array([
    (0.212, -0.114), (0.199, 0.017), (0.259, 0.020), (0.199, 0.076), (0.297, 0.082), 
    (0.735, 0.085), (0.641, 0.104), (0.791, 0.104), (0.681, 0.109), (0.606, 0.132), 
    (0.262, 0.135), (0.813, 0.137), (0.334, 0.157), (0.565, 0.165), (0.647, 0.170), 
    (0.876, 0.174), (0.746, 0.186), (0.509, 0.197), (0.398, 0.203), (0.693, 0.207), 
    (0.829, 0.215), (0.299, 0.226), (0.585, 0.228), (0.549, 0.242), (0.430, 0.242), 
    (0.637, 0.253), (0.511, 0.257), (0.918, 0.268), (0.813, 0.269), (0.746, 0.271), 
    (0.336, 0.288), (0.449, 0.297), (0.398, 0.299), (0.783, 0.306), (0.578, 0.312), 
    (0.871, 0.330), (0.515, 0.345), (0.468, 0.353), (0.818, 0.380), (0.936, 0.391), 
    (0.889, 0.416), (0.876, 0.503), (1.027, 0.522), (1.040, 0.601), (0.965, 0.656), 
    (1.130, 0.796), (1.224, 0.845), (1.261, 0.964), (1.378, 1.149)])

fig,ax1 = plt.subplots(nrows=1,ncols=1)
# fig.subplots_adjust(left=0.14,bottom=0.08,right=0.95,top=0.97,wspace=0,hspace=0)

pickett = pickett(ax1)

pickett.axis.scatter(*obser.T,s=2,c="k")

fig.tight_layout()

plt.show()
