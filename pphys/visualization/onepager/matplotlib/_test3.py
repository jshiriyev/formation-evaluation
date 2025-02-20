import matplotlib.pyplot as plt

from matplotlib.hatch import Shapes
from matplotlib.patches import Rectangle
from matplotlib.hatch import _hatch_types

import numpy as np

class SquareHatch(Shapes):
    """
    Square hatch defined by a path drawn inside [-0.5, 0.5] square.
    Identifier 's'.
    """
    def __init__(self, hatch, density):
        self.filled = False
        self.size = 1
        self.path = Rectangle((-0.25, 0.25), 0.5, 0.5).get_path()
        self.num_rows = (hatch.count('brick')) * density
        self.shape_vertices = self.path.vertices
        self.shape_codes = self.path.codes
        Shapes.__init__(self, hatch, density)

# attach our new hatch
_hatch_types.append(SquareHatch)

x = np.linspace(0, 10, 50)
y1 = np.sin(x) * 2 + 8
y2 = np.sin(x) * 2 + 6

fig, ax = plt.subplots(figsize=(8, 6))

ax.plot(x, y1, 'k', linewidth=1.5)
ax.plot(x, y2, 'k', linewidth=1.5)

ax.fill_between(x,y1,y2,hatch='brick')

plt.show()