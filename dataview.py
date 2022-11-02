import io

import logging

import os

import tkinter

from ttkwidgets.autocomplete import AutocompleteEntryListbox

from matplotlib import gridspec
from matplotlib import pyplot
from matplotlib import transforms

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import LogFormatter
from matplotlib.ticker import LogFormatterExponent
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.ticker import NullLocator
from matplotlib.ticker import ScalarFormatter

import numpy

from PIL import ImageTk, Image

if __name__ == "__main__":
    import dirsetup

# Main Visualizers

class TimeView():

    legendpos = (
        "best","right",
        "upper left","upper center","upper right",
        "lower left","lower center","lower right",
        "center left","center","center right",
        )

    drawstyles = (
        'default','steps','steps-pre','steps-mid','steps-post',
        )

    linestyles = (
        ('-',    "solid line"),
        ('--',   "dashed line"),
        ('-.',   "dash dot line"),
        (':',    "dotted line"),
        (None,   "None Line"),
        (' ',    "Empty Space"),
        ('',     "Empty String"),
        )

    markers = (
        (None, "no marker"),
        ('.',  "point marker"),
        (',',  "pixel marker"),
        ('o',  "circle marker"),
        ('v',  "triangle down marker"),
        ('^',  "triangle up marker"),
        ('<',  "triangle left marker"),
        ('>',  "triangle right marker"),
        ('1',  "tri down marker"),
        ('2',  "tri up marker"),
        ('3',  "tri left marker"),
        ('4',  "tri right marker"),
        ('s',  "square marker"),
        ('p',  "pentagon marker"),
        ('*',  "star marker"),
        ('h',  "hexagon1 marker"),
        ('H',  "hexagon2 marker"),
        ('+',  "plus marker"),
        ('x',  "saltire marker"),
        ('D',  "diamond marker"),
        ('d',  "thin diamond marker"),
        ('|',  "vline marker"),
        ('_',  "hline marker"),
        )

    linecolors = (
        ('b', "blue"),
        ('g', "green"),
        ('r', "red"),
        ('c', "cyan"),
        ('m', "magenta"),
        ('y', "yellow"),
        ('k', "black"),
        ('w', "white"),
        )

    template0 = {
        "name": "Standard",
        #
        "subplots": [1,1],
        "title": [""],
        "twinx": [False],
        "xlabel": ["x-axis"],
        "ylabel": ["y-axis"],
        "legends": [True],
        "xticks": [None],
        "yticks": [None],
        "grid": [True],
        #
        "sublines": [[3]],
        "xaxes": [[(0,1),(0,1),(0,1)]],
        "yaxes": [[(0,2),(0,3),(0,4)]],
        "colors": [[6,0,2]],
        "markers": [[0,0,0]],
        "linestyles": [[0,1,0]],
        "drawstyles": [[0,0,0]],
        }

    template1 = {
        "name": "Standard-dual horizontal stack",
        #
        "subplots": [1,2],
        "twinx": [False,False],
        "title": ["Left","Right"],
        "xlabel": ["x-axis","x-axis"],
        "ylabel": ["y-axis","y-axis"],
        "legends": [True,True],
        "xticks": [None,None],
        "yticks": [None,None],
        "grid": [True,True],
        #
        "sublines": [[1],[2]],
        "xaxes": [[(0,1)],[(0,1),(0,1)]],
        "yaxes": [[(0,2)],[(0,3),(0,4)]],
        "colors": [[6],[0,2]],
        "markers": [[0],[0,0]],
        "linestyles": [[0],[0,0]],
        "drawstyles": [[0],[0,0]],
        }

    template2 = {
        "name": "Standard-dual vertical stack",
        #
        "subplots": [2,1],
        "twinx": [False,False],
        "title": ["Top","Bottom"],
        "xlabel": ["x-axis","x-axis"],
        "ylabel": ["y-axis","y-axis"],
        "legends": [True,True],
        "xticks": [None,None],
        "yticks": [None,None],
        "grid": [True,True],
        #
        "sublines": [[1],[2]],
        "xaxes": [[(0,1)],[(0,1),(0,1)]],
        "yaxes": [[(0,2)],[(0,3),(0,4)]],
        "colors": [[6],[0,2]],
        "markers": [[0],[0,0]],
        "linestyles": [[0],[0,0]],
        "drawstyles": [[4],[0,0]],
        }

    template3 = {
        "name": "Standard-quadruple",
        #
        "subplots": [2,2],
        "twinx": [False,False,False,False],
        "title": ["NW","NE","SW","SE"],
        "xlabel": ["x-axis","x-axis","x-axis","x-axis"],
        "ylabel": ["y-axis","y-axis","y-axis","y-axis"],
        "legends": [True,True,True,False],
        "xticks": [None,None,None,None],
        "yticks": [None,None,None,None],
        "grid": [True,True,True,True],
        #
        "sublines": [[1],[1],[1],[0]],
        "xaxes": [[(0,1)],[(0,1)],[(0,1)],[]],
        "yaxes": [[(0,2)],[(0,3)],[(0,4)],[]],
        "colors": [[6],[0],[2],[0]],
        "markers": [[0],[0],[0],[0]],
        "linestyles": [[0],[0],[0],[0]],
        "drawstyles": [[0],[0],[0],[0]],
        }

    templates = (
        template0,template1,template2,template3,
        )

    def __init__(self,window,**kwargs):

        super().__init__(**kwargs)

        self.dirname = os.path.dirname(__file__)

        self.root = window

    def set_plot(self):

        # configuration of window pane
        self.pane_NS = tkinter.ttk.PanedWindow(self.root,orient=tkinter.VERTICAL,width=1000)

        self.frame_body = tkinter.ttk.Frame(self.root,height=450)

        self.pane_NS.add(self.frame_body,weight=1)

        self.footer = tkinter.Listbox(self.root,height=5)

        self.pane_NS.add(self.footer,weight=0)

        self.pane_NS.pack(expand=1,fill=tkinter.BOTH)

        # configuration of top pane
        self.pane_EW = tkinter.ttk.PanedWindow(self.frame_body,orient=tkinter.HORIZONTAL)

        self.frame_side = tkinter.ttk.Frame(self.frame_body)

        self.pane_EW.add(self.frame_side,weight=0)

        self.frame_plot = tkinter.ttk.Frame(self.frame_body)

        self.pane_EW.add(self.frame_plot,weight=1)

        self.pane_EW.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.frame_plot.columnconfigure(0,weight=1)
        self.frame_plot.columnconfigure(1,weight=0)

        self.frame_plot.rowconfigure(0,weight=1)
        self.frame_plot.rowconfigure(1,weight=0)

        self.figure = pyplot.Figure()
        self.canvas = FigureCanvasTkAgg(self.figure,self.frame_plot)

        self.plotbox = self.canvas.get_tk_widget()
        self.plotbox.grid(row=0,column=0,sticky=tkinter.NSEW)        

        self.plotbar = VerticalNavigationToolbar2Tk(self.canvas,self.frame_plot)
        self.plotbar.update()
        self.plotbar.grid(row=0,column=1,sticky=tkinter.N)

        # configuration of top left pane
        self.pane_ns = tkinter.ttk.PanedWindow(self.frame_side,orient=tkinter.VERTICAL,width=300)

        self.itembox = AutocompleteEntryListbox(self.frame_side,height=250,padding=0)

        self.itembox.content = self.itemnames.tolist()
        self.itembox.config(completevalues=self.itembox.content,allow_other_values=True)

        self.itembox.listbox.bind('<<ListboxSelect>>',lambda event: self.set_lines(event))

        self.pane_ns.add(self.itembox,weight=1)

        self.tempbox = tkinter.ttk.Frame(self.frame_side,height=200)

        self.tempbox.rowconfigure(0,weight=0)
        self.tempbox.rowconfigure(1,weight=1)

        self.tempbox.columnconfigure(0,weight=1)
        self.tempbox.columnconfigure(1,weight=0)
        self.tempbox.columnconfigure(2,weight=0)

        self.tempbox.label = tkinter.ttk.Label(self.tempbox,text="Graph Templates")
        self.tempbox.label.grid(row=0,column=0,sticky=tkinter.EW)

        self.tempbox.iconadd = tkinter.PhotoImage(file=os.path.join(self.dirname,"graphics","Add","Add-9.png"))
        self.tempbox.iconedit = tkinter.PhotoImage(file=os.path.join(self.dirname,"graphics","Edit","Edit-9.png"))
        self.tempbox.icondel = tkinter.PhotoImage(file=os.path.join(self.dirname,"graphics","Delete","Delete-9.png"))

        self.tempbox.buttonadd = tkinter.ttk.Button(self.tempbox,image=self.tempbox.iconadd,command=lambda:self.get_template("add"))
        self.tempbox.buttonadd.grid(row=0,column=1)

        self.tempbox.buttonedit = tkinter.ttk.Button(self.tempbox,image=self.tempbox.iconedit,command=lambda:self.get_template("edit"))
        self.tempbox.buttonedit.grid(row=0,column=2)

        self.tempbox.buttondel = tkinter.ttk.Button(self.tempbox,image=self.tempbox.icondel,command=lambda:self.get_template("delete"))
        self.tempbox.buttondel.grid(row=0,column=3)

        self.tempbox.listbox = tkinter.Listbox(self.tempbox,exportselection=False)
        self.tempbox.listbox.grid(row=1,column=0,columnspan=4,sticky=tkinter.NSEW)

        for template in self.templates:
            self.tempbox.listbox.insert(tkinter.END,template.get("name"))

        self.curtemp = {}

        self.tempbox.listbox.bind('<<ListboxSelect>>',lambda event: self.set_axes(event))

        self.pane_ns.add(self.tempbox,weight=1)

        self.pane_ns.pack(expand=1,fill=tkinter.BOTH)

    def set_axes(self,event):

        if not self.tempbox.listbox.curselection():
            return

        if self.curtemp == self.templates[self.tempbox.listbox.curselection()[0]]:
            return
        
        self.curtemp = self.templates[self.tempbox.listbox.curselection()[0]]

        naxrows,naxcols = self.curtemp.get("subplots")

        twinx = self.curtemp.get("twinx")

        self.curtemp["flagMainAxes"] = []

        for flagTwinAxis in twinx:
            self.curtemp["flagMainAxes"].append(True)
            if flagTwinAxis: self.curtemp["flagMainAxes"].append(False)

        if hasattr(self,"axes"):
            self.figure.clear()
            # [self.figure.delaxes(axis) for axis in self.axes]

        self.axes = []

        for index,flagMainAxis in enumerate(self.curtemp.get("flagMainAxes")):

            index_main = sum(self.curtemp.get("flagMainAxes")[:index+1])-1

            if flagMainAxis:
                axis = self.figure.add_subplot(naxrows,naxcols,index_main+1)
            else:
                axis = self.axes[-1].twinx()
                
            if flagMainAxis and self.curtemp.get("title")[index_main] is not None:
                axis.set_title(self.curtemp.get("title")[index_main])

            if flagMainAxis and self.curtemp.get("xlabel")[index_main] is not None:
                axis.set_xlabel(self.curtemp.get("xlabel")[index_main])

            if self.curtemp.get("ylabel")[index] is not None:
                axis.set_ylabel(self.curtemp.get("ylabel")[index])

            if flagMainAxis and self.curtemp.get("xticks")[index_main] is not None:
                axis.set_xticks(self.curtemp.get("xticks")[index_main])

            if self.curtemp.get("yticks")[index] is not None:
                axis.set_yticks(self.curtemp.get("yticks")[index])

            if flagMainAxis and self.curtemp.get("grid")[index_main] is not None:
                axis.grid(self.curtemp.get("grid")[index_main])

            self.axes.append(axis)

            # for tick in axis0.get_xticklabels():
            #     tick.set_rotation(45)

        status = "{} template has been selected.".format(self.curtemp.get("name"))

        self.footer.insert(tkinter.END,status)
        self.footer.see(tkinter.END)

        self.figure.set_tight_layout(True)

        self.canvas.draw()

    def set_lines(self,event):

        if self.itembox.listbox.curselection():
            itemname = self.itemnames[self.itembox.listbox.curselection()[0]]
        else:
            return

        if not hasattr(self,"axes"):
            status = "No template has been selected."
            self.footer.insert(tkinter.END,status)
            self.footer.see(tkinter.END)
            return

        for attrname in self.attrnames:
            if hasattr(self,attrname):
                getattr(self,attrname).filter(0,keywords=[itemname],inplace=False)

        if hasattr(self,"lines"):
            [line.remove() for line in self.lines]
                
        self.lines = []

        self.plotbar.update()

        for index,axis in enumerate(self.axes):

            xaxes = self.curtemp.get("xaxes")[index]
            yaxes = self.curtemp.get("yaxes")[index]

            colors = self.curtemp.get("colors")[index]
            markers = self.curtemp.get("markers")[index]
            lstyles = self.curtemp.get("linestyles")[index]
            dstyles = self.curtemp.get("drawstyles")[index]

            for xaxis,yaxis,color,marker,lstyle,dstyle in zip(xaxes,yaxes,colors,markers,lstyles,dstyles):
                line = axis.plot(
                    getattr(self,self.attrnames[xaxis[0]]).running[xaxis[1]],
                    getattr(self,self.attrnames[yaxis[0]]).running[yaxis[1]],
                    color=self.linecolors[color][0],
                    marker=self.markers[marker][0],
                    linestyle=self.linestyles[lstyle][0],
                    drawstyle=self.drawstyles[dstyle],
                    label=getattr(self,self.attrnames[yaxis[0]]).headers[yaxis[1]])[0]
                self.lines.append(line)

            # if self.curtemp.get("legends")[index]:
            #     axis.legend()

            axis.relim()
            axis.autoscale()
            axis.set_ylim(bottom=0,top=None,auto=True)

        self.figure.set_tight_layout(True)

        self.canvas.draw()

    def get_template(self,manipulation):

        if manipulation=="add":

            self.curtemp = {# when creating a template
                "name": "",
                "subplots": [1,1],
                "title": [""],
                "twinx": [False],
                "xlabel": [""],
                "ylabel": [""],
                "legends": [False],
                "xticks": [None],
                "yticks": [None],
                "grid": [False],
                #
                "sublines": [[0]],
                "xaxes": [[]],
                "yaxes": [[]],
                "colors": [[]],
                "markers": [[]],
                "linestyles": [[]],
                "drawstyles": [[]],
                }

            self.set_temptop("add") # when adding a new one

        elif manipulation=="edit":

            if not self.tempbox.listbox.curselection(): return # when editing

            self.curtemp = self.templates[self.tempbox.listbox.curselection()[0]] # when editing
            self.set_temptop(tempid=self.tempbox.listbox.curselection()[0]) # editing the existing one
            
        elif manipulation=="delete":
            # deleting a template

            if not self.tempbox.listbox.curselection(): return

            name = self.tempbox.listbox.get(self.tempbox.listbox.curselection())

            item = self.curtemp.get("name").index(name)
            
            self.tempbox.listbox.delete(item)

            self.curtemp.get("name").pop(item)
            # self.curtemp.get("naxrows").pop(item)
            # self.curtemp.get("naxcols").pop(item)

    def set_temptop(self,manipulation,tempid=None):

        if hasattr(self,"temptop"):
            if self.temptop.winfo_exists(): return

        if tempid is not None:
            curtemp = self.templates[tempid]
        else:
            curtemp = {"subplots": [1,1]}
            curtemp["sublines"] = [[1,0]]

        self.temptop = tkinter.Toplevel()

        self.temptop.title("Template Editor")

        self.temptop.geometry("700x450")

        self.temptop.resizable(0,0)

        self.style = tkinter.ttk.Style(self.temptop)

        self.style.configure("TNotebook.Tab",width=15,anchor=tkinter.CENTER)

        self.tempedit = tkinter.ttk.Notebook(self.temptop)

        # General Properties

        self.tempeditgeneral = tkinter.Frame(self.tempedit)

        self.tempeditgeneral0 = tkinter.Frame(self.tempeditgeneral,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditgeneral0.templabel = tkinter.ttk.Label(self.tempeditgeneral0,text="Settings")
        self.tempeditgeneral0.templabel.grid(row=0,column=0,columnspan=2,sticky=tkinter.W,padx=(10,10),pady=(2,2))

        self.tempeditgeneral0.tempnamelabel = tkinter.ttk.Label(self.tempeditgeneral0,text="Template Name")
        self.tempeditgeneral0.tempnamelabel.grid(row=1,column=0,sticky=tkinter.E,padx=(10,10),pady=(2,2))

        self.tempeditgeneral0.tempname = tkinter.ttk.Entry(self.tempeditgeneral0,width=30)
        self.tempeditgeneral0.tempname.grid(row=1,column=1,padx=(0,20),pady=(2,2),sticky=tkinter.EW)

        self.tempeditgeneral0.tempname.focus()

        self.tempeditgeneral0.legendLabel = tkinter.ttk.Label(self.tempeditgeneral0,text="Legend Position")
        self.tempeditgeneral0.legendLabel.grid(row=2,column=0,sticky=tkinter.E,padx=(10,10),pady=(2,2))

        self.tempeditgeneral0.legend = tkinter.ttk.Entry(self.tempeditgeneral0,width=30)
        self.tempeditgeneral0.legend.grid(row=2,column=1,padx=(0,20),pady=(2,2),sticky=tkinter.EW)

        self.tempeditgeneral0.pack(side=tkinter.LEFT,expand=0,fill=tkinter.Y)

        self.tempeditgeneral1 = tkinter.Frame(self.tempeditgeneral,borderwidth=2)

        self.tempeditgeneral1.naxlabel = tkinter.ttk.Label(self.tempeditgeneral1,text="Number of Axes")
        self.tempeditgeneral1.naxlabel.grid(row=0,column=0,columnspan=2,sticky=tkinter.EW,padx=(10,2),pady=(2,2))

        self.tempeditgeneral1.naxrowslabel = tkinter.ttk.Label(self.tempeditgeneral1,text="Rows")
        self.tempeditgeneral1.naxrowslabel.grid(row=1,column=0,sticky=tkinter.E,padx=(10,10),pady=(2,2))

        self.tempeditgeneral1.naxval0 = tkinter.StringVar(self.root)
        self.tempeditgeneral1.naxrows = tkinter.ttk.Spinbox(self.tempeditgeneral1,textvariable=self.tempeditgeneral1.naxval0,from_=1,to=5,command=lambda:self.set_temptopdict("rows"))
        self.tempeditgeneral1.naxrows.grid(row=1,column=1,sticky=tkinter.EW,padx=(0,2),pady=(2,2))

        self.tempeditgeneral1.naxcolslabel = tkinter.ttk.Label(self.tempeditgeneral1,text="Columns")
        self.tempeditgeneral1.naxcolslabel.grid(row=2,column=0,sticky=tkinter.E,padx=(10,10),pady=(2,2))

        self.tempeditgeneral1.naxval1 = tkinter.StringVar(self.root)
        self.tempeditgeneral1.naxcols = tkinter.ttk.Spinbox(self.tempeditgeneral1,textvariable=self.tempeditgeneral1.naxval1,from_=1,to=5,command=lambda:self.set_temptopdict("columns"))
        self.tempeditgeneral1.naxcols.grid(row=2,column=1,sticky=tkinter.EW,padx=(0,2),pady=(2,2))

        self.tempeditgeneral1.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)
        
        self.tempedit.add(self.tempeditgeneral,text="General",compound=tkinter.CENTER)

        # Axes Properties

        self.tempeditaxes = tkinter.Frame(self.tempedit)

        self.tempeditaxes0 = tkinter.Frame(self.tempeditaxes,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditaxes0.axislabel = tkinter.ttk.Label(self.tempeditaxes0,text="Axis List")
        self.tempeditaxes0.axislabel.pack(side=tkinter.TOP,fill=tkinter.X)

        self.tempeditaxes0.listbox = tkinter.Listbox(self.tempeditaxes0)

        self.tempeditaxes0.listbox.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH)

        self.tempeditaxes0.pack(side=tkinter.LEFT,expand=0,fill=tkinter.Y)

        self.tempeditaxes1 = tkinter.Frame(self.tempeditaxes,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditaxes1.entry00 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check00 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Draw X Twin",variable=self.tempeditaxes1.entry00,command=lambda:self.set_temptopdict("entry00"))
        self.tempeditaxes1.check00.grid(row=0,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.label01 = tkinter.ttk.Label(self.tempeditaxes1,text="Title")
        self.tempeditaxes1.label01.grid(row=1,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.entry01 = tkinter.ttk.Entry(self.tempeditaxes1)
        self.tempeditaxes1.entry01.grid(row=1,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.label02 = tkinter.ttk.Label(self.tempeditaxes1,text="X Label")
        self.tempeditaxes1.label02.grid(row=2,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.entry02 = tkinter.ttk.Entry(self.tempeditaxes1)
        self.tempeditaxes1.entry02.grid(row=2,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.label03 = tkinter.ttk.Label(self.tempeditaxes1,text="Y-1 Label")
        self.tempeditaxes1.label03.grid(row=3,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.entry03 = tkinter.ttk.Entry(self.tempeditaxes1,state=tkinter.NORMAL)
        self.tempeditaxes1.entry03.grid(row=3,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.label04 = tkinter.ttk.Label(self.tempeditaxes1,text="Y-2 Label",state=tkinter.DISABLED)
        self.tempeditaxes1.label04.grid(row=4,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.entry04 = tkinter.ttk.Entry(self.tempeditaxes1,state=tkinter.DISABLED)
        self.tempeditaxes1.entry04.grid(row=4,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.entry05 = tkinter.StringVar(self.root)
        self.tempeditaxes1.label05 = tkinter.ttk.Label(self.tempeditaxes1,text="Y-1 Lines")
        self.tempeditaxes1.label05.grid(row=5,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.spinb05 = tkinter.ttk.Spinbox(self.tempeditaxes1,to=20,textvariable=self.tempeditaxes1.entry05,command=lambda:self.set_temptopdict("entry05"))
        self.tempeditaxes1.spinb05.grid(row=5,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.entry06 = tkinter.StringVar(self.root)
        self.tempeditaxes1.label06 = tkinter.ttk.Label(self.tempeditaxes1,text="Y-2 Lines",state=tkinter.DISABLED)
        self.tempeditaxes1.label06.grid(row=6,column=0,sticky=tkinter.EW,padx=(30,),pady=(4,))
        self.tempeditaxes1.spinb06 = tkinter.ttk.Spinbox(self.tempeditaxes1,to=20,textvariable=self.tempeditaxes1.entry06,command=lambda:self.set_temptopdict("entry06"),state=tkinter.DISABLED)
        self.tempeditaxes1.spinb06.grid(row=6,column=1,sticky=tkinter.EW,padx=(0,10),pady=(4,))

        self.tempeditaxes1.entry07 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check07 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show Legends",variable=self.tempeditaxes1.entry07)
        self.tempeditaxes1.check07.grid(row=7,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.entry08 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check08 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show X Ticks",variable=self.tempeditaxes1.entry08)
        self.tempeditaxes1.check08.grid(row=8,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.entry09 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check09 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show Y-1 Ticks",variable=self.tempeditaxes1.entry09)
        self.tempeditaxes1.check09.grid(row=9,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.entry10 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check10 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show Y-2 Ticks",variable=self.tempeditaxes1.entry10,state=tkinter.DISABLED)
        self.tempeditaxes1.check10.grid(row=10,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.entry11 = tkinter.IntVar(self.root)
        self.tempeditaxes1.check11 = tkinter.ttk.Checkbutton(self.tempeditaxes1,text="Show Grids",variable=self.tempeditaxes1.entry11)
        self.tempeditaxes1.check11.grid(row=11,column=0,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditaxes1.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.tempedit.add(self.tempeditaxes,text="Axes",compound=tkinter.CENTER)

        # Line Properties

        self.tempeditlines = tkinter.Frame(self.tempedit)

        self.tempeditlines0 = tkinter.Frame(self.tempeditlines,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditlines0.axislabel = tkinter.ttk.Label(self.tempeditlines0,text="Axis List")
        self.tempeditlines0.axislabel.pack(side=tkinter.TOP,fill=tkinter.X)

        self.tempeditlines0.listbox = tkinter.Listbox(self.tempeditlines0)

        self.tempeditlines0.listbox.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH)

        self.tempeditlines0.pack(side=tkinter.LEFT,expand=0,fill=tkinter.Y)

        self.tempeditlines1 = tkinter.Frame(self.tempeditlines,borderwidth=2,relief=tkinter.GROOVE)

        self.tempeditlines1.line1label = tkinter.ttk.Label(self.tempeditlines1,text="Y-1 Lines")
        self.tempeditlines1.line1label.pack(side=tkinter.TOP,fill=tkinter.X)

        self.tempeditlines1.listbox1 = tkinter.Listbox(self.tempeditlines1)

        self.tempeditlines1.listbox1.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH)

        self.tempeditlines1.line2label = tkinter.ttk.Label(self.tempeditlines1,text="Y-2 Lines")
        self.tempeditlines1.line2label.pack(side=tkinter.TOP,fill=tkinter.X)

        self.tempeditlines1.listbox2 = tkinter.Listbox(self.tempeditlines1)

        self.tempeditlines1.listbox2.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH)

        self.tempeditlines1.pack(side=tkinter.LEFT,expand=0,fill=tkinter.Y)

        self.tempeditlines2 = tkinter.Frame(self.tempeditlines)

        self.tempeditlines2.label = tkinter.ttk.Label(self.tempeditlines2,text="Line Details")
        self.tempeditlines2.label.grid(row=0,column=0,columnspan=2,sticky=tkinter.W,padx=(10,),pady=(4,))

        self.tempeditlines2.label0 = tkinter.ttk.Label(self.tempeditlines2,text="X-axis")
        self.tempeditlines2.label0.grid(row=1,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.label1 = tkinter.ttk.Label(self.tempeditlines2,text="Y-axis")
        self.tempeditlines2.label1.grid(row=2,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.label2 = tkinter.ttk.Label(self.tempeditlines2,text="Draw Style")
        self.tempeditlines2.label2.grid(row=3,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.label3 = tkinter.ttk.Label(self.tempeditlines2,text="Line Style")
        self.tempeditlines2.label3.grid(row=4,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.label4 = tkinter.ttk.Label(self.tempeditlines2,text="Line Color")
        self.tempeditlines2.label4.grid(row=5,column=0,sticky=tkinter.E,padx=(10,),pady=(2,))

        self.tempeditlines2.val0 = tkinter.StringVar(self.tempeditlines2)
        self.tempeditlines2.val1 = tkinter.StringVar(self.tempeditlines2)
        self.tempeditlines2.val2 = tkinter.StringVar(self.tempeditlines2)
        self.tempeditlines2.val3 = tkinter.StringVar(self.tempeditlines2)
        self.tempeditlines2.val4 = tkinter.StringVar(self.tempeditlines2)

        self.tempeditlines2.menu0 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val0,"Select Attribute",*self.attrnames)
        self.tempeditlines2.menu0.grid(row=1,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.menu1 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val1,"Select Attribute",*self.attrnames)
        self.tempeditlines2.menu1.grid(row=2,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.menu2 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val2,"Select Style",*self.drawstyles)
        self.tempeditlines2.menu2.grid(row=3,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.menu3 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val3,"Select Style",*self.linestyles)
        self.tempeditlines2.menu3.grid(row=4,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.menu4 = tkinter.ttk.OptionMenu(
            self.tempeditlines2,self.tempeditlines2.val4,"Select Color",*self.linecolors)
        self.tempeditlines2.menu4.grid(row=5,column=1,sticky=tkinter.EW,padx=(10,),pady=(4,))

        self.tempeditlines2.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.tempedit.add(self.tempeditlines,text="Lines",compound=tkinter.CENTER)

        self.tempedit.pack(side=tkinter.TOP,expand=1,fill=tkinter.BOTH,padx=(0,1))

        buttonname = "Add Template" if tempid is None else "Edit Template"

        self.temptop.button = tkinter.ttk.Button(self.temptop,text=buttonname,width=20,command=lambda: self.temptopapply(tempid))
        self.temptop.button.pack(side=tkinter.TOP,expand=1,anchor=tkinter.E,padx=(0,1),pady=(1,1))

        self.temptop.button.bind('<Return>',lambda event: self.temptopapply(tempid,event))

        self.temptop.mainloop()

    def set_temptopdict(self):
        pass
        # self.tempeditgeneral0.tempname.insert(0,curtemp.get("name"))
        # naxrows,naxcols = self.curtemp.get("subplots")

        # self.tempeditgeneral1.naxrows.insert(0,naxrows)
        # self.tempeditgeneral1.naxcols.insert(0,naxcols)

        # for index in range(naxrows*naxcols):
        #     self.tempeditaxes0.listbox.insert(tkinter.END,"Axis {}".format(index))
        #     self.tempeditlines0.listbox.insert(tkinter.END,"Axis {}".format(index))

        # self.tempeditaxes1.entry00.set(self.curtemp.get("twinx")[0])
        # self.tempeditaxes1.entry01.set(self.curtemp.get("title")[0])
        # self.tempeditaxes1.enrty02.set(self.curtemp.get("xlabel")[0])
        # self.tempeditaxes1.enrty03.set(self.curtemp.get("ylabel")[0])
        # self.tempeditaxes1.enrty04.set(self.curtemp.get("ylabel")[1])
        # self.tempeditaxes1.entry05.set(self.curtemp.get("sublines")[0])
        # self.tempeditaxes1.entry06.set(self.curtemp.get("sublines")[1])
        # self.tempeditaxes1.entry07.set(self.curtemp.get("legends")[0])
        # self.tempeditaxes1.entry08.set(self.curtemp.get("xticks")[0])
        # self.tempeditaxes1.entry09.set(self.curtemp.get("yticks")[0])
        # self.tempeditaxes1.entry10.set(self.curtemp.get("yticks")[1])
        # self.tempeditaxes1.entry11.set(self.curtemp.get("grids")[0])

        # for index in range(curtemp.get("sublines")[0][0]):
        #     self.tempeditlines1.listbox1.insert(tkinter.END,"Line {}".format(index))

        # for index in range(curtemp.get("sublines")[0][1]):
        #     self.tempeditlines1.listbox2.insert(tkinter.END,"Line {}".format(index))

        # self.tempeditlines2.val0.set(self.headers[self.curtemp.get("xaxes")[0][0]])
        # self.tempeditlines2.val1.set(self.headers[self.curtemp.get("yaxes")[0][0]])
        # self.tempeditlines2.val2.set(self.drawstyles[self.curtemp.get("drawstyles")[0][0]])
        # self.tempeditlines2.val3.set(self.linestyles[self.curtemp.get("linestyles")[0][0]])
        # self.tempeditlines2.val4.set(self.linecolors[self.curtemp.get("linecolors")[0][0]])

    def set_temptopedits(self,input_):

        if input_=="rows" or input_=="columns":
            numx = self.tempeditgeneral1.naxval0.get()
            numy = self.tempeditgeneral1.naxval1.get()
            numx = int(numx) if numx else 1
            numy = int(numy) if numy else 1
            numa = numx*numy
            if numa>len(self.tempeditaxes0.listbox.get(0,tkinter.END)):
                self.tempeditaxes0.listbox.insert(tkinter.END,"Axis {}".format(numa))
                self.tempeditlines0.listbox.insert(tkinter.END,"Axis {}".format(numa))
        elif input_=="entry00":
            if self.tempeditaxes1.entry00.get():
                self.tempeditaxes1.label04.config(state=tkinter.NORMAL)
                self.tempeditaxes1.entry04.config(state=tkinter.NORMAL)
                self.tempeditaxes1.label06.config(state=tkinter.NORMAL)
                self.tempeditaxes1.spinb06.config(state=tkinter.NORMAL)
                self.tempeditaxes1.check10.config(state=tkinter.NORMAL)
            else:
                self.tempeditaxes1.label04.config(state=tkinter.DISABLED)
                self.tempeditaxes1.entry04.config(state=tkinter.DISABLED)
                self.tempeditaxes1.label06.config(state=tkinter.DISABLED)
                self.tempeditaxes1.spinb06.config(state=tkinter.DISABLED)
                self.tempeditaxes1.check10.config(state=tkinter.DISABLED)
        elif input_=="entry05":
            num1 = int(self.tempeditaxes1.entry05.get())
            if num1>len(self.tempeditlines1.listbox1.get(0,tkinter.END)):
                self.tempeditlines1.listbox1.insert(tkinter.END,"Line {}".format(num1))
        elif input_=="entry06":
            num2 = int(self.tempeditaxes1.entry06.get())
            if num2>len(self.tempeditlines1.listbox2.get(0,tkinter.END)):
                self.tempeditlines1.listbox2.insert(tkinter.END,"Line {}".format(num2))

        # if x.isdigit() or x=="":
        #     # print(prop)
        #     return True
        # else:
        #     return False

    def set_template(self,tempid=None,event=None):

        if event is not None and event.widget!=self.temptop.button:
            return

        if tempid is not None:
            names = [name for index,name in enumerate(self.curtemp.get("name")) if index!=tempid]
        else:
            names = self.curtemp.get("name")

        name = self.tempeditgeneral0.tempname.get()

        if name in names:
            tkinter.messagebox.showerror("Error","You have a template with the same name!",parent=self.temptop)
            return
        elif name.strip()=="":
            tkinter.messagebox.showerror("Error","You have not named the template!",parent=self.temptop)
            return

        if tempid is None:
            tempid = len(self.temps.get("names"))
        else:
            self.tempbox.listbox.delete(tempid)
            self.curtemp.get("name").pop(tempid)
            # self.curtemp.get("naxrows").pop(tempid)
            # self.curtemp.get("naxcols").pop(tempid)
        
        self.tempbox.listbox.insert(tempid,name)

        self.curtemp.get("name").insert(tempid,name)

        try:
            naxrows = int(self.tempeditgeneral1.naxrows.get())
        except ValueError:
            naxrows = 1

        # self.curtemp.get("naxrows").insert(tempid,naxrows)

        try:
            naxcols = int(self.tempeditgeneral1.naxcols.get())
        except ValueError:
            naxcols = 1

        # self.curtemp.get("naxcols").insert(tempid,naxcols)

        self.temptop.destroy()

""" DEPTVIEW RELATED EDITS
 1. DepthView should be a frame that can be added to any parent frame.
 2. Axis and line numbers should not be predefined.
 3. Adding axis should not affect previous axes.
 4. Adding line should not affect previous lines.
 5. DepthView should be added to dataview and get dataframe as an input
 6. Depth axis must be unique!
 7. x-axis grids must be the same for the axis on top of each other.
 8. get_xticks() should be working perfectly for both normal and logarithmic scale
 9. set_lines() should be working smoothly
10. set_listbox() should be adding {idfile: mnemonic} to the listbox
"""

class DepthView():

    def __init__(self,root):
        """It initializes the DepthView with listbox and figure canvas."""

        self.root = root

        self.root.title("datum - depth view")

        # The main frame for the listbox

        self.framelist = tkinter.Frame(root,width=31*8)
        self.framelist.pack(side=tkinter.LEFT,fill=tkinter.Y,expand=0)

        self.listbox = tkinter.Listbox(self.framelist,width=31)
        self.listbox.pack(side=tkinter.LEFT,fill=tkinter.BOTH,expand=1)

        # The main frame for the plot canvas

        self.framefigs = tkinter.Frame(root)
        self.framefigs.pack(side=tkinter.LEFT,fill=tkinter.BOTH,expand=1)

        self.canvas = tkinter.Canvas(self.framefigs)

        self.canvas.grid(row=0,column=0,sticky=tkinter.NSEW)

        self.hscroll = tkinter.Scrollbar(self.framefigs,orient=tkinter.HORIZONTAL)
        self.vscroll = tkinter.Scrollbar(self.framefigs,orient=tkinter.VERTICAL)

        self.hscroll.grid(row=1,column=0,sticky=tkinter.EW)
        self.vscroll.grid(row=0,column=1,sticky=tkinter.NS)

        self.framefigs.rowconfigure(0,weight=1)
        self.framefigs.columnconfigure(0,weight=1)

        self.canvas.config(xscrollcommand=self.hscroll.set)
        self.canvas.config(yscrollcommand=self.vscroll.set)

        self.hscroll.config(command=self.canvas.xview)
        self.vscroll.config(command=self.canvas.yview)

        self.canvas.bind_all("<MouseWheel>",self._on_mousewheel)

        # The colors to be used for lines

        # self.colors = ("black","crimson","blue","sienna")
        self.colors = pyplot.rcParams['axes.prop_cycle'].by_key()['color']
        # self.colors.insert(0,"#000000")

    def set_listbox(self):

        pass

    def set_axes(self,numaxes=1,subaxes=None,depth=None,inchdepth=15.,width=3.,height=128.,dpi=100.):
        """Creates the figure and axes and their sub-axes and stores them in the self.axes."""

        # numaxes   : integer
        #            Number of axes in the figure

        # subaxes   : list or tuple of integers
        #            Number of subaxes in each axis

        # depth     : float
        #            Depth of log in meters; every inch will represent inchdepth meter of formation
        #            Default value for inchdepth is 15 meters.

        # inchdepth : float
        #            The depth (meters) to be shown in every inch of the figure

        # width     : float
        #            Width of each axis in inches

        # height    : float
        #            Height of figure in inches

        # dpi       : integer
        #            Resolution of the figure, dots per inches

        self.figure = pyplot.figure(dpi=dpi)

        self.figure.set_figwidth(width*numaxes)

        if depth is None:
            self.figure.set_figheight(height)
        else:
            self.figure.set_figheight(depth/inchdepth)

        self.fgspec = gridspec.GridSpec(1,numaxes)

        self.axes = []

        if subaxes is None:
            subaxes = (1,)*numaxes
        elif not hasattr(subaxes,"__len__"):
            logging.warning(f"Expected subaxes is a list or tuple with the length equal to numaxes; input is {type(subaxes)}")
        elif len(subaxes)!=numaxes:
            logging.warning(f"The length of subaxes should be equal to numaxes; {len(subaxes)} not equal to {numaxes=}")

        for idaxis in range(numaxes):
            self.add_axis(idaxis,subaxes[idaxis])

    def add_axis(self,idaxis,numsubaxes=1):
        """Adds main-axis and its subaxes to the list of self.axes."""

        subaxes = []

        subaxis_main = pyplot.subplot(self.fgspec[idaxis])

        xlims = (0,1)

        ylims = (0,1)

        subaxis_main.set_xticks(numpy.linspace(*xlims,11))
        subaxis_main.set_yticks(ylims)

        subaxis_main.set_ylim(ylims[::-1])

        subaxis_main.yaxis.set_minor_locator(AutoMinorLocator(25))

        subaxis_main.grid(True,which="both",axis='y')

        subaxis_main.grid(True,which="major",axis='x')

        pyplot.setp(subaxis_main.get_xticklabels(),visible=False)
        pyplot.setp(subaxis_main.get_xticklines(),visible=False)

        # pyplot.setp(subaxis_main.xaxis.get_minorticklabels(),visible=False)
        # pyplot.setp(subaxis_main.xaxis.get_minorticklines(),visible=False)

        pyplot.setp(subaxis_main.yaxis.get_minorticklines(),visible=False)
        # subaxis_main.tick_params(axis='y',which='major',length=0)

        if idaxis>0:
            pyplot.setp(subaxis_main.get_yticklabels(),visible=False)

        subaxes.append(subaxis_main)

        self.axes.append(subaxes)

        self.set_subaxes(idaxis,numsubaxes)

    def set_subaxes(self,idaxis,numsubaxes):
        """Creates subaxes and stores them in self.axes."""

        numsubaxes_current = len(self.axes[idaxis])-1

        if numsubaxes_current>=numsubaxes:
            return

        roofpos = 1+0.4*numsubaxes/self.figure.get_figheight()

        self.axes[idaxis][0].spines["top"].set_position(("axes",roofpos))

        for idline in range(numsubaxes_current,numsubaxes):
            self.add_subaxis(idaxis,idline)

    def add_subaxis(self,idaxis,idline):
        """Adds subaxis to the self.axes."""

        axsub = self.axes[idaxis][0].twiny()

        axsub.set_xticks((0.,1.))
        axsub.set_ylim(self.axes[0][0].get_ylim())

        spinepos = 1+0.4*idline/self.figure.get_figheight()

        axsub.spines["top"].set_position(("axes",spinepos))
        axsub.spines["top"].set_color(self.colors[idline])

        axsub.spines["left"].set_visible(False)
        axsub.spines["right"].set_visible(False)
        axsub.spines["bottom"].set_visible(False)

        axsub.tick_params(axis='x',labelcolor=self.colors[idline])

        # self.axes[idaxis][0].yaxis.set_minor_locator(AutoMinorLocator(25))

        # self.axes[idaxis][0].grid(True,which="both",axis='y')

        pyplot.setp(self.axes[idaxis][0].get_xticklabels(),visible=False)
        pyplot.setp(self.axes[idaxis][0].get_xticklines(),visible=False)

        axsub.LineExistFlag = False

        self.set_xaxis(axsub)

        self.axes[idaxis].append(axsub)

    def set_depth(self,depth=None):
        """It will check the depths of axis and set depth which include all depths."""

        for axis in self.axes:
            for axsub in axis:
                axsub.set_ylim(self.axes[0][0].get_ylim())

            # axis[0].yaxis.set_minor_locator(AutoMinorLocator(25))
            # axis[0].grid(True,which="both",axis='y')

    def set_xaxis(self,axis):

        pyplot.setp(axis.xaxis.get_majorticklabels()[1:-1],visible=False)

        pyplot.setp(axis.xaxis.get_majorticklabels()[0],ha="left")
        pyplot.setp(axis.xaxis.get_majorticklabels()[-1],ha="right")

        if not axis.LineExistFlag:

            loffset = transforms.ScaledTranslation(5/72,-5/72,self.figure.dpi_scale_trans)
            
            ltrans = axis.xaxis.get_majorticklabels()[0].get_transform()

            axis.xaxis.get_majorticklabels()[0].set_transform(ltrans+loffset)

            roffset = transforms.ScaledTranslation(-5/72,-5/72,self.figure.dpi_scale_trans)

            rtrans = axis.xaxis.get_majorticklabels()[-1].get_transform()

            axis.xaxis.get_majorticklabels()[-1].set_transform(rtrans+roffset)

        else:

            roffset = transforms.ScaledTranslation(-10/72,0,self.figure.dpi_scale_trans)

            rtrans = axis.xaxis.get_majorticklabels()[-1].get_transform()

            axis.xaxis.get_majorticklabels()[-1].set_transform(rtrans+roffset)

        pyplot.setp(axis.xaxis.get_majorticklines()[2:-1],visible=False)

        pyplot.setp(axis.xaxis.get_majorticklines()[1],markersize=25)
        pyplot.setp(axis.xaxis.get_majorticklines()[-1],markersize=25)

        # axis.xaxis.get_majorticklines()[0].set_markersize(100)

    def set_lines(self,idaxis,idline,xcol,ycol):

        axis = self.axes[idaxis][idline+1]

        axis.plot(xcol.vals,ycol.vals,color=self.colors[idline])

        axis.LineExistFlag = True

        yticks = self.get_yticks(ycol.vals)
        xticks = self.get_xticks(xcol.vals)

        axis.set_xlabel(xcol.head)

        # figheight_temp = (yticks.max()-yticks.min())/128

        # if figheight_temp>self.figure.get_figheight():
        #   self.figure.set_figheight(figheight_temp)

        # figheight = max(self.figure.get_figheight(),figheight_temp)

        axis.set_ylim((yticks.max(),yticks.min()))
        axis.set_yticks(yticks)

        axis.set_xlim((xticks.min(),xticks.max()))
        axis.set_xticks(xticks)

        self.set_xaxis(axis)

        # axis.grid(True,which="both",axis='y')

        # axis.yaxis.set_minor_locator(AutoMinorLocator(10))

        # if idline==0:
            # axis.grid(True,which="major",axis='x')

        # axis.xaxis.set_major_formatter(ScalarFormatter())
        # # axis.xaxis.set_major_formatter(LogFormatter())

    def set_image(self):
        """Creates the image of figure in memory and displays it on canvas."""

        self.fgspec.tight_layout(self.figure,rect=[0,0,1.0,0.995])
        self.fgspec.update(wspace=0)

        buff = io.BytesIO()

        self.figure.savefig(buff,format='png')

        buff.seek(0)

        self.image = ImageTk.PhotoImage(Image.open(buff))

        self.canvas.create_image(0,0,anchor=tkinter.NW,image=self.image)

        self.canvas.config(scrollregion=self.canvas.bbox('all'))

    def get_xticks(self,xvals,xmin=None,xmax=None,xscale="normal",xdelta=None,xdelta_count=11):

        xvals_min = numpy.nanmin(xvals)

        if xvals_min is numpy.nan:
            xvals_min = 0.

        xvals_max = numpy.nanmax(xvals)

        if xvals_max is numpy.nan:
            xvals_max= 1.

        xrange_given = xvals_max-xvals_min

        if xdelta is None:
            xdelta = xrange_given/(xdelta_count-1)

        beforeDot,afterDot = format(xdelta,'f').split('.')

        nondim_xunit_sizes = numpy.array([1,2,4,5,10])

        if xdelta>1:

            xdelta_temp = xdelta/10**(len(beforeDot)-1)
            xdelta_temp = nondim_xunit_sizes[(numpy.abs(nondim_xunit_sizes-xdelta_temp)).argmin()]

            xdelta = xdelta_temp*10**(len(beforeDot)-1)

        else:

            zeroCountAfterDot = len(afterDot)-len(afterDot.lstrip('0'))

            xdelta_temp = xdelta*10**(zeroCountAfterDot+1)
            xdelta_temp = nondim_xunit_sizes[(numpy.abs(nondim_xunit_sizes-xdelta_temp)).argmin()]

            xdelta = xdelta_temp/10**(zeroCountAfterDot+1)

        if xscale=="normal":

            if xmin is None:
                xmin = (numpy.floor(xvals_min/xdelta)-1).astype(float)*xdelta

            if xmax is None:
                xmax = (numpy.ceil(xvals_max/xdelta)+1).astype(float)*xdelta

            xticks = numpy.arange(xmin,xmax+xdelta/2,xdelta)

        elif xscale=="log":

            if xmin is None:
                xmin = xvals_min if xvals_min>0 else 0.001

            if xmax is None:
                xmax = xvals_max if xvals_max>0 else 0.1

            xmin_power = numpy.floor(numpy.log10(xmin))
            xmax_power = numpy.ceil(numpy.log10(xmax))

            xticks = 10**numpy.arange(xmin_power,xmax_power+1/2)

        return xticks

    def get_yticks(self,yvals=None,top=None,bottom=None,endmultiple=5.,ydelta=25.):

        if yvals is None:
            yvals = numpy.array([0,1])

        if top is None:
            top = numpy.nanmin(yvals)

        if bottom is None:
            bottom = numpy.nanmax(yvals)

        if top>bottom:
            top,bottom = bottom,top

        ymin = numpy.floor(top/endmultiple)*endmultiple

        ymax = numpy.ceil(bottom/endmultiple)*endmultiple

        yticks = numpy.arange(ymin,ymax+ydelta/2,ydelta)

        return yticks

    def set_DepthViewGRcut(self,GRline,indexI,indexJ,perc_cut=40):

        # indexI index of GR containing axis in the plot
        # indexJ index of GR containing line in the axis

        try:
            depth = self.frames[GRline[0]].columns("MD")
        except ValueError:
            depth = self.frames[GRline[0]].columns("DEPT")

        xvals = self.frames[GRline[0]].columns(GRline[1])

        GRmin = numpy.nanmin(xvals)
        GRmax = numpy.nanmax(xvals)

        GRcut = (GRmin+(GRmax-GRmin)*perc_cut/100)

        cut_line = GRcut*numpy.ones(depth.shape)

        cond_clean = cut_line>=xvals

        indexTop = []
        indexBtm = []

        for i,cond in enumerate(cond_clean):
            
            if i>0:
                old_cond = cond_clean[i-1]
            else:
                old_cond = False
                
            try:
                new_cond = cond_clean[i+1]
            except IndexError:
                new_cond = False
                
            if cond and not old_cond:
                indexTop.append(i)

            if cond and not new_cond:
                indexBtm.append(i)

        net_pay = 0

        for i,j in zip(indexTop,indexBtm):

            net_pay += depth[j]-depth[i]

        self.axes[indexI].subax[indexJ].fill_betweenx(
            depth,xvals,x2=cut_line,where=cond_clean,color=self.color_clean)

        self.netPayThickness = net_pay
        self.netToGrossRatio = net_pay/self.gross_thickness*100

        return GRcut

    def set_DepthViewNeuPorCorr(self,NeuPorLine,indexI,indexJ,Vsh,NeuPorShale):

        # indexI index of Neutron Porosity containing axis in the plot
        # indexJ index of Neutron Porosity containing line in the axis

        try:
            depth = self.frames[NeuPorLine[0]]["MD"]
        except KeyError:
            depth = self.frames[NeuPorLine[0]]["DEPT"]

        xvals = self.frames[NeuPorLine[0]][NeuPorLine[1]]

        NeuPorCorr = xvals-Vsh*NeuPorShale

        self.axes[indexI].subax[indexJ].plot(NeuPorCorr,depth,
            color=self.lineColors[indexJ],linestyle="--")

    def set_DepthViewResistivityCut(self,ResLine,indexI,indexJ,ohmm_cut=10):

        # indexI index of Resistivity containing axis in the plot
        # indexJ index of Resistivity containing line in the axis

        depth = self.frames[ResLine[0]].columns(0)

        xvals = self.frames[ResLine[0]].columns(ResLine[1])

        cut_line = ohmm_cut*numpy.ones(depth.shape)

        self.axes[indexI].subax[indexJ].fill_betweenx(
            depth,xvals,x2=cut_line,where=ohmm_cut<=xvals,color=self.color_HC)

    def set_DepthViewSaturationCut(self,SwLine,indexI,indexJ,Sw_cut=0.5):

        # indexI index of Resistivity containing axis in the plot
        # indexJ index of Resistivity containing line in the axis

        depth = self.frames[SwLine[0]].columns(0)

        xvals = self.frames[SwLine[0]].columns(SwLine[1])

        cut_line = Sw_cut*numpy.ones(depth.shape)

        self.axes[indexI].subax[indexJ].fill_betweenx(
            depth,xvals,x2=cut_line,where=Sw_cut>=xvals,color=self.color_HC)

    def set_DepthViewNMRfluid(self,NMRline,indexI,water_clay,water_capi,water_move,HC):

        # indexL index of NMR containing lasio in the pack
        # indexI index of NMR containing axis in the plot

        try:
            depth = self.frames[NMRline]["MD"]
        except KeyError:
            depth = self.frames[NMRline]["DEPT"]

        xvals0 = numpy.zeros(water_clay.shape)
        xvals1 = water_clay
        xvals2 = water_clay+water_capi
        xvals3 = water_clay+water_capi+water_move
        xvals4 = water_clay+water_capi+water_move+HC

        self.axes[indexI].subax[0].fill_betweenx(
            depth,xvals1,x2=xvals0,where=xvals0<=xvals1,color=self.color_waterclay)

        self.axes[indexI].subax[0].fill_betweenx(
            depth,xvals2,x2=xvals1,where=xvals1<=xvals2,color=self.color_watercapi)

        self.axes[indexI].subax[0].fill_betweenx(
            depth,xvals3,x2=xvals2,where=xvals2<=xvals3,color=self.color_watermove)

        self.axes[indexI].subax[0].fill_betweenx(
            depth,xvals4,x2=xvals3,where=xvals3<=xvals4,color=self.color_HC)

    def set_DepthViewPerfs(self,indexI,indexJ,depths,perfs):

        xtick = self.axes[indexI].subax[indexJ].get_xticks()

        ytick = self.axes[indexI].subax[indexJ].get_yticks()

        perfs = numpy.array(perfs)

        perfs_just = perfs[perfs>0]

        perfs_just[::10] -= perfs_just[::10]*0.5

        perfs[perfs>0] = perfs_just

        perfs_scaled = xtick.min()+(xtick.max()-xtick.min())/10/(perfs.max()-perfs.min())*perfs

        # pfgun_point = xtick.min()

        # for arg in args:

        #     depths = numpy.arange(arg[0],arg[1]+1/2,1.)

        #     for index,depth in enumerate(depths):

        #         if index==0:
        #             marker,size = 11,10
        #         elif index==len(depths)-1:
        #             marker,size = 10,10
        #         else:
        #             marker,size = 9,10

        #         self.axes[indexI].subax[indexJ].plot(pfgun_point,depth,
        #             marker=marker,color='orange',markersize=size,markerfacecolor='black')

        self.axes[indexI].subax[indexJ].plot(perfs_scaled,depths)

    def set_DepthViewCasing(self):
        """It creates an axis to include casing set depths"""

        pass

    def _on_mousewheel(self,event):
        """Lets the scroll work everywhere on the window."""

        self.canvas.yview_scroll(int(-1*(event.delta/120)),"units")

class View3D():

        def __init__(self,window,**kwargs):

            super().__init__(**kwargs)

            self.dirname = os.path.dirname(__file__)

            self.root = window

        def set_plot(self):

            self.pane_EW = tkinter.ttk.PanedWindow(self.root,orient=tkinter.HORIZONTAL)

            self.frame_side = tkinter.ttk.Frame(self.root)

            self.pane_EW.add(self.frame_side,weight=1)

            self.frame_plot = tkinter.ttk.Frame(self.root)

            self.pane_EW.add(self.frame_plot,weight=1)

            self.pane_EW.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

            self.frame_plot.columnconfigure(0,weight=1)
            self.frame_plot.columnconfigure(1,weight=0)

            self.frame_plot.rowconfigure(0,weight=1)
            self.frame_plot.rowconfigure(1,weight=0)

            self.figure = pyplot.Figure()
            self.canvas = FigureCanvasTkAgg(self.figure,self.frame_plot)

            self.plotbox = self.canvas.get_tk_widget()
            self.plotbox.grid(row=0,column=0,sticky=tkinter.NSEW)        

            self.plotbar = VerticalNavigationToolbar2Tk(self.canvas,self.frame_plot)
            self.plotbar.update()
            self.plotbar.grid(row=0,column=1,sticky=tkinter.N)

            self.itembox = AutocompleteEntryListbox(self.frame_side,height=250,padding=0)

            self.itembox.content = self.itemnames.tolist()
            self.itembox.config(completevalues=self.itembox.content,allow_other_values=True)

            self.itembox.listbox.bind('<<ListboxSelect>>',lambda event: self.set_object(event))

            self.itembox.pack(expand=1,fill=tkinter.BOTH)

        def set_object(self,event):

            pass

class TableView():

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        self.dirname = os.path.dirname(__file__)

    def draw(self,func=None):

        self.scrollbar = tkinter.Scrollbar(self.root)

        self.columns = ["#"+str(idx) for idx,_ in enumerate(self.headers,start=1)]

        self.tree = tkinter.ttk.Treeview(self.root,columns=self.columns,show="headings",selectmode="browse",yscrollcommand=self.scrollbar.set)

        self.sortReverseFlag = [False for column in self.columns]

        for idx,(column,header) in enumerate(zip(self.columns,self.headers)):
            self.tree.column(column,anchor=tkinter.W,stretch=tkinter.NO)
            self.tree.heading(column,text=header,anchor=tkinter.W)

        self.tree.column(self.columns[-1],stretch=tkinter.YES)

        self.tree.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.scrollbar.pack(side=tkinter.LEFT,fill=tkinter.Y)

        self.scrollbar.config(command=self.tree.yview)

        # self.frame = tkinter.Frame(self.root,width=50)
        # self.frame.configure(background="white")
        # self.frame.pack(side=tkinter.LEFT,fill=tkinter.Y)

        self.tree.bind("<KeyPress-i>",self.addItem)

        # self.button_Add = tkinter.Button(self.frame,text="Add Item",width=50,command=self.addItem)
        # self.button_Add.pack(side=tkinter.TOP,ipadx=5,padx=10,pady=(5,1))

        self.tree.bind("<KeyPress-e>",self.editItem)
        self.tree.bind("<Double-1>",self.editItem)

        self.tree.bind("<Delete>",self.deleteItem)

        self.tree.bind("<KeyPress-j>",self.moveDown)
        self.tree.bind("<KeyPress-k>",self.moveUp)

        self.tree.bind("<Button-1>",self.sort_column)

        self.tree.bind("<Control-KeyPress-s>",lambda event: self.saveChanges(func,event))

        # self.button_Save = tkinter.Button(self.frame,text="Save Changes",width=50,command=lambda: self.saveChanges(func))
        # self.button_Save.pack(side=tkinter.TOP,ipadx=5,padx=10,pady=(10,1))

        self.root.protocol('WM_DELETE_WINDOW',lambda: self.close_no_save(func))

        self.counter = self.running[0].size

        self.iids = numpy.arange(self.counter)

        self.added = []
        self.edited = []
        self.deleted = []

        self.refill()

    def refill(self):

        self.tree.delete(*self.tree.get_children())

        rows = numpy.array(self.running).T.tolist()

        for iid,row in zip(self.iids,rows):
            self.tree.insert(parent="",index="end",iid=iid,values=row)

    def addItem(self,event):

        if hasattr(self,"topAddItem"):
            if self.topAddItem.winfo_exists():
                return

        self.topAddItem = tkinter.Toplevel()

        self.topAddItem.resizable(0,0)

        for index,header in enumerate(self.headers):
            label = "label_"+str(index)
            entry = "entry_"+str(index)
            pady = (30,5) if index==0 else (5,5)
            setattr(self.topAddItem,label,tkinter.Label(self.topAddItem,text=header,font="Helvetica 11",width=20,anchor=tkinter.E))
            setattr(self.topAddItem,entry,tkinter.Entry(self.topAddItem,width=30,font="Helvetica 11"))
            getattr(self.topAddItem,label).grid(row=index,column=0,ipady=5,padx=(10,5),pady=pady)
            getattr(self.topAddItem,entry).grid(row=index,column=1,ipady=5,padx=(5,10),pady=pady)

        self.topAddItem.entry_0.focus()

        self.topAddItem.button = tkinter.Button(self.topAddItem,text="Add Item",command=self.addItemEnterClicked)
        self.topAddItem.button.grid(row=index+1,column=0,columnspan=2,ipady=5,padx=15,pady=(15,30),sticky=tkinter.EW)

        self.topAddItem.button.bind('<Return>',self.addItemEnterClicked)

        self.topAddItem.mainloop()

    def addItemEnterClicked(self,event=None):

        if event is not None and event.widget!=self.topAddItem.button:
            return

        values = []

        for idx,header in enumerate(self.headers):
            entry = "entry_"+str(idx)
            value = getattr(self.topAddItem,entry).get()
            values.append(value)

        self.added.append(self.counter)

        self.set_rows(values)

        self.iids = numpy.append(self.iids,self.counter)

        self.tree.insert(parent="",index="end",iid=self.counter,values=values)

        self.counter += 1

        self.topAddItem.destroy()

    def editItem(self,event):

        region = self.tree.identify('region',event.x,event.y)

        if region=="separator":
            self.autowidth(event)
            return

        if not(region=="cell" or event.char=="e"):
            return

        if hasattr(self,"topEditItem"):
            if self.topEditItem.winfo_exists():
                return

        if not self.tree.selection():
            return
        else:
            item = self.tree.selection()[0]

        values = self.tree.item(item)['values']

        self.topEditItem = tkinter.Toplevel()

        self.topEditItem.resizable(0,0)

        for idx,(header,explicit) in enumerate(zip(self.headers,self.headers)):
            label = "label_"+str(idx)
            entry = "entry_"+str(idx)
            pady = (30,5) if idx==0 else (5,5)
            setattr(self.topEditItem,label,tkinter.Label(self.topEditItem,text=explicit,font="Helvetica 11",width=20,anchor=tkinter.E))
            setattr(self.topEditItem,entry,tkinter.Entry(self.topEditItem,width=30,font="Helvetica 11"))
            getattr(self.topEditItem,label).grid(row=idx,column=0,ipady=5,padx=(10,5),pady=pady)
            getattr(self.topEditItem,entry).grid(row=idx,column=1,ipady=5,padx=(5,10),pady=pady)
            getattr(self.topEditItem,entry).insert(0,values[idx])

        self.topEditItem.entry_0.focus()

        self.topEditItem.button = tkinter.Button(self.topEditItem,text="Save Item Edit",command=lambda: self.editItemEnterClicked(item))
        self.topEditItem.button.grid(row=idx+1,column=0,columnspan=2,ipady=5,padx=15,pady=(15,30),sticky=tkinter.EW)

        self.topEditItem.button.bind('<Return>',lambda event: self.editItemEnterClicked(item,event))

        self.topEditItem.mainloop()

    def editItemEnterClicked(self,item,event=None):

        if event is not None and event.widget!=self.topEditItem.button:
            return

        values = []

        for idx,header in enumerate(self.headers):
            entry = "entry_"+str(idx)
            value = getattr(self.topEditItem,entry).get()
            values.append(value)

        self.edited.append([int(item),self.tree.item(item)["values"]])

        self.set_rows(values,numpy.argmax(self.iids==int(item)))

        self.tree.item(item,values=values)

        self.topEditItem.destroy()

    def deleteItem(self,event):

        if not self.tree.selection():
            return
        else:
            item = self.tree.selection()[0]

        self.deleted.append([int(item),self.tree.item(item)["values"]])

        self.del_rows(numpy.argmax(self.iids==int(item)),inplace=True)

        self.iids = numpy.delete(self.iids,numpy.argmax(self.iids==int(item)))

        self.tree.delete(item)

    def autowidth(self,event):

        column = self.tree.identify('column',event.x,event.y)

        index = self.columns.index(column)

        if index==len(self.columns)-1:
            return

        header_char_count = len(self.headers[index])

        vcharcount = numpy.vectorize(lambda x: len(x))

        if self.running[index].size != 0:
            column_char_count = vcharcount(self.running[index].astype(str)).max()
        else:
            column_char_count = 0

        char_count = max(header_char_count,column_char_count)

        width = tkinter.font.Font(family="Consolas", size=12).measure("A"*char_count)

        column_width_old = self.tree.column(column,"width")

        self.tree.column(column,width=width)

        column_width_new = self.tree.column(column,"width")

        column_width_last_old = self.tree.column(self.columns[-1],"width")

        column_width_last_new = column_width_last_old+column_width_old-column_width_new

        self.tree.column(self.columns[-1],width=column_width_last_new)

    def moveUp(self,event):
 
        if not self.tree.selection():
            return
        else:
            item = self.tree.selection()[0]

        self.tree.move(item,self.tree.parent(item),self.tree.index(item)-1)

    def moveDown(self,event):

        if not self.tree.selection():
            return
        else:
            item = self.tree.selection()[0]

        self.tree.move(item,self.tree.parent(item),self.tree.index(item)+1)

    def sort_column(self,event):

        region = self.tree.identify('region',event.x,event.y)

        if region!="heading":
            return

        column = self.tree.identify('column',event.x,event.y)

        header_index = self.columns.index(column)

        reverseFlag = self.sortReverseFlag[header_index]

        N = self.running[0].size

        argsort = numpy.argsort(self.running[header_index])

        if reverseFlag:
            argsort = numpy.flip(argsort)

        for index,column in enumerate(self.running):
            self.running[index] = column[argsort]

        self.iids = self.iids[argsort]
        # indices = numpy.arange(N)

        # sort_indices = indices[numpy.argsort(argsort)]

        self.refill()

        # for item,sort_index in zip(self.iids,sort_indices):
        #     self.tree.move(item,self.tree.parent(item),sort_index)

        self.sortReverseFlag[header_index] = not reverseFlag

    def saveChanges(self,func=None,event=None):

        self.added = []
        self.edited = []
        self.deleted = []

        if func is not None:
            func()

    def close_no_save(self,func=None):

        try:
            for deleted in self.deleted:
                self.set_rows(deleted[1])
        except:
            print("Could not bring back deleted rows ...")

        try:
            for edited in self.edited:
                self.set_rows(edited[1],numpy.argmax(self.iids==edited[0]))
        except:
            print("Could not bring back editions ...")

        added = [numpy.argmax(self.iids==add) for add in self.added]

        try:
            self.del_rows(added,inplace=True)
        except:
            print("Could not remove additions ...")

        try:
            if func is not None:
                func()
        except:
            print("Could not run the called function ...")

        self.root.destroy()

class TreeView():

    def __init__(self,dirpath):

        self.dirpath = dirpath

    def draw(self,window,func=None):

        self.root = window

        self.scrollbar = tkinter.ttk.Scrollbar(self.root)

        self.tree = tkinter.ttk.Treeview(self.root,show="headings tree",selectmode="browse",yscrollcommand=self.scrollbar.set)

        self.tree.pack(side=tkinter.LEFT,expand=1,fill=tkinter.BOTH)

        self.scrollbar.pack(side=tkinter.LEFT,fill=tkinter.Y)

        self.scrollbar.config(command=self.tree.yview)

        self.tree.bind("<Button-1>",lambda event: self.set_path(func,event))

        self.refill()

    def refill(self):

        self.tree.heading("#0",text="")

        self.tree.delete(*self.tree.get_children())

        iterator = os.walk(self.dirpath)

        parents_name = []
        parents_link = []

        counter  = 0

        while True:

            try:
                root,dirs,frames = next(iterator)
            except StopIteration:
                break

            if counter==0:
                dirname = os.path.split(root)[1]
                self.tree.heading("#0",text=dirname,anchor=tkinter.W)
                parents_name.append(root)
                parents_link.append("")
            
            parent = parents_link[parents_name.index(root)]

            for directory in dirs:
                link = self.tree.insert(parent,'end',iid=counter,text=directory)
                counter += 1

                parents_name.append(os.path.join(root,directory))
                parents_link.append(link)

            for file in frames:            
                self.tree.insert(parent,'end',iid=counter,text=file)
                counter += 1

    def set_path(self,func=None,event=None):

        if event is not None:
            region = self.tree.identify("region",event.x,event.y)
        else:
            return

        if region!="tree":
            return

        item = self.tree.identify("row",event.x,event.y)

        path = self.tree.item(item)['text']

        while True:

            item = self.tree.parent(item)

            if item:
                path = os.path.join(self.tree.item(item)['text'],path)
            else:
                path = os.path.join(self.dirpath,path)
                break

        if func is not None:
            func(path)
        else:
            print(path)

# Supporting Tkinter Widgets

class VerticalNavigationToolbar2Tk(NavigationToolbar2Tk):

    def __init__(self,canvas,window):

        super().__init__(canvas,window,pack_toolbar=False)

        self.message = tkinter.StringVar(master=window)
        self._message_label = tkinter.Label(master=window,textvariable=self.message)
        self._message_label.grid(row=1,column=0,columnspan=2,sticky=tkinter.W)

    # override _Button() to re-pack the toolbar button in vertical direction
    def _Button(self,text,image_file,toggle,command):
        b = super()._Button(text,image_file,toggle,command)
        b.pack(side=tkinter.TOP) # re-pack button in vertical direction
        return b

    # override _Spacer() to create vertical separator
    def _Spacer(self):
        s = tkinter.Frame(self,width=26,relief=tkinter.RIDGE,bg="DarkGray",padx=2)
        s.pack(side=tkinter.TOP,pady=5) # pack in vertical direction
        return s

if __name__ == "__main__":

    pass
