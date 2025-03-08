from matplotlib import pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path

import numpy

from _templix import PropDict
    
class Weaver():

    @staticmethod
    def fill_between(axis:plt.Axes,x:numpy.ndarray,y1:numpy.ndarray,y2:numpy.ndarray,prop:PropDict):

        # Fill between the curves
        fill = axis.fill_between(x,y1,y2,facecolor=prop.facecolor,hatch=prop.hatch)

        for motif in prop.motifs:
            # Create the pattern patches
            patches = Weaver.patches(
                x.min(),x.max(),y1.min(),y2.max(),motif
                )

            # Clip the pattern patches
            for patch in patches:
                patch.set_clip_path(
                    fill.get_paths()[0],transform=axis.transData
                    )  # Clip each patch to the filled region

                axis.add_patch(patch)

        return axis

    @staticmethod
    def patches(x_min,x_max,y_min,y_max,motif):
        """Creates individual patches within a bounded region. Returns list of PathPatch objects."""
        offsety = motif.height*(motif.height_ratio-1)/2.

        y_nodes = numpy.arange(y_min+offsety,y_max,motif.extern_height)

        offset1 = motif.length*(motif.length_ratio-1)/2.
        offset2 = motif.length*motif.offset_ratio

        x_lower = numpy.arange(x_min+offset1,x_max,motif.extern_length)
        x_upper = numpy.arange(x_min-offset2,x_max,motif.extern_length)

        patches = []
        
        for y_index,y_node in enumerate(y_nodes):

            x_nodes = x_lower if y_index%2==0 else x_upper
            
            for x_node in x_nodes:

                path = Weaver.path(x_node,y_node,motif)
                
                patches.append(PathPatch(path,**motif.params))
        
        return patches

    def path(x_node,y_node,motif):
        """Returns path for the instance figure."""
        element = getattr(Weaver,motif.element)

        x_func,y_func = element(length=motif.length,height=motif.height,tilted_ratio=motif.tilted_ratio)

        return Path([(x,y) for x,y in zip(x_func(x_node),y_func(y_node))])

    @staticmethod
    def fissure(length=0.2,**kwargs):
        """Returns functions that calculates line vertex coordinates for the given lower left corner."""
        x_func = lambda x: [x, x+length, x]
        y_func = lambda y: [y, y, y]

        return x_func,y_func


    @staticmethod
    def triangle(length=0.2,height=0.1,tilted_ratio=0.):
        """Returns functions that calculates triangle vertex coordinates for the given lower left corner."""
        x_func = lambda x: [x, x+length, x+length/2+length*tilted_ratio, x]
        y_func = lambda y: [y, y, y+height, y]

        return x_func,y_func

    @staticmethod
    def quadrupe(length=0.8,height=0.4,tilted_ratio=0.):
        """Returns functions that calculates quadrilateral node coordinates for the given lower left corner."""
        x_func = lambda x: [x, x+length, x+length+length*tilted_ratio, x+length*tilted_ratio, x]
        y_func = lambda y: [y, y, y+height, y+height, y]

        return x_func,y_func

if __name__ == "__main__":

    import numpy as np

    from _templix import PropDict
    from _templix import MotifPattern

    x = np.linspace(0, 10, 100)

    y1 = np.sin(x) * 2 + 6
    y2 = np.sin(x) * 2 + 8 # Upper curve

    fig,ax = plt.subplots(figsize=(8,5))

    motif = MotifPattern(**dict(
            element="triangle",length=0.4,height=0.3,offset_ratio=0.5,tilted_ratio=0.,length_ratio=4.,height_ratio=2,
            params = dict(edgecolor='black',fill=None)
            ))

    prop = PropDict(**{"facecolor":"tan","hatch":None,"motifs":(motif,)})

    # alpha=0.5,edgecolor='black',lw=1.2,
    ax = Weaver.fill_between(ax,x,y1,y2,prop=prop)

    # Adjust limits and labels
    # ax.set_xlim(x.min(),x.max())
    ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()