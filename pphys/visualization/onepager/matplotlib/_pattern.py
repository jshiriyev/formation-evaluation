from dataclasses import dataclass, field

from matplotlib import pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path

import numpy

@dataclass
class PatchPattern:
    """
    A class representing a repetitive patch pattern with customizable dimensions and spacing.

    Attributes:
    ----------
    motive (str): The shape used for the pattern.

    length (float): Length of each pattern figure. Must be positive.
    height (float): Height of each pattern figure. Must be positive.

    length_ratio (float): Spacing multiplier between patterns along the length.
    height_ratio (float): Spacing multiplier between patterns along the height.

    offset_ratio (float): Horizontal shift for every other row (0 = no shift, 0.5 = half length).
    tilted_ratio (float): Tilt applied to the ceiling of the figure (0 = no tilt, 1 = full length).
    """
    motive : str = None

    length : float = 0.8
    height : float = 0.4

    length_ratio  : float = 1.
    height_ratio  : float = 1.

    offset_ratio  : float = 0.5
    tilted_ratio  : float = 0.

    params : field(default_factory=dict) = None

    def __post_init__(self):
        """Validates input parameters and stores additional keyword arguments."""
        self.params = {} if self.params is None else self.params

    @property
    def extern_length(self):
        """Returns the effective external length, including spacing."""
        return self.length*self.length_ratio

    @property
    def extern_height(self):
        """Returns the effective external height, including spacing."""
        return self.height*self.height_ratio

    @property
    def tilted_length(self):
        """Returns the effective tilted length based on the tilt ratio."""
        return self.length*self.tilted_ratio
    
class PatternBuilder():

    @staticmethod
    def fill_between(axis:plt.Axes,x:numpy.ndarray,y1:numpy.ndarray,y2:numpy.ndarray,patch:dict=None,**kwargs:dict):

        # Fill between the curves
        fill = axis.fill_between(x,y1,y2,**kwargs)

        # Create the pattern object if `patch` is provided
        pattern = PatchPattern(**patch) if patch else PatchPattern()

        if pattern.motive is None:
            return axis # No pattern applied, return early

        # Create the pattern patches
        patches = PatternBuilder.patches(
            x.min(),x.max(),y1.min(),y2.max(),pattern
            )

        # Clip the pattern patches
        for patch in patches:
            patch.set_clip_path(
                fill.get_paths()[0],transform=axis.transData
                )  # Clip each brick to the filled region

            axis.add_patch(patch)

        return axis

    @staticmethod
    def patches(x_min,x_max,y_min,y_max,pattern:PatchPattern):
        """Creates individual patches within a bounded region. Returns list of PathPatch objects representing bricks."""
        offsety = pattern.height*(pattern.height_ratio-1)/2.

        y_nodes = numpy.arange(y_min+offsety,y_max,pattern.extern_height)

        offset1 = pattern.length*(pattern.length_ratio-1)/2.
        offset2 = pattern.length*pattern.offset_ratio

        x_lower = numpy.arange(x_min+offset1,x_max,pattern.extern_length)
        x_upper = numpy.arange(x_min-offset2,x_max,pattern.extern_length)

        patches = []
        
        for y_index,y_node in enumerate(y_nodes):

            x_nodes = x_lower if y_index%2==0 else x_upper
            
            for x_node in x_nodes:

                path = PatternBuilder.path(x_node,y_node,pattern)
                
                patches.append(PathPatch(path,**pattern.params))
        
        return patches

    def path(x_node,y_node,pattern):
        """Returns path for the instance figure."""
        x_func,y_func = getattr(PatternBuilder,pattern.motive)(
            pattern.length,
            pattern.height,
            pattern.tilted_ratio
            )

        return Path([(x,y) for x,y in zip(x_func(x_node),y_func(y_node))])

    @staticmethod
    def triangle(length=0.2,height=0.1,tilted_ratio=0.):
        """Returns functions that calculates triangle vertex coordinates for the given lower left corner."""
        x_func = lambda x: [x, x+length, x+length/2+length*tilted_ratio, x]
        y_func = lambda y: [y, y, y+height, y]

        return x_func,y_func

    @staticmethod
    def brick(length=0.8,height=0.4,tilted_ratio=0.):
        """Returns functions that calculates brick node coordinates for the given lower left corner."""
        x_func = lambda x: [x, x+length, x+length+length*tilted_ratio, x+length*tilted_ratio, x]
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
            motive="triangle",length=0.4,height=0.3,offset_ratio=0.5,tilted_ratio=0.,length_ratio=4., height_ratio=2,
        ))

    # Adjust limits and labels
    # ax.set_xlim(x.min(),x.max())
    ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()