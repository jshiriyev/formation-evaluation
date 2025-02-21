from matplotlib import pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path

import numpy

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

def brick_patches(x_min:float,x_max:float,y_min:float,y_max:float,brick_width:float=1,brick_height:float=0.5,offset_ratio:float=0.5,**kwargs):
    """Creates individual brick patches within a bounded region.
    
    Parameters:
    - x_min,x_max   : horizontal boundaries where bricks should be drawn.
    - y_min,y_max   : vertical boundaries where bricks should be drawn.

    - brick_width   : width of each brick.
    - brick_height  : height of each brick.
    
    - offset_ratio  : how much to horizontally shift every other row (0 = no shift, 0.5 = half a brick width).
    
    Returns:
    - List of PathPatch objects representing bricks.
    """
    patches = []

    y_nodes = numpy.arange(y_min,y_max+0.01*brick_height,brick_height)

    offset = offset_ratio*brick_width

    x_lower = numpy.arange(x_min,x_max+0.01*brick_width,brick_width)
    x_upper = numpy.arange(x_min+offset,x_max+1.01*offset,brick_width)
    
    for y_index in range(len(y_nodes)-1):

        x_nodes = x_lower if y_index%2==0 else x_upper
        
        for x_index in range(len(x_nodes)-1):

            vertices = Path([
                (x_nodes[x_index],y_nodes[y_index]), 
                (x_nodes[x_index+1],y_nodes[y_index]), 
                (x_nodes[x_index+1],y_nodes[y_index+1]), 
                (x_nodes[x_index],y_nodes[y_index+1]), 
                (x_nodes[x_index],y_nodes[y_index])
            ])
            
            patches.append(PathPatch(vertices,**kwargs))
    
    return patches

if __name__ == "__main__":

    import numpy as np

    x = np.linspace(0, 10, 100)

    y1 = np.sin(x) * 2 + 6
    y2 = np.sin(x) * 2 + 8 # Upper curve

    fig,ax = plt.subplots(figsize=(8,5))

    ax = fill_pattern(ax,x,y1,y2,color="tan",alpha=0.5,
        pattern=dict(
            brick_width=0.8,brick_height=0.4,offset_ratio=0.5,facecolor='none',edgecolor='black',lw=1.2
        ))

    # Adjust limits and labels
    # ax.set_xlim(x.min(),x.max())
    ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()