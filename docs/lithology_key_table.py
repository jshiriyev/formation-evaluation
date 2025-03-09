import matplotlib.pyplot as plt
import numpy as np

from _weaver import Weaver
from _templix import Lithology

def draw_rectangle(axis,xy,width,height,prop):

    x = np.array((xy[0],xy[0]+width))

    y_min = np.array((xy[1],xy[1]))
    y_max = np.array((xy[1]+height,xy[1]+height))

    axis = Weaver.fill_between(axis,x,y_min,y_max,prop)

    rect = plt.Rectangle(xy,width,height,lw=1.2,edgecolor='black',fill=None)

    axis.add_patch(rect)

    return axis

lithology_dict = {
    "limestone": Lithology.get("limestone"),
    "dolomite": Lithology.get("dolomite"),
    "chert": Lithology.get("chert"),
    "dolomitic limestone": Lithology.get("dolomitic_limestone"),
    "cherty dolomite": Lithology.get("cherty_dolomite"),
    "cherty limestone": Lithology.get("cherty_limestone"),
    "shaly limestone": Lithology.get("shaly_limestone"),
    "shaly dolomite": Lithology.get("shaly_dolomite"),
    "cherty dolomitic limestone": Lithology.get("cherty_dolomitic_limestone"),
    "shale": Lithology.get("shale"),
    "calcareous shale": Lithology.get("calcareous_shale"),
    "dolomitic shale": Lithology.get("dolomitic_shale"),
    "sandstone": Lithology.get("sandstone"),
    "shaly sandstone": Lithology.get("shaly_sandstone"),
    "sandy shale": Lithology.get("sandy_shale"),
    "ironstone": Lithology.get("ironstone"),
    "coal": Lithology.get("coal"),
    "null": dict(),
    "gypsum": Lithology.get("gypsum"),
    "anhydrite": Lithology.get("anhydrite"),
    "halite": Lithology.get("halite"),
}

fig, ax = plt.subplots(figsize=(8, 10))

cols = 3

y_start = len(lithology_dict)//cols

width,height = 1.6,0.4

for index,(lithology,prop) in enumerate(lithology_dict.items()):

    if index==17:
        continue

    y = y_start-index//cols-height

    if index//cols == 5:
        x = (3*(index%cols)+2.5)/2*width
    else:
        x = (3*(index%cols)+1.0)/2*width

    ax = draw_rectangle(ax,(x,y),width,height,prop=prop)

    ax.text(x+width/2,y-0.2,lithology,
        fontweight='bold',fontsize=10,verticalalignment='center',horizontalalignment='center')

plt.title("GRAPHIC LITHOLOGY KEY",fontsize=14,fontweight='bold')

ax.set_xlim(0,5*width)
ax.set_ylim(0,y_start+height)
ax.set_xticks([])
ax.set_yticks([])
# ax.spines['top'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.spines['left'].set_visible(False)
# ax.spines['bottom'].set_visible(False)

plt.show()