import matplotlib.pyplot as plt
import numpy as np

from _pattern import PatternBuilder

def draw_rectangle(axis,xy,width,height,patch:dict=None):

    x = np.array((xy[0],xy[0]+width))

    y_min = np.array((xy[1],xy[1]))
    y_max = np.array((xy[1]+height,xy[1]+height))

    axis = PatternBuilder.fill_between(axis,x,y_min,y_max,patch=patch)

    rect = plt.Rectangle(xy,width,height,lw=1.2,edgecolor='black',fill=None)

    axis.add_patch(rect)

    return axis

lithology_dict = {
    "limestone": limestone,
    "dolomite": dolomite,
    "chert": chert,
    "dolomitic limestone": dolomitic_limestone,
    "cherty dolomite": cherty_dolomite,
    "cherty limestone": cherty_limestone,
    "shaly limestone": shaly_limestone,
    "shaly dolomite": shaly_dolomite,
    "cherty dolomitic limestone": cherty_dolomitic_limestone,
    "shale": shale,
    "calcareous shale": calcareous_shale,
    "dolomitic shale": dolomitic_shale,
    "sandstone": sandstone,
    "shaly sandstone": shaly_sandstone,
    "sandy shale": sandy_shale,
    "ironstone": ironstone,
    "coal": coal,
    "null": dict(),
    "gypsum": gypsum,
    "anhydrite": anhydrite,
    "halite": halite
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

    ax = draw_rectangle(ax,(x,y),width,height,patch=props)

    # if index==5:
    #     ax = draw_rectangle(ax,(x,y),width,height,patch=lithology_dict['chert'])

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