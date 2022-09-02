import matplotlib.pyplot as plt

import tkinter

import setup

from textio import las

from dataview import DepthView

filename = "tut_dataview_lasfile.las"

log = las(filename)

print(log.well)
print(log.curve)

FS_t = 3600
FS_b = 3700

column_ = log.depths(FS_t,FS_b,"DEPT")

print(column_.vals)

# fig = plt.figure()

# axis = fig.add_subplot(111)

# # axis = log.nanplot(axis)
# # axis = log.frame['VSH'].histogram(axis)

# fig.tight_layout()

# plt.show()

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

# root = tkinter.Tk()

# las = DepthView(root)

# Y = numpy.arange(5000)*0.1
# X = numpy.random.random(5000)/5

# las.set_axes(2)
# las.set_subaxes(0,3)
# las.set_subaxes(1,3)
# # las.set_subaxes(2,3)
# las.set_lines(0,0,xvals=X,yvals=Y)
# # las.set_lines(1,0,xvals=X,yvals=Y)
# # las.set_lines(1,1,xvals=numpy.random.random(500),yvals=Y)

# las.set_image()

# # root.geometry("750x270")

# tkinter.mainloop()