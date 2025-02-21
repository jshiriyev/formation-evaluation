from matplotlib import pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.collections import PatchCollection

import numpy

def brick_pattern(x_min,x_max,y_min,y_max,brick_width=1,brick_height=0.5,offset_ratio=0.5):
    """Creates individual brick patches within a bounded region.
    
    Parameters:
    - x_min, x_max: Horizontal boundaries where bricks should be drawn.
    - y_min, y_max: Vertical boundaries where bricks should be drawn.

    - brick_width: Width of each brick.
    - brick_height: Height of each brick.
    
    - offset_ratio: How much to horizontally shift every other row (0 = no shift, 0.5 = half a brick width).
    
    Returns:
    - List of PathPatch objects representing bricks.
    """
    patches = []

    cols = int((x_max-x_min)/brick_width)+1
    rows = int((y_max-y_min)/brick_height)+1

    x_starts = numpy.tile([x_min,x_min+brick_width*offset_ratio],(rows+1)//2)[:rows]
    y_starts = numpy.arange(y_min,y_max+brick_height/2,brick_height)

    x_lower = numpy.arange(x_min,x_max+brick_width/2,brick_width)
    x_upper = numpy.arange(x_min+brick_width/2,x_max+brick_width/2,brick_width)
    
    for index,(x_start,y_start) in enumerate(zip(x_starts,y_starts)):
        
        for idx,col in enumerate(range(cols)):

            x = x_lower[idx] if index%2==0 else x_upper[idx]

            vertices = [
                (x,y_start), 
                (x+brick_width,y_start), 
                (x+brick_width,y_start+brick_height), 
                (x,y_start+brick_height), 
                (x,y_start)
            ]

            brick = PathPatch(Path(vertices),facecolor='none',edgecolor='brown',lw=1.2)
            
            patches.append(brick)
    
    return patches

if __name__ == "__main__":

    import numpy as np

    # Generate sample data
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x) * 2 + 8 # Upper curve
    y2 = np.sin(x) * 2 + 6

    fig, ax = plt.subplots(figsize=(8, 5))

    # Fill between the curves
    fill = ax.fill_between(x, y1, y2, color="tan", alpha=0.5)

    # Create and clip the brick pattern
    brick_patches = brick_pattern(0,10,4,10,brick_width=0.8,brick_height=0.4)

    for brick in brick_patches:
        brick.set_clip_path(fill.get_paths()[0], transform=ax.transData)  # Clip each brick to the filled region
        ax.add_patch(brick)

    # Adjust limits and labels
    # ax.set_xlim(x.min(), x.max())
    ax.set_ylim(y2.min(), y1.max() + 0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()