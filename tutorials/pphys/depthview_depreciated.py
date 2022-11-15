import matplotlib.pyplot as plt

import tkinter

import dirsetup

from pphys import loadlas

from pphys import DepthView

filename = "lasfile.las"

ls = loadlas(filename)

print(ls.well)
print(ls.curve)

FS_t = 3600
FS_b = 3700

# ls.ascii = ls.depths(FS_t,FS_b)

# fig = plt.figure()

# axis = fig.add_subplot(111)

# # axis = ls.nanplot(axis)
# # axis = ls.ascii['VSH'].histogram(axis)

# fig.tight_layout()

# plt.show()

root = tkinter.Tk()

dv = DepthView(root)

dv.set_axes(4)

dv.set_subaxes(0,1)
dv.set_subaxes(1,3)
dv.set_subaxes(2,2)
dv.set_subaxes(3,2)

dv.set_lines(0,0,xcol=ls.ascii["VSH"],ycol=ls.ascii.running[0])
dv.set_lines(1,0,xcol=ls.ascii["PHIE"],ycol=ls.ascii.running[0])
dv.set_lines(1,1,xcol=ls.ascii["PHIT"],ycol=ls.ascii.running[0])
dv.set_lines(1,2,xcol=ls.ascii["NGL230986"],ycol=ls.ascii.running[0])
dv.set_lines(2,0,xcol=ls.ascii["bvw"],ycol=ls.ascii.running[0])
dv.set_lines(2,1,xcol=ls.ascii["CBW"],ycol=ls.ascii.running[0])
dv.set_lines(3,0,xcol=ls.ascii["RL4"],ycol=ls.ascii.running[0])
dv.set_lines(3,1,xcol=ls.ascii["RL8"],ycol=ls.ascii.running[0])

dv.set_header()
dv.set_image()

# root.geometry("750x270")

# dv.figure.savefig("filename.png")

# plt.show()

tkinter.mainloop()