import matplotlib.pyplot as plt
import numpy as np

def draw_rectangle(ax, xy, width, height, facecolor, edgecolor='black', hatch=None, overlay_color=None, overlay_pattern=None):
    rect = plt.Rectangle(xy, width, height, facecolor=facecolor, edgecolor=edgecolor, hatch=hatch, lw=1.5)
    ax.add_patch(rect)
    
    if overlay_color and overlay_pattern:
        overlay_rect = plt.Rectangle(xy, width, height, facecolor=overlay_color, edgecolor='none', hatch=overlay_pattern, lw=0)
        ax.add_patch(overlay_rect)

lithology_dict = {
    "limestone": {"color": "#2BFFFF", "hatch": "-", "overlay_color": None, "overlay_pattern": None},
    "dolomite": {"color": "#E277E3", "hatch": "\\", "overlay_color": None, "overlay_pattern": None},
    "chert": {"color": "white", "hatch": "^", "overlay_color": None, "overlay_pattern": None},
    "dolomitic limestone": {"color": "#2BFFFF", "hatch": "-", "overlay_color": "#E277E3", "overlay_pattern": "\\"},
    "cherty dolomite": {"color": "#E277E3", "hatch": "\\", "overlay_color": "white", "overlay_pattern": "^"},
    "cherty limestone": {"color": "#2BFFFF", "hatch": "-", "overlay_color": "white", "overlay_pattern": "^"},
    "shaly limestone": {"color": "#2BFFFF", "hatch": "-", "overlay_color": "gray", "overlay_pattern": "-"},
    "shaly dolomite": {"color": "#E277E3", "hatch": "\\", "overlay_color": "gray", "overlay_pattern": "-"},
    "shale": {"color": "gray", "hatch": "-", "overlay_color": None, "overlay_pattern": None},
    "calcareous shale": {"color": "gray", "hatch": "-", "overlay_color": "#2BFFFF", "overlay_pattern": "-"},
    "dolomitic shale": {"color": "gray", "hatch": "-", "overlay_color": "#E277E3", "overlay_pattern": "\\"},
    "sandstone": {"color": "#F4A460", "hatch": "*", "overlay_color": None, "overlay_pattern": None},
    "shaly sandstone": {"color": "#F4A460", "hatch": "*", "overlay_color": "gray", "overlay_pattern": "-"},
    "sandy shale": {"color": "brown", "hatch": "-", "overlay_color": "#F4A460", "overlay_pattern": "*"},
    "ironstone": {"color": "gray", "hatch": None, "overlay_color": "red", "overlay_pattern": "o"},
    "coal": {"color": "black", "hatch": None, "overlay_color": None, "overlay_pattern": None},
    "gypsum": {"color": "#9370DB", "hatch": "\\", "overlay_color": None, "overlay_pattern": None},
    "anhydrite": {"color": "#DAA520", "hatch": "x", "overlay_color": None, "overlay_pattern": None},
    "halite": {"color": "#00FF00", "hatch": "+", "overlay_color": None, "overlay_pattern": None}
}

fig, ax = plt.subplots(figsize=(8, 10))
ax.set_xlim(0, 4)
ax.set_ylim(0, len(lithology_dict))
ax.set_xticks([])
ax.set_yticks([])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

y = len(lithology_dict) - 1
for lithology, props in lithology_dict.items():
    draw_rectangle(ax, (0.5, y), 1, 0.8, facecolor=props['color'], hatch=props['hatch'], 
                   overlay_color=props['overlay_color'], overlay_pattern=props['overlay_pattern'])
    ax.text(2, y + 0.3, lithology, fontsize=10, verticalalignment='center')
    y -= 1.5

plt.title("Graphic Lithology Key", fontsize=14, fontweight='bold')
plt.show()