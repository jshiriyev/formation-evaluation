import lasio

from matplotlib import backends
from matplotlib import patches
from matplotlib import pyplot as plt

import numpy as np

from .wellview._booter import Boot

class WellView(Boot):

    def __init__(self,las,**kwargs):

        self._las = las

        super().__init__(**kwargs)

    def __call__(self,figure):

        self.axes = super().__call__(figure)

    def axis_label(self,index):
        return self.axes[index*2+0]

    def axis_curve(self,index):
        return self.axes[index*2+1]

    def add_curve(self,index,mnem):

        label_axis = label_axes[curve.col]
        curve_axis = curve_axes[curve.col]

        xaxis = self.axes['xaxis'][curve.col]

        getattr(self,f"set_{xaxis['scale'][:3]}xaxis")(curve,xaxis)

        if hasattr(curve,'gradalpha'):
            gradient(curve.xaxis,curve.depth,axis=curve_axis,
                color = curve.color,
                fill_color = curve.myfill_color,
                linestyle = curve.style,
                linewidth = curve.width,
                alpha = curve.gradalpha)
        else:
            curve_axis.plot(curve.xaxis,curve.depth,
                color = curve.color,
                linestyle = curve.style,
                linewidth = curve.width,)

        row = len(curve_axis.lines)

        # if curve.row is False:
        #     curve.row = row
        #     return

        if curve.row is None:
            curve.row = row

        if curve.row is False:
            return

        label_axis.plot((0,1),(curve.row-0.6,curve.row-0.6),
            color=curve.color,linestyle=curve.style,linewidth=curve.width)

        label_axis.text(0.5,curve.row-0.5,f"{curve.mnemonic}",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        label_axis.text(0.5,curve.row-0.9,f"[{curve.unit}]",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        label_axis.text(0.02,curve.row-0.5,f"{curve.limit[0]:.5g}",horizontalalignment='left')
        label_axis.text(0.98,curve.row-0.5,f"{curve.limit[1]:.5g}",horizontalalignment='right')

    def set_curve_label(self,index,mnem,cmin,cmax,nrow,**kwargs):

        axis = self.axis_label(index)

        xlim = self[index].limit

        row = nrow*self.label.major

        xmin,xmax = xlim

        xlen = xmax-xmin

        axis.plot(xlim,(row-6,row-6),**kwargs)

        curve = self._las.curves[mnem]

        axis.text(np.mean(xlim),row-5,f"{mnem}",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        axis.text(np.mean(xlim),row-8,f"{curve.unit}",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        axis.text(xmin+xlen*2/100,row-5,f"{cmin:.5g}",horizontalalignment='left')
        axis.text(xmax-xlen*2/100,row-5,f"{cmax:.5g}",horizontalalignment='right')

    def add_module(self):

        label_axes = self.figure.axes[self.axes['label_indices']]
        curve_axes = self.figure.axes[self.axes['curve_indices']]

        for module in self.modules:

            label_axis = label_axes[module['col']]
            curve_axis = curve_axes[module['col']]

            xlim = curve_axis.get_xlim()

            lines = curve_axis.lines

            if module['left'] is None:
                yvals = lines[0].get_ydata()
                xvals = np.ones(yvals.shape)
            else:
                yvals = lines[module['left']].get_ydata()
                xvals = lines[module['left']].get_xdata()

            if module['right'] is None:
                x2 = 0
            elif module['right']>=len(lines):
                x2 = max(xlim)
            else:
                x2 = lines[module['right']].get_xdata()

            if module.get('leftnum') is not None:
                x2 = module['leftnum']

            if module.get('where') is None:
                where = (xvals>x2)
            elif module.get('where') is True:
                where = (xvals<x2)
            else:
                where = module['where']

            curve_axis.fill_betweenx(yvals,xvals,x2=x2,where=where,facecolor=module['module']['fillcolor'],hatch=module['module']["hatch"])

            if module.get('row') is None:
                module['row'] = len(lines)

            rect = patches.Rectangle((0,module['row']),1,1,
                fill=True,facecolor=module['module']['fillcolor'],hatch=module['module']['hatch'])

            label_axis.add_patch(rect)
            
            label_axis.text(0.5,module['row']+0.5,module['module']['detail'],
                horizontalalignment='center',
                verticalalignment='center',
                backgroundcolor='white',
                fontsize='small',)

    def add_perf(self):
        """It includes perforated depth."""

        curve_axes = self.figure.axes[self.axes['curve_indices']]

        for perf in self.perfs:

            curve_axis = curve_axes[perf['col']]

            depth = np.array(perf['depth'],dtype=float)

            yvals = np.arange(depth.min(),depth.max()+0.5,1.0)

            xvals = np.zeros(yvals.shape)

            curve_axis.plot(xvals[0],yvals[0],
                marker=11,
                color='orange',
                markersize=10,
                markerfacecolor='black')

            curve_axis.plot(xvals[-1],yvals[-1],
                marker=10,
                color='orange',
                markersize=10,
                markerfacecolor='black')

            curve_axis.plot(xvals[1:-1],yvals[1:-1],
                marker=9,
                color='orange',
                markersize=10,
                markerfacecolor='black')

    def add_casing(self):
        """It includes casing set depth."""
        pass

    def view(self,top,wspace=0.0,hspace=0.0,height=30,**kwargs):

        if len(self.axes)==0:
            self.set_axes()

        if kwargs.get("figsize") is None:
            kwargs["figsize"] = ((self.columns)*1.5,6.5)

        self.add_figure(**kwargs)

        self.add_axes()
        self.add_curves()
        self.add_modules()
        self.add_perfs()
        self.add_casings()

        self.gspecs.tight_layout(self.figure)

        self.gspecs.update(wspace=wspace,hspace=hspace)

        for index,axis in enumerate(self.figure.axes):
            if self.axes['labelloc'] == "none":
                axis.set_ylim(top+height,top)
            elif index%2==1:
                axis.set_ylim(top+height,top)

        plt.show()

    def save(self,filepath,wspace=0.0,hspace=0.0,**kwargs):
        """It saves the WellView as a multipage pdf file."""

        if len(self.axes)==0:
            self.set_axes()

        if not hasattr(self,"page"):
            self.set_page(**kwargs)

        filepath = self.get_extended(path=filepath,extension='.pdf')

        filepath = self.get_abspath(path=filepath,homeFlag=True)

        self.add_figure(**kwargs)

        self.add_axes()
        self.add_curves()
        self.add_modules()
        self.add_perfs()
        self.add_casings()

        self.gspecs.tight_layout(self.figure)

        self.gspecs.update(wspace=wspace,hspace=hspace)

        with backends.backend_pdf.PdfPages(filepath) as pdf:

            for limit in self.page['depth'].limits:

                for index,axis in enumerate(self.figure.axes):
                    if self.axes['labelloc'] == "none":
                        axis.set_ylim(limit)
                    elif index%2==1:
                        axis.set_ylim(limit)

                pdf.savefig()

    @property
    def columns(self):

        columns = []

        for _,curve in self.curves.items():
            columns.append(curve.col)

        return len(set(columns))

    @property
    def rows(self):

        columns = []

        for _,curve in self.curves.items():
            columns.append(curve.col)

        columns_unique = set(columns)

        rows = []

        for column in columns_unique:
            rows.append(columns.count(column))

        nrows = 3 if max(rows)<3 else max(rows)

        return nrows
