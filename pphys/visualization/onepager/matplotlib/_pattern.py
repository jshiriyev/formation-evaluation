from matplotlib import pyplot as plt

from matplotlib.patches import PathPatch
from matplotlib.path import Path

import numpy

class Pattern():

    def __init__(self,name:str):
        self.name = name

    def __call__(self,axis:plt.Axes,x:numpy.ndarray,y1:numpy.ndarray,y2:numpy.ndarray,pattern_dict:dict=None,**fill_between:dict):

        # Fill between the curves
        fill = axis.fill_between(x,y1,y2,**fill_between)

        self.x_min = x.min()
        self.x_max = x.max()
        self.y_min = y1.min()
        self.y_max = y2.max()

        pattern_dict = {} if pattern_dict is None else pattern_dict

        # Create and clip the brick pattern
        patches = self.patches(**pattern_dict)

        for patch in patches:
            patch.set_clip_path(
                fill.get_paths()[0],transform=axis.transData
                )  # Clip each brick to the filled region

            axis.add_patch(patch)

        return axis

    def patches(self,length:float=1,height:float=0.5,spacing_ratio:float=1.,offset_ratio:float=0.5,tilting_ratio=0.,**kwargs):
        """Creates individual patches within a bounded region.
        
        Parameters:
        ----------
        length  : length of each pattern figure.
        height  : height of each pattern figure.
        
        spacing_ratio : how much spacing to put between the figures.
        offset_ratio  : how much to horizontally shift every other row (0 = no shift, 0.5 = half length).
        tilting_ratio : how much tilting to use for the ceiling of the figure.
        
        Returns:
        -------
        List of PathPatch objects representing bricks.
        """
        y_nodes = numpy.arange(
            self.y_min-height*(spacing_ratio-1)/2.,
            self.y_max+height*(spacing_ratio-1)/2.,
            height*spacing_ratio
            )

        offset1 = length*(spacing_ratio-1)/2.
        offset2 = length*(spacing_ratio-1)/2.+offset_ratio*length*spacing_ratio

        x_lower = numpy.arange(self.x_min-offset1,self.x_max+offset1,length*spacing_ratio)
        x_upper = numpy.arange(self.x_min-offset2,self.x_max+offset2,length*spacing_ratio)

        patches = []
        
        for y_index,y_node in enumerate(y_nodes):

            x_nodes = x_lower if y_index%2==0 else x_upper
            
            for x_node in x_nodes:

                path = self.path(x_node,y_node,
                    length=length,height=height,tilting_ratio=tilting_ratio)
                
                patches.append(PathPatch(path,**kwargs))
        
        return patches

    def path(self,x_node,y_node,**kwargs):
        """Returns path for the instance figure."""
        x_func,y_func = getattr(self,self.name)(**kwargs)

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

    pattern = Pattern("triangle")

    fig,ax = plt.subplots(figsize=(8,5))

    ax = pattern(ax,x,y1,y2,color="tan",alpha=0.5,
        pattern_dict=dict(
            length=0.8,height=0.2,offset_ratio=0.5,tilting_ratio=0.,spacing_ratio=1.,facecolor='none',edgecolor='black',lw=1.2
        ))

    # Adjust limits and labels
    # ax.set_xlim(x.min(),x.max())
    ax.set_ylim(y1.min(),y2.max()+0.2)  # Extra space for visibility
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")

    plt.show()