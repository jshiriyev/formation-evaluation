from matplotlib import pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path

import numpy

class CustomPattern():

    def __init__(self,pattern:str):
        self.pattern = pattern

    def path(self,x_node,y_node,*args,**kwargs):
        x_func,y_func = getattr(self,self.pattern)(*args,**kwargs)
        return Path([(x,y) for x,y in zip(x_func(x_node),y_func(y_node))])

    @staticmethod
    def triangle(length,height,tilt_ratio=0.):
        x_func = lambda x: [x, x+length, x+length/2*tilt_ratio]
        y_func = lambda y: [y, y, y+height]
        return x_func,y_func

    @staticmethod
    def brick(length,height,tilt_ratio=0.):
        x_func = lambda x: [x, x+length, x+length+length*tilt_ratio, x+length*tilt_ratio]
        y_func = lambda y: [y, y, y+height, y+height]
        return x_func,y_func

def fill_pattern(axis,x:numpy.ndarray,y1:numpy.ndarray,y2:numpy.ndarray,pattern:dict=None,**kwargs):

    # Fill between the curves
    fill = axis.fill_between(x,y1,y2,**kwargs)

    # Create and clip the brick pattern
    patches = brick_patches(x.min(),x.max(),y1.min(),y2.max(),**pattern)

    for patch in patches:
        patch.set_clip_path(
            fill.get_paths()[0],transform=axis.transData
            )  # Clip each brick to the filled region

        axis.add_patch(patch)

    return axis

def brick_patches(x_min:float,x_max:float,y_min:float,y_max:float,length:float=1,height:float=0.5,offset_ratio:float=0.5,tilt_ratio=0.,**kwargs):
    """Creates individual brick patches within a bounded region.
    
    Parameters:
    - x_min,x_max   : horizontal boundaries where bricks should be drawn.
    - y_min,y_max   : vertical boundaries where bricks should be drawn.

    - length  : length of each brick.
    - height  : height of each brick.
    
    - offset_ratio  : how much to horizontally shift every other row (0 = no shift, 0.5 = half a brick length).
    
    Returns:
    - List of PathPatch objects representing bricks.
    """
    y_nodes = numpy.arange(y_min,y_max,height)

    offset = offset_ratio*length

    x_lower = numpy.arange(x_min,x_max,length)
    x_upper = numpy.arange(x_min-offset,x_max,length)

    x_func = lambda x: [x, x+length, x+length+length*tilt_ratio, x+length*tilt_ratio]
    y_func = lambda y: [y, y, y+height, y+height]

    patches = []

    pattern = CustomPattern("brick")
    
    for y_index,y_node in enumerate(y_nodes):

        x_nodes = x_lower if y_index%2==0 else x_upper
        
        for x_node in x_nodes:

            path = pattern.path(x_node,y_node,length=length,height=height,tilt_ratio=0.)
            
            patches.append(PathPatch(path,fill=False,**kwargs))
    
    return patches

if __name__ == "__main__":

    import numpy as np

    x = np.linspace(0, 10, 100)

    y1 = np.sin(x) * 2 + 6
    y2 = np.sin(x) * 2 + 8 # Upper curve

    fig,ax = plt.subplots(figsize=(8,5))

    ax = fill_pattern(ax,x,y1,y2,color="tan",alpha=0.5,
        pattern=dict(
            length=0.8,height=0.4,offset_ratio=0.5,facecolor='none',edgecolor='black',lw=1.2
        ))

    # Adjust limits and labels
    # ax.set_xlim(x.min(),x.max())
    ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()