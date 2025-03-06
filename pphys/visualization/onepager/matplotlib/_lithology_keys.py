import matplotlib.pyplot as plt
import numpy as np

from _pattern import Pattern

def draw_rectangle(axis,xy,width,height,facecolor,edgecolor='black',hatch=None,pattern_dict:dict=None,**kwargs):

    if hatch in ("brick","triangle"):

        # rect = plt.Rectangle(xy,width,height,edgecolor=edgecolor,lw=2.0,
        #     fill=False)

        # axis.add_patch(rect)

        pattern = Pattern(hatch)

        x = np.array((xy[0],xy[0]+width))

        y_min = np.array((xy[1],xy[1]))
        y_max = np.array((xy[1]+height,xy[1]+height))

        axis = pattern(axis,x,y_min,y_max,facecolor=facecolor,
            pattern_dict=pattern_dict,**kwargs)

    else:

        rect = plt.Rectangle(xy,width,height,edgecolor=edgecolor,lw=1.5,
            facecolor=facecolor,hatch=hatch)

        axis.add_patch(rect)

    return axis

limestone = dict(
    color="#2BFFFF",hatch="brick",length=0.8,height=0.2,offset_ratio=0.5,tilting_ratio=0.,
    spacing_ratio=1.,facecolor='none',edgecolor='black',lw=1.2
    )

dolomite = dict(
    color="#E277E3",hatch="brick",length=0.8,height=0.2,offset_ratio=0.5,tilting_ratio=0.25,
    spacing_ratio=1.,facecolor='none',edgecolor='black',lw=1.2
    )

chert = dict(
    color="white",hatch="triangle",length=0.6/4,height=0.3/4,offset_ratio=0.5,tilting_ratio=0.,
    spacing_ratio=2.,facecolor='none',edgecolor='black',lw=1.0
    )

dolomitic_limestone = dict(color="#2BFFFF",hatch=None)

cherty_dolomite = dict(color="#E277E3", hatch="brick",length=0.8,height=0.2)
cherty_limestone = dict(color="#2BFFFF", hatch="brick",length=0.8,height=0.2)
shaly_limestone = dict(color="#2BFFFF", hatch="brick",length=0.8,height=0.2)
shaly_dolomite = dict(color="#E277E3", hatch="brick",length=0.8,height=0.2)

cherty_dolomitic_limestone = dict(color="#E277E3",hatch=None)
shale = dict(color="gray", hatch= None)
calcareous_shale = dict(color="gray", hatch= None)
dolomitic_shale = dict(color="gray", hatch= None)
sandstone = dict(color="#F4A460", hatch= "...")
shaly_sandstone = dict(color="#F4A460", hatch= "...")
sandy_shale = dict(color="brown", hatch= None)
ironstone = dict(color="gray", hatch= 'O')
coal = dict(color="black", hatch= None)
null = dict()
gypsum = dict(color="#9370DB", hatch= "\\\\")
anhydrite = dict(color="#DAA520", hatch= "xx")
halite = dict(color="#00FF00", hatch= "+")

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
    "null": null,
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

    ax = draw_rectangle(ax,(x,y),width,height,facecolor=props.pop('color'),hatch=props.pop('hatch'),lw=1.5,pattern_dict=props)

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