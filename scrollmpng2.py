import tkinter as tk

class ScrollableImage(tk.Frame):

    def __init__(self, master=None, **kw):

        self.image = kw.pop('image', None)
        sw = kw.pop('scrollbarwidth', 10)
        super(ScrollableImage, self).__init__(master=master, **kw)
        self.cnvs = tk.Canvas(self, highlightthickness=0, **kw)
        self.cnvs.create_image(0, 0, anchor='nw', image=self.image)
        # Vertical and Horizontal scrollbars
        self.v_scroll = tk.Scrollbar(self, orient='vertical', width=sw)
        self.h_scroll = tk.Scrollbar(self, orient='horizontal', width=sw)
        # Grid and configure weight.
        self.cnvs.grid(row=0, column=0,  sticky='nsew')
        self.h_scroll.grid(row=1, column=0, sticky='ew')
        self.v_scroll.grid(row=0, column=1, sticky='ns')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Set the scrollbars to the canvas
        self.cnvs.config(xscrollcommand=self.h_scroll.set, 
                           yscrollcommand=self.v_scroll.set)
        # Set canvas view to the scrollbars
        self.v_scroll.config(command=self.cnvs.yview)
        self.h_scroll.config(command=self.cnvs.xview)
        # Assign the region to be scrolled 
        self.cnvs.config(scrollregion=self.cnvs.bbox('all'))
        # self.cnvs.bind_class(self.cnvs, "<MouseWheel>", self.mouse_scroll)
        self.cnvs.bind_all("<MouseWheel>",self._on_mousewheel)

    def mouse_scroll(self, evt):
        if evt.state == 0 :
            self.cnvs.yview_scroll(-1*(evt.delta), 'units') # For MacOS
            self.cnvs.yview_scroll(int(-1*(evt.delta/120)), 'units') # For windows
        if evt.state == 1:
            self.cnvs.xview_scroll(-1*(evt.delta), 'units') # For MacOS
            self.cnvs.xview_scroll(int(-1*(evt.delta/120)), 'units') # For windows

    def _on_mousewheel(self,event):

        self.cnvs.yview_scroll(int(-1*(event.delta/120)), "units")


if __name__ == "__main__":

    root = tk.Tk()

    # PhotoImage from tkinter only supports:- PGM, PPM, GIF, PNG format.
    # To use more formats use PIL ImageTk.PhotoImage
    img = tk.PhotoImage(file="FS.png")

    image_window = ScrollableImage(root, image=img, scrollbarwidth=20, 
                                   width=200, height=200)
    image_window.pack(side=tk.TOP,fill=tk.BOTH,expand=1)

    root.mainloop()