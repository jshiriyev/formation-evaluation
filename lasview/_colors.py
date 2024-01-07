import numpy

from matplotlib import pyplot

from matplotlib import colors as mcolors

from matplotlib.patches import Polygon

def gradient(x,y,fill_color=None,axis=None,alpha=None,**kwargs):
    """
    Plot a line with a linear alpha gradient filled beneath it.

    Parameters
    ----------
    x, y : array-like
        The data values of the line.
    fill_color : a matplotlib color specifier (string, tuple) or None
        The color for the fill. If None, the color of the line will be used.
    axis : a matplotlib Axes instance
        The axes to plot on. If None, the current pyplot axes will be used.
    Additional arguments are passed on to matplotlib's ``plot`` function.

    Returns
    -------
    line : a Line2D instance
        The line plotted.
    im : an AxesImage instance
        The transparent gradient clipped to just the area beneath the curve.
    """

    if axis is None:
        axis = pyplot.gca()

    line, = axis.plot(x,y,**kwargs)

    if fill_color is None:
        fill_color = line.get_color()

    zorder = line.get_zorder()

    # z = numpy.empty((y.size,1,3),dtype='float64')

    rgb = mcolors.colorConverter.to_rgb(fill_color)

    # print(rgb)

    rgb = numpy.array([rgb]).repeat(y.size,axis=0)

    # print(rgb)

    # print(rgb[:,:,numpy.newaxis])

    z = rgb[:,:,numpy.newaxis].transpose((0,2,1))

    xmin,xmax = numpy.nanmin(x),numpy.nanmax(x)

    nondim = (x-xmin)/(xmax-xmin)

    z[:,0,1] = 1-nondim #numpy.vstack((nondim,nondim,nondim)).transpose()

    # z[z<0] = 0

    # z = numpy.empty((1,100,4),dtype=float)

    # rgb = mcolors.colorConverter.to_rgb(fill_color)

    # alpha_range = numpy.linspace(0,alpha,100)

    # alpha_range[alpha_range>1.0] = 1.0

    # z[:,:,:3] = rgb
    # z[:,:,-1] = alpha_range

    xmin,xmax = numpy.nanmin(x),numpy.nanmax(x)
    ymin,ymax = numpy.nanmin(y),numpy.nanmax(y)

    image = axis.imshow(z,
        aspect = 'auto',
        extent = [0,xmax,ymin,ymax],
        origin = 'lower',
        zorder = zorder)

    xy = numpy.column_stack([x,y])
    xy = numpy.vstack([[0,ymin],xy,[0,ymax],[0,ymin]])

    clip = Polygon(xy,facecolor='none',edgecolor='none',closed=True)

    axis.add_patch(clip)

    image.set_clip_path(clip)

    # axis.fill_betweenx(y,0,x2=x,hatch='..',zorder=3)

if __name__ == '__main__':

    numpy.random.seed(1977)

    # for _ in range(5):

    y = numpy.linspace(0,100,100)
    x = numpy.random.normal(0,1,100).cumsum()

    gradient_fill(x,y,alpha=1)
    
    pyplot.show()