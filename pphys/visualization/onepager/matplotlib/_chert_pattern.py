import numpy
import matplotlib.pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path

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

def brick_patches(x_min:float,x_max:float,y_min:float,y_max:float,brick_length:float=1,brick_height:float=0.5,offset_ratio:float=0.5,tilt_ratio=0.,**kwargs):
    """Creates individual brick patches within a bounded region.
    
    Parameters:
    - x_min,x_max   : horizontal boundaries where bricks should be drawn.
    - y_min,y_max   : vertical boundaries where bricks should be drawn.

    - brick_length  : length of each brick.
    - brick_height  : height of each brick.
    
    - offset_ratio  : how much to horizontally shift every other row (0 = no shift, 0.5 = half a brick length).
    
    Returns:
    - List of PathPatch objects representing bricks.
    """
    patches = []

    y_nodes = numpy.arange(y_min,y_max+0.01*brick_height,brick_height)

    offset = offset_ratio*brick_length

    x_lower = numpy.arange(x_min,x_max+0.01*brick_length,brick_length)
    x_upper = numpy.arange(x_min+offset,x_max+1.01*offset,brick_length)
    
    for y_index in range(len(y_nodes)-1):

        x_nodes = x_lower if y_index%2==0 else x_upper
        
        for x_index in range(len(x_nodes)-1):

            vertices = Path([
                (x_nodes[x_index],y_nodes[y_index]), 
                (x_nodes[x_index+1],y_nodes[y_index]), 
                (x_nodes[x_index+1]+brick_length*tilt_ratio,y_nodes[y_index+1]), 
                (x_nodes[x_index]+brick_length*tilt_ratio,y_nodes[y_index+1]), 
                (x_nodes[x_index],y_nodes[y_index])
            ])
            
            patches.append(PathPatch(vertices,fill=False,**kwargs))
    
    return patches

def triangle_patches(
	x_min : float,
	x_max : float,
	y_min : float,
	y_max : float,
	triangle_bottom : float=0.5,
	triangle_height : float=0.5,
	offset_ratio : float=0.5,
	**kwargs):

    patches = []

    y_nodes = numpy.arange(y_min,y_max+0.01*triangle_height,triangle_height)

    offset = offset_ratio*brick_width

    x_lower = numpy.arange(x_min,x_max+0.01*brick_width,brick_width)
    x_upper = numpy.arange(x_min+offset,x_max+1.01*offset,brick_width)
    
    for y_index in range(len(y_nodes)-1):

        x_nodes = x_lower if y_index%2==0 else x_upper
        
        for x_index in range(len(x_nodes)-1):

            vertices = Path([
                (x_nodes[x_index],y_nodes[y_index]), 
                (x_nodes[x_index+1],y_nodes[y_index]), 
                (x_nodes[x_index+1]+brick_width*tilt_ratio,y_nodes[y_index+1]), 
                (x_nodes[x_index]+brick_width*tilt_ratio,y_nodes[y_index+1]), 
                (x_nodes[x_index],y_nodes[y_index])
            ])
            
            patches.append(PathPatch(vertices,fill=False,**kwargs))
    
    return patches

# Define triangles inside the rectangle

triangle_bottom = 3.
triangle_height = 3.

brick_length = 9.*triangle_bottom/2.
brick_height = 3.*triangle_height

xnodes = lambda x: [x, x+triangle_bottom/2., x+triangle_bottom]
ynodes = lambda y: [y, y+triangle_height, y]

triangles = [
    [xnodes( 4.*triangle_bottom/4.), ynodes(1.*triangle_height/4.)],  # Left triangle
    [xnodes(10.*triangle_bottom/4.), ynodes(1.*triangle_height/4.)],  # Right triangle
    [xnodes( 7.*triangle_bottom/4.), ynodes(7.*triangle_height/4.)],  # Top triangle
    [xnodes( 1.*triangle_bottom/4.), ynodes(7.*triangle_height/4.)],  # Left-top triangle
    [xnodes(13.*triangle_bottom/4.), ynodes(7.*triangle_height/4.)],  # Right-top triangle
]

# Define the rectangle boundary
x_rect = [0, brick_length, brick_length, 0, 0]
y_rect = [0, 0, brick_height, brick_height, 0]

# Plot
fig, ax = plt.subplots(figsize=(5, 2))

# Draw rectangle
ax.fill(x_rect, y_rect, edgecolor='black', facecolor='none', linewidth=2)


# triangle_pacthes = []

for x_nodes,y_nodes in triangles:
	vertices = Path([
        (x_nodes[0],y_nodes[0]), 
        (x_nodes[2],y_nodes[2]), 
        (x_nodes[1],y_nodes[1]), 
        (x_nodes[0],y_nodes[0]),
    ])

	ax.add_patch(PathPatch(vertices,fill=False))

    # triangle_pacthes.append()

# Draw triangles
# for tri in triangles:
#     ax.fill(tri[0], tri[1], edgecolor='black', facecolor='none')

# Formatting
ax.set_xlim(0, brick_length)
ax.set_ylim(0, brick_height)
ax.set_xticks([])
ax.set_yticks([])
ax.set_frame_on(False)

plt.show()

# x = numpy.linspace(0, 10, 100)

# y1 = numpy.sin(x) * 2 + 6
# y2 = numpy.sin(x) * 2 + 8 # Upper curve

# fig,ax = plt.subplots(figsize=(8,5))

# ax = fill_pattern(ax,x,y1,y2,color="tan",alpha=0.5,
#     pattern=dict(
#         brick_length=brick_length,brick_height=brick_height,offset_ratio=0.5,facecolor='none',edgecolor='black',lw=1.2
#     ))

# # Adjust limits and labels
# # ax.set_xlim(x.min(),x.max())
# ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
# ax.set_xlabel("X-axis")
# ax.set_ylabel("Y-axis")

# plt.show()