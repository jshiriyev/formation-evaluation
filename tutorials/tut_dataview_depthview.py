import matplotlib.pyplot as plt

import setup

from textio import las

from dataview import DepthView

filename = "tut_dataview_lasfile.las"

log = las(filename)

print(log.curve)

print(log.frame)

# print(log.)

# FS_t = 3670
# FS_b = 3700

# logs.print_well_info(0)
# logs.print_curve_info()

# logs.set_interval(FS_t,FS_b)

# plot = (
#     {"lines":((0,"VSH"),),
#      "ptype":"default"},
#     {"lines":((0,"PHIE"),(0,"PHIT"),(0,"NGL")),
#      "ptype":"default"},
#     {"lines":((0,"BVW"),(0,"CBW")),
#      "ptype":"default",},
#     {"lines":((0,"RL4"),(0,"RL8")),
#      "ptype":"log",},
#     )

# logs.set_axes(plot)
# logs.set_lines(plot)

# # logs.axes[2].subax[0].set_xlim((0,0.30))

# plt.tight_layout()
# plt.show()