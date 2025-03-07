from dataclasses import dataclass

from matplotlib import pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path

import numpy

@dataclass
class PatchPattern:
    motive : str = None
    length : float = 0.8        # length of each pattern figure.
    height : float = 0.4        # height of each pattern figure.
    bottom_ratio  : float = 1.  # how much spacing to put between the figures.
    offset_ratio  : float = 0.5 # how much to horizontally shift every other row (0 = no shift, 0.5 = half length).
    tilting_ratio : float = 0.  # how much tilting to use for the ceiling of the figure.

class PatternBuilder():

    @staticmethod
    def fill_between(axis:plt.Axes,x:numpy.ndarray,y1:numpy.ndarray,y2:numpy.ndarray,patch:dict=None,**kwargs:dict):

        # Fill between the curves
        fill = axis.fill_between(x,y1,y2,**kwargs)

        pattern = PatchPattern(**patch)

        if pattern.motive is None:
            return axis

        # Create and clip the brick pattern
        patches = PatternBuilder.patches(x.min(),x.max(),y1.min(),y2.max(),pattern)

        for patch in patches:
            patch.set_clip_path(
                fill.get_paths()[0],transform=axis.transData
                )  # Clip each brick to the filled region

            axis.add_patch(patch)

        return axis

    @staticmethod
    def patches(x_min,x_max,y_min,y_max,pattern:PatchPattern,**kwargs):
        """Creates individual patches within a bounded region. Returns list of PathPatch objects representing bricks."""
        y_nodes = numpy.arange(
            y_min-pattern.height*(pattern.bottom_ratio-1)/2.,
            y_max+pattern.height*(pattern.bottom_ratio-1)/2.,
            pattern.height*pattern.bottom_ratio
            )

        offset1 = pattern.length*(pattern.bottom_ratio-1)/2.
        offset2 = pattern.length*(pattern.bottom_ratio-1)/2.+pattern.offset_ratio*pattern.length*pattern.bottom_ratio

        x_lower = numpy.arange(x_min+offset1,x_max,pattern.length*pattern.bottom_ratio)
        x_upper = numpy.arange(x_min+offset2,x_max,pattern.length*pattern.bottom_ratio)

        patches = []
        
        for y_index,y_node in enumerate(y_nodes):

            x_nodes = x_lower if y_index%2==0 else x_upper
            
            for x_node in x_nodes:

                path = PatternBuilder.path(x_node,y_node,pattern)
                
                patches.append(PathPatch(path,**kwargs))
        
        return patches

    def path(x_node,y_node,pattern):
        """Returns path for the instance figure."""
        x_func,y_func = getattr(PatternBuilder,pattern.motive)(
            pattern.length,
            pattern.height,
            pattern.tilting_ratio
            )

        return Path([(x,y) for x,y in zip(x_func(x_node),y_func(y_node))])

    @staticmethod
    def triangle(length=0.2,height=0.1,tilting_ratio=0.):
        """Returns functions that calculates triangle vertex coordinates for the given lower left corner."""
        x_func = lambda x: [x, x+length, x+length/2+length*tilting_ratio, x]
        y_func = lambda y: [y, y, y+height, y]

        return x_func,y_func

    @staticmethod
    def brick(length=0.8,height=0.4,tilting_ratio=0.):
        """Returns functions that calculates brick node coordinates for the given lower left corner."""
        x_func = lambda x: [x, x+length, x+length+length*tilting_ratio, x+length*tilting_ratio, x]
        y_func = lambda y: [y, y, y+height, y+height, y]

        return x_func,y_func

if __name__ == "__main__":

    import numpy as np

    x = np.linspace(0, 10, 100)

    y1 = np.sin(x) * 2 + 6
    y2 = np.sin(x) * 2 + 8 # Upper curve

    fig,ax = plt.subplots(figsize=(8,5))

    ax = PatternBuilder.fill_between(ax,x,y1,y2,color="tan",alpha=0.5,facecolor='none',edgecolor='black',lw=1.2,
        patch=dict(
            motive="triangle",length=0.8,height=0.4,offset_ratio=0.5,tilting_ratio=0.,bottom_ratio=3.,
        ))

    # Adjust limits and labels
    # ax.set_xlim(x.min(),x.max())
    ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()