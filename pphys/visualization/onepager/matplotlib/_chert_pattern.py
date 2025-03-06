import numpy
import matplotlib.pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path

def fill_pattern(axis,x:numpy.ndarray,y1:numpy.ndarray,y2:numpy.ndarray,pattern:dict=None,**kwargs):

    # Fill between the curves
    fill = axis.fill_between(x,y1,y2,**kwargs)

    # Create and clip the brick pattern
    # patches = brick_patches(x.min(),x.max(),y1.min(),y2.max(),**pattern)
    patches = triangle_patches(x.min(),x.max(),y1.min(),y2.max(),**pattern)

    for patch in patches:
        patch.set_clip_path(
            fill.get_paths()[0],transform=axis.transData
            )  # Clip each brick to the filled region

        axis.add_patch(patch)

    return axis

def brick_patches(
     x_min : float,
     x_max : float,
     y_min : float,
     y_max : float,
    length : float = 1,
    height : float = 0.5,
    offset_ratio : float = 0.5,
    tilt_ratio = 0.,
    **kwargs):
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
    y_nodes = numpy.arange(y_min,y_max+0.01*height,height)

    offset = offset_ratio*length

    x_lower = numpy.arange(x_min,x_max+0.01*length,length)
    x_upper = numpy.arange(x_min+offset,x_max+1.01*offset,length)

    patches = []
    
    for y_index in range(len(y_nodes)-1):

        x_nodes = x_lower if y_index%2==0 else x_upper
        
        for x_index in range(len(x_nodes)-1):

            vertices = Path([
                (x_nodes[x_index],y_nodes[y_index]), 
                (x_nodes[x_index+1],y_nodes[y_index]), 
                (x_nodes[x_index+1]+length*tilt_ratio,y_nodes[y_index+1]), 
                (x_nodes[x_index]+length*tilt_ratio,y_nodes[y_index+1]), 
                (x_nodes[x_index],y_nodes[y_index])
            ])
            
            patches.append(PathPatch(vertices,fill=False,**kwargs))
    
    return patches

def triangle_patches(
     x_min : float,
     x_max : float,
     y_min : float,
     y_max : float,
    length : float = 0.5,
    height : float = 0.5,
    spacing_ratio : float = 1.5,
    offset_ratio : float = 0.5,
    **kwargs):
    """Creates individual triangle patches within a bounded region."""
    y_nodes = numpy.arange(y_min+height/4.,y_max+height/4.,height*spacing_ratio)

    offset1 = length/4.
    offset2 = length/4.+offset_ratio*length*spacing_ratio

    x_lower = numpy.arange(x_min+offset1,x_max+offset1,length*spacing_ratio)
    x_upper = numpy.arange(x_min+offset2,x_max+offset2,length*spacing_ratio)

    x_nodes_func = lambda x: [x, x+length/2., x+length]
    y_nodes_func = lambda y: [y, y+height, y]

    patches = []

    for y_index, y_node in enumerate(y_nodes):

        x_nodes = x_lower if y_index%2==0 else x_upper
        
        for x_node in x_nodes:

            x_vertices = x_nodes_func(x_node)
            y_vertices = y_nodes_func(y_node)

            vertices_path = Path([
                (x_vertices[0],y_vertices[0]), 
                (x_vertices[2],y_vertices[2]), 
                (x_vertices[1],y_vertices[1]), 
                (x_vertices[0],y_vertices[0]),
            ])

            patches.append(PathPatch(vertices_path,fill=False,**kwargs))

    return patches

if __name__ == "__main__":

    # # # Plot
    # fig, ax = plt.subplots(figsize=(5, 2))

    # for x_nodes,y_nodes in triangles:
    #     print(x_nodes,y_nodes)
    #     vertices = Path([
    #         (x_nodes[0],y_nodes[0]), 
    #         (x_nodes[2],y_nodes[2]), 
    #         (x_nodes[1],y_nodes[1]), 
    #         (x_nodes[0],y_nodes[0]),
    #     ])

    #     ax.add_patch(PathPatch(vertices,fill=False))

    # # Formatting
    # ax.set_xlim(0, brick_length)
    # ax.set_ylim(0, brick_height)
    # # ax.set_xticks([])
    # # ax.set_yticks([])
    # ax.set_frame_on(False)

    # plt.show()

    triangle_length = 0.15
    triangle_height = 0.1

    x = numpy.linspace(0, 10, 100)

    y1 = numpy.sin(x) * 2 + 6
    y2 = numpy.sin(x) * 2 + 8 # Upper curve

    fig,ax = plt.subplots(figsize=(8,5))

    ax = fill_pattern(ax,x,y1,y2,color="tan",alpha=0.5,
        pattern=dict(
            length=triangle_length,height=triangle_height,spacing_ratio=2.5,offset_ratio=0.7,facecolor='none',edgecolor='black',lw=1.2,
        ))

    # Adjust limits and labels
    # ax.set_xlim(x.min(),x.max())
    ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()