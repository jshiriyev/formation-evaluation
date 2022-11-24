from matplotlib import pyplot as plt

from matplotlib.backend_bases import MouseButton

import numpy

class PicketPlot():

    def __init__(self,axis,ebv,eub):

        self.axis = axis
        self.canvas = self.axis.figure.canvas

        self.archie_m = 1
        self.archie_a = 0
        self.archie_Rw = 1
        self.archie_n = 2

        self.slope = self.archie_m

        self.intercept = self.archie_Rw*self.archie_a

        self.line, = axis.plot(*self.water_line(),linewidth=1.1,c="b")

        self.xydata = self.line.get_xydata()

        self.shift = 0.0
        
        self.ebv = ebv
        self.eub = eub

        self.moved = None
        self.point = None
        self.pressed = False
        self.start = False

        self.canvas.mpl_connect('button_press_event',self.mouse_press)
        self.canvas.mpl_connect('motion_notify_event',self.mouse_move)
        self.canvas.mpl_connect('button_release_event',self.mouse_release)

    def water_line(self,slope=None,intercept=None,percent=None):

        if slope is None:
            slope = self.slope

        if intercept is None:
            intercept = self.intercept

        x_values = self.axis.get_xlim()

        y_values = [slope*x+intercept for x in x_values]

        return x_values,y_values

    def mouse_press(self,event):

        if self.axis.get_navigate_mode()!= None: return
        if not event.inaxes: return
        if event.inaxes != self.axis: return

        if self.start: return

        if event.button is not MouseButton.LEFT: return

        self.point = event.xdata
        self.pressed = True

    def mouse_move(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if not self.pressed: return

        self.start = True

        # intercept = self.slope*event.xdata+event.ydata

        self.shift = self.point-event.xdata

        keub = 0.72*self.shift+0.025*self.shift**2

        self.moved = self.xydata-[self.shift,keub]

        self.line.remove()

        # self.line, = self.axis.plot(*self.water_line(intercept=intercept),linewidth=1.1,c="b")
        self.line, = self.axis.plot(self.moved[:,0],self.moved[:,1],linewidth=1.1,c="b")

        self.canvas.draw()

    def mouse_release(self,event):

        if self.axis.get_navigate_mode()!=None: return
        if not event.inaxes: return
        if event.inaxes!=self.axis: return

        if self.pressed:

            self.pressed = False
            self.start = False
            self.point = None
            self.ebv -= self.shift
            self.xydata = self.moved

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

shift = (model.mean(axis=0)-obser.mean(axis=0))

sebv = shift[0]
seub = 0.72*sebv+0.025*sebv**2

ax1.invert_yaxis()
ax1.set_xlabel("BmV")
ax1.set_ylabel("UmB")
ax1.set_ylim(2, -1)
ax1.set_xlim(-0.5, 2)
ax1.scatter(obser[:,0],obser[:,1],s=2,c="k")

moveline = PicketPlot(ax1,sebv,seub)

fig.tight_layout()

plt.show()
