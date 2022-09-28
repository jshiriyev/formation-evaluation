import matplotlib.pyplot as plt

import tkinter

import dirsetup

from textio import las

from dataview import DepthView

filename = "tut_dataview_lasfile.las"

ls = las(filename)

print(ls.well)
print(ls.curve)

FS_t = 3600
FS_b = 3700

# ls.frame = ls.depths(FS_t,FS_b)

# fig = plt.figure()

# axis = fig.add_subplot(111)

# # axis = ls.nanplot(axis)
# # axis = ls.frame['VSH'].histogram(axis)

# fig.tight_layout()

# plt.show()

root = tkinter.Tk()

dv = DepthView(root)

dv.set_axes(4)

dv.set_subaxes(0,1)
dv.set_subaxes(1,3)
dv.set_subaxes(2,2)
dv.set_subaxes(3,2)

dv.set_lines(0,0,xcol=ls.frame["VSH"],ycol=ls.frame.running[0])
dv.set_lines(1,0,xcol=ls.frame["PHIE"],ycol=ls.frame.running[0])
dv.set_lines(1,1,xcol=ls.frame["PHIT"],ycol=ls.frame.running[0])
dv.set_lines(1,2,xcol=ls.frame["NGL230986"],ycol=ls.frame.running[0])
dv.set_lines(2,0,xcol=ls.frame["bvw"],ycol=ls.frame.running[0])
dv.set_lines(2,1,xcol=ls.frame["CBW"],ycol=ls.frame.running[0])
dv.set_lines(3,0,xcol=ls.frame["RL4"],ycol=ls.frame.running[0])
dv.set_lines(3,1,xcol=ls.frame["RL8"],ycol=ls.frame.running[0])

dv.set_image()

# root.geometry("750x270")

# dv.figure.savefig("filename.png")

tkinter.mainloop()