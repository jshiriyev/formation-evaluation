from matplotlib import pyplot as plt

from matplotlib import colors as mcolors

from matplotlib.patches import PathPatch, Polygon
from matplotlib.path import Path

import numpy as np

from ._templix import PropDict
    
class Pigment():

    @staticmethod
    def fill_solid(axis:plt.Axes,y:np.ndarray,x1:np.ndarray,x2:np.ndarray,prop:PropDict):
        """Fill between the log curves with a solid facecolor, hatches, and motifs.

        For color specification, please check:
        - https://matplotlib.org/stable/tutorials/colors/colors.html

        For list of hatches, please check:
        - https://matplotlib.org/stable/gallery/shapes_and_collections/hatch_style_reference.html

        """
        fill = axis.fill_betweenx(y,x1,x2,facecolor=prop.facecolor,hatch=prop.hatch)

        for motif in prop.motifs:
            # Create the pattern patches
            patches = Pigment.patches(
                x1.min(),x2.max(),y.min(),y.max(),motif
                )

            # Clip the pattern patches
            for patch in patches:
                patch.set_clip_path(
                    fill.get_paths()[0],transform=axis.transData
                    )  # Clip each patch to the filled region

                axis.add_patch(patch)

        return axis

    @staticmethod
    def fill_colormap(axis:plt.Axes,y:np.ndarray,x1:np.ndarray,x2:float=0,colormap='Reds',vmin=None,vmax=None,**kwargs):
        """Fill between the log curves with a given colormap.

        For list of colormaps, please check:
        - https://matplotlib.org/stable/users/explain/colors/colormaps.html

        """
        vmin = np.nanmin(x1) if vmin is None else vmin
        vmax = np.nanmax(x1) if vmax is None else vmax

        x_normalized = mcolors.Normalize(vmin=vmin,vmax=vmax)(x1)

        z = plt.get_cmap(colormap)(x_normalized)
        z = z[:,:,np.newaxis].transpose((0,2,1))

        xmin = np.nanmin(x1) if np.nanmin(x1)<x2 else x2
        xmax = np.nanmax(x1) if np.nanmax(x1)>x2 else x2

        ymin,ymax = np.nanmin(y),np.nanmax(y)

        img = axis.imshow(z,
            aspect = 'auto',
            extent = [xmin,xmax,ymin,ymax],  
            origin = 'lower',**kwargs
            # zorder = line.get_zorder()
            )

        xy = np.column_stack([x1,y])
        xy = np.vstack([[x2,ymin],xy,[x2,ymax],[x2,ymin]])
        xy = xy[~np.isnan(xy).any(axis=1)]

        clip = Polygon(xy,facecolor='none',edgecolor='none',closed=True)
        axis.add_patch(clip)

        img.set_clip_path(clip)

        return axis

    @staticmethod
    def patches(x_min,x_max,y_min,y_max,motif):
        """Creates individual patches within a bounded region. Returns list of PathPatch objects."""
        offsety = (motif.height_extern-motif.height)/2.

        y_nodes = np.arange(y_min+offsety,y_max,motif.height_extern)

        offset1 = motif.length*(motif.length_ratio-1)/2.
        offset2 = motif.length*motif.offset_ratio

        x_lower = np.arange(x_min+offset1,x_max,motif.length_extern)
        x_upper = np.arange(x_min-offset2,x_max,motif.length_extern)

        patches = []
        
        for y_index,y_node in enumerate(y_nodes):

            x_nodes = x_lower if y_index%2==0 else x_upper
            
            for x_node in x_nodes:

                path = Pigment.path(x_node,y_node,motif)
                
                patches.append(PathPatch(path,**motif.params))
        
        return patches

    def path(x_node,y_node,motif):
        """Returns path for the instance figure."""
        element = getattr(Pigment,motif.element)

        x_func,y_func = element(length=motif.length,height=motif.height,tilted_ratio=motif.tilted_ratio)

        if motif.element == "circle":
            return Path.circle((x_func(x_node),y_func(y_node)),radius=motif.radius)
        
        return Path([(x,y) for x,y in zip(x_func(x_node),y_func(y_node))])

    @staticmethod
    def circle(length=0.2,height=0.2,**kwargs):
        """Returns functions that calculates center coordinates for the given lower left corner."""
        x_func = lambda x: x+np.sqrt(length*height)/2
        y_func = lambda y: y+np.sqrt(length*height)/2

        return x_func,y_func

    @staticmethod
    def line(length=0.2,height=0.1,**kwargs):
        """Returns functions that calculates line vertex coordinates for the given lower left corner."""
        x_func = lambda x: [x, x+length]
        y_func = lambda y: [y, y+height]

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

    import np as np

    from _templix import PropDict
    from _motifs import MotifPattern

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
    ax = Pigment.fill_between(ax,x,y1,y2,prop=prop)

    # Adjust limits and labels
    # ax.set_xlim(x.min(),x.max())
    ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()