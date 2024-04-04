import lasio

from matplotlib import backends
from matplotlib import colors
from matplotlib import gridspec
from matplotlib import patches
from matplotlib import pyplot
from matplotlib import ticker
from matplotlib import transforms

import numpy

from utils._popdict import popdict

from ._depths import Depths
from ._layout import Layout
from ._curve import Curve
from ._module import Module
from ._perfor import Perfor
from ._casing import Casing

from ._gradient import gradient

class DepthView():

    def __init__(self,lasfile:lasio.LASFile,*args,**kwargs):

        self.lasfile = lasfile

        self.layout  = Layout() # head, body, depth, xaxis

        self.curves  = ()
        self.modules = ()
        self.perfors = ()
        self.casings = ()

    def set_layout(self):

        pass

    def set_curve(self,col,head,row=None,vmin=None,vmax=None,multp=None,**kwargs):
        """It adds LasCurve[head] to the axes[col]."""

        kwargs['color'] = popdict(kwargs,"color","black")
        kwargs['style'] = popdict(kwargs,"style","solid")
        kwargs['width'] = popdict(kwargs,"width",0.75)

        depth = self.lasfile[0]

        # lasio.CurveItem(mnemonic='', unit='', value='', descr='', data=None)

        curve = lasio.CurveItem()

        conds = numpy.logical_and(depth>self.depths['top'],depth<self.depths['bottom'])

        curve.mnemonic = head.split('_')[0]
        
        curve.data = self.lasfile[head][conds]

        curve.depth = depth[conds]

        self.curves[curve.mnemonic] = curve

    def set_xaxis(self,col,**kwargs):

        if len(self.axes)==0:
            self.set_axes()

        if col==self.axes['depthloc']:
            subs,limit = 1,(0,10)

        self.axes['xaxis'][col] = xaxis = XAxis(**kwargs)

    def __getitem__(self,head):

        return self.curves[head]

    def set_module(self,col,module,left=0,right=None,**kwargs):
        """It adds petrophysical module to the defined curve axis."""

        _module = {}

        _module['col'] = col
        _module['module'] = module

        for key,value in kwargs.items():
            _module[key] = value

        self.modules.append(_module)

    def set_perf(self,depth,col=None,**kwargs):
        """It adds perforation depth to the depth axis."""

        _perf = {}

        if len(self.axes)==0:
            self.set_axes()

        if col is None:
            col = self.axes['depthloc']

        _perf['col'] = col

        _perf['depth'] = depth

        for key,value in kwargs.items():
            _perf[key] = value

        self.perfs.append(_perf)

    def set_casing(self,depth,col=None,**kwargs):
        """It adds casing depth to the depth axis."""

        _casing = {}

        if len(self.axes)==0:
            self.set_axes()

        if col is None:
            col = self.axes['depthloc']

        _casing['col'] = col

        _casing['depth'] = depth

        for key,value in kwargs.items():
            _casing[key] = value

        self.casings.append(_casing)

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

        pyplot.show()

    def set_page(self,**kwargs):
        """It sets the format of page for printing."""

        depths = popdict(kwargs,"depths")

        self.page = {}

        self.page['fmt'] = popdict(kwargs,"fmt","A4").lower()

        self.page['orientation'] = popdict(kwargs,"orientation","portrait").lower()

        size = self.get_pagesize(self.page['orientation'])

        self.page['width'] = size['width']

        self.page['height'] = size['height']

        self.page['size'] = (size['width'],size['height'])

        self.page['dpi'] = popdict(kwargs,"dpi",100)

        grids = self.get_pagegrid(self.page['orientation'])

        self.set_axes(label=4,**grids)

        if depths is not None:

            top,bottom = abs(min(depths)),abs(max(depths))

            depths = (bottom,top)

            top,bottom = min(depths),max(depths)

            height_total = bottom-top

        else:

            height_total = self.depths['height']

            top,bottom = self.depths['top'],self.depths['bottom']

        height_pages = self.axes['curve_indices']

        self.page['depth'].number = -(-height_total//height_pages)

        self.page['depth'].limits = []

        while top<bottom:
            self.page['depth'].limits.append(top,top+height_pages)
            top += height_pages

    def save(self,filepath,wspace=0.0,hspace=0.0,**kwargs):
        """It saves the DepthView as a multipage pdf file."""

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

    def add_figure(self,**kwargs):

        self.figure = pyplot.figure(**kwargs)

        self.gspecs = gridspec.GridSpec(
            nrows = self.axes['naxes_percolumn'],
            ncols = self.axes['ncols'],
            figure = self.figure,
            width_ratios = self.axes['width_ratio'],
            height_ratios = self.axes['height_ratio'])

    def add_axes(self):

        for index in range(self.axes['ncols']):

            xaxis = self.axes['xaxis'][index]

            yaxis = self.depths

            if self.axes['labelloc'] == "none":
                curve_axis = self.figure.add_subplot(self.gspecs[index])
            elif self.axes['labelloc'] == "top":
                label_axis = self.figure.add_subplot(self.gspecs[0,index])
                curve_axis = self.figure.add_subplot(self.gspecs[1,index])
            elif self.axes['labelloc'] == "bottom":
                label_axis = self.figure.add_subplot(self.gspecs[1,index])
                curve_axis = self.figure.add_subplot(self.gspecs[0,index])

            if self.axes['labelloc'] != "none":
                xlim,ylim = (0,1),(0,self.axes['nrows'])
                self.set_axislabel(label_axis,xlim,ylim)

            if index != self.axes['depthloc']:
                self.set_yaxiscurve(curve_axis,yaxis)
                self.set_xaxiscurve(curve_axis,xaxis)
            else:
                self.set_axisdepth(curve_axis,xaxis,yaxis)

    def add_curves(self):

        label_axes = self.figure.axes[self.axes['label_indices']]
        curve_axes = self.figure.axes[self.axes['curve_indices']]

        for _,curve in self.curves.items():

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

            self.set_labelcurve(label_axis,curve)

    def add_modules(self):

        label_axes = self.figure.axes[self.axes['label_indices']]
        curve_axes = self.figure.axes[self.axes['curve_indices']]

        for module in self.modules:

            label_axis = label_axes[module['col']]
            curve_axis = curve_axes[module['col']]

            xlim = curve_axis.get_xlim()

            lines = curve_axis.lines

            if module['left'] is None:
                yvals = lines[0].get_ydata()
                xvals = numpy.ones(yvals.shape)
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

            self.set_labelmodule(label_axis,module)

    def add_perfs(self):
        """It includes perforated depth."""

        curve_axes = self.figure.axes[self.axes['curve_indices']]

        for perf in self.perfs:

            curve_axis = curve_axes[perf['col']]

            depth = numpy.array(perf['depth'],dtype=float)

            yvals = numpy.arange(depth.min(),depth.max()+0.5,1.0)

            xvals = numpy.zeros(yvals.shape)

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

    def add_casings(self):
        """It includes casing set depth."""

        pass

    @staticmethod
    def get_pagesize(fmt="A4",orientation="portrait",unit="in"):

        fmt = fmt.lower()

        orientation = orientation.lower()

        unit = unit.lower()[:2]

        _page = {}

        a4,letter = {},{}

        if orientation == "portrait":
            a4["cm"] = [21.0,29.7]
            letter["in"] = [8.5,11.0]
        elif orientation == "landscape":
            a4["cm"] = [29.7,21.0]
            letter["in"] = [11.0,8.5]
        else:
            raise(f'Page orientation={orientation} has not been defined!')

        a4["in"] = [size/2.54 for size in a4['cm']]
        
        letter["cm"] = [size*2.54 for size in letter['in']]

        _page['a4'],_page['letter'] = a4,letter

        return {'width': _page[fmt][unit][0], 'height': _page[fmt][unit][1]}

    @staticmethod
    def get_pagegrid(fmt="A4",orientation="portrait"):

        fmt = fmt.lower()

        orientation = orientation.lower()

        _grid = {}

        if orientation=="portrait":
            a4,letter = [66,86],[66,81]
        elif orientation=="landscape":
            a4,letter = [90,61],[90,62]
        else:
            raise(f'Page orientation={orientation} has not been defined!')

        _grid['a4'],_grid['letter'] = a4,letter

        return {'width': _grid[fmt][0], 'height': _grid[fmt][1]}

    @staticmethod
    def set_labelcurve(axis,curve):

        if curve.row is False:
            return

        axis.plot((0,1),(curve.row-0.6,curve.row-0.6),
            color=curve.color,linestyle=curve.style,linewidth=curve.width)

        axis.text(0.5,curve.row-0.5,f"{curve.mnemonic}",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        axis.text(0.5,curve.row-0.9,f"[{curve.unit}]",
            horizontalalignment='center',
            # verticalalignment='bottom',
            fontsize='small',)

        axis.text(0.02,curve.row-0.5,f"{curve.limit[0]:.5g}",horizontalalignment='left')
        axis.text(0.98,curve.row-0.5,f"{curve.limit[1]:.5g}",horizontalalignment='right')

    @staticmethod
    def set_labelmodule(axis,module):

        rect = patches.Rectangle((0,module['row']),1,1,
            fill=True,facecolor=module['module']['fillcolor'],hatch=module['module']['hatch'])

        axis.add_patch(rect)
        
        axis.text(0.5,module['row']+0.5,module['module']['detail'],
            horizontalalignment='center',
            verticalalignment='center',
            backgroundcolor='white',
            fontsize='small',)

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
