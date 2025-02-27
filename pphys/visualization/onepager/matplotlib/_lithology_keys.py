import matplotlib.pyplot as plt
import numpy as np

from _brick_pattern import brick_patches

def draw_rectangle(axis,xy,width,height,facecolor,edgecolor='black',hatch=None):

    if hatch=="brick":

        rect = plt.Rectangle(xy,width,height,fill=False,edgecolor=edgecolor,lw=1.5)

        fill = axis.fill_between((xy[0],xy[0]+width),(xy[1],xy[1]),(xy[1]+height,xy[1]+height),facecolor=facecolor)

        patches = brick_patches(xy[0],xy[0]+2*0.8,xy[1],xy[1]+2*0.2,brick_width=0.8,brick_height=0.2,offset_ratio=0.5)

        for patch in patches:
            patch.set_clip_path(fill.get_paths()[0],transform=axis.transData)
            axis.add_patch(patch)

        axis.add_patch(rect)

    elif hatch=="baklava":

        rect = plt.Rectangle(xy,width,height,fill=None,edgecolor=edgecolor,lw=1.5)

        fill = axis.fill_between((xy[0],xy[0]+width),(xy[1],xy[1]),(xy[1]+height,xy[1]+height),facecolor=facecolor)

        patches = brick_patches(xy[0]-0.8,xy[0]+3*0.8,xy[1],xy[1]+2*0.2,brick_width=0.8,brick_height=0.2,offset_ratio=0.7,tilt_ratio=0.25)

        for patch in patches:
            patch.set_clip_path(fill.get_paths()[0],transform=axis.transData)
            axis.add_patch(patch)

        axis.add_patch(rect)

    else:

        rect = plt.Rectangle(xy,width,height,
            facecolor=facecolor,edgecolor=edgecolor,hatch=hatch,lw=1.5)

        axis.add_patch(rect)

    return axis

lithology_dict = {
    "limestone": {"color": "#2BFFFF", "hatch": "brick"},
    "dolomite": {"color": "#E277E3", "hatch": "baklava"},
    "chert": {"color": "white", "hatch": None},
    "dolomitic limestone": {"color": "#2BFFFF", "hatch": None},
    "cherty dolomite": {"color": "#E277E3", "hatch": "baklava"},
    "cherty limestone": {"color": "#2BFFFF", "hatch": "brick"},
    "shaly limestone": {"color": "#2BFFFF", "hatch": "brick"},
    "shaly dolomite": {"color": "#E277E3", "hatch": "baklava"},
    "cherty dolomitic limestone": {"color": "#E277E3","hatch":None},
    "shale": {"color": "gray", "hatch": None},
    "calcareous shale": {"color": "gray", "hatch": None},
    "dolomitic shale": {"color": "gray", "hatch": None},
    "sandstone": {"color": "#F4A460", "hatch": "..."},
    "shaly sandstone": {"color": "#F4A460", "hatch": "..."},
    "sandy shale": {"color": "brown", "hatch": None},
    "ironstone": {"color": "gray", "hatch": 'O'},
    "coal": {"color": "black", "hatch": None},
    "null": {},
    "gypsum": {"color": "#9370DB", "hatch": "\\\\"},
    "anhydrite": {"color": "#DAA520", "hatch": "xx"},
    "halite": {"color": "#00FF00", "hatch": "+"}
}

fig, ax = plt.subplots(figsize=(8, 10))

cols = 3

y_start = len(lithology_dict)//cols

width,height = 1.6,0.4

for index,(lithology,props) in enumerate(lithology_dict.items()):

    if index==17:
        continue

    y = y_start-index//cols-height

    if index//cols == 5:
        x = (3*(index%cols)+2.5)/2*width
    else:
        x = (3*(index%cols)+1.0)/2*width

    ax = draw_rectangle(ax,(x,y),width,height,facecolor=props['color'],hatch=props['hatch'])
        # overlay_color=props['overlay_color'],
        # overlay_pattern=props['overlay_pattern']

    ax.text(x+width/2,y-0.2,lithology,
        fontweight='bold',fontsize=10,verticalalignment='center',horizontalalignment='center')

plt.title("GRAPHIC LITHOLOGY KEY",fontsize=14,fontweight='bold')

ax.set_xlim(0,5*width)
ax.set_ylim(0,y_start+height)
# ax.set_xticks([])
# ax.set_yticks([])
# ax.spines['top'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.spines['left'].set_visible(False)
# ax.spines['bottom'].set_visible(False)

plt.show()