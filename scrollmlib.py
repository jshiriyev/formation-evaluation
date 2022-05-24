import tkinter as tk

from matplotlib import pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np

root = tk.Tk()

frame = tk.Frame(root)
frame.pack(side=tk.TOP,fill=tk.BOTH,expand=1)

figure = plt.Figure(figsize=(4,64))

axis = figure.add_subplot(1,1,1)

xaxis = np.random.random(500)
yaxis = np.arange(500)

axis.plot(xaxis,yaxis)
##axis.figure.set_size_inches(4,400)


canvas = tk.Canvas(frame)
canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

scrollbar = tk.Scrollbar(frame) #,orient=tk.VERTICAL
scrollbar.pack(side=tk.LEFT,fill=tk.Y)

canvas.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=canvas.yview)



figagg = FigureCanvasTkAgg(figure,canvas)
canagg = figagg.get_tk_widget()

##figagg.get_tk_widget().config(width=400,height=1600)
##figagg.get_tk_widget().config(bg="blue",scrollregion=(0,0,400,1600))
##figagg.get_tk_widget().config(yscrollcommand=scrollbar.set)
##figagg.get_tk_widget().pack(side=tk.LEFT,fill=tk.BOTH,expand=tk.Y)

canwin = canvas.create_window(0,0,window=canagg,anchor=tk.constants.NW)

wi,hi = [i*figure.dpi for i in figure.get_size_inches()]

canagg.config(width=wi,height=hi)

canvas.itemconfigure(canwin,width=wi,height=hi)
canvas.config(scrollregion=canvas.bbox(tk.constants.ALL),width=400,height=400)

figure.canvas.draw()

figure.set_tight_layout(True)





tk.mainloop()
