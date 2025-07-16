import lasio

from matplotlib import backends
from matplotlib import patches
from matplotlib import pyplot as plt
from matplotlib import ticker

from matplotlib.colors import to_rgb
from matplotlib.figure import Figure

import numpy as np
import pandas as pd

from scipy.interpolate import interp1d

import wellx

from ._pigment import Pigment

from .wellview._builder import Builder

class WellView(Builder):
    """
    A plotting class for rendering well log data using a layout defined in Builder.
    """

    def __init__(self,las:lasio.LASFile,**kwargs):
        """
        Initialize the WellView instance.

        Args:
            las: LAS file object (e.g., loaded using `lasio`).
            **kwargs: Additional keyword arguments forwarded to Builder.

        """
        self._las = las

        super().__init__(**kwargs)

    @property
    def las(self):
        """Return the internal LAS object representing well log data."""
        return self._las
    
    def __call__(self,figure:Figure):
        """
        This method calls the parent 'Builder.__call__' method to construct the layout 
        on the given matplotlib figure, and stores the resulting axes.
        """
        self.axes = super().__call__(figure)

    def label(self,index:int):
        """Return the axis used for the label (head) of the given track index."""
        return self.axes[index*2+0]

    def stage(self,index:int):
        """Return the axis that is used for adding a curve, shading, and module."""
        return self.axes[index*2+1]

    def add_depths(self,index:int,survey:pd.DataFrame=None):
        """Add depth annotations or MD-transformed ticks to the specified axis."""

        axis = self.stage(index)

        md_min,md_max = np.flip(self._depth.limit).tolist()

        loc_major = ticker.MultipleLocator(self._depth.major)
        loc_minor = ticker.MultipleLocator(self._depth.minor)

        if survey is None:
            yticks_major = loc_major.tick_values(md_min,md_max)
            # If no survey is provided, annotate MD ticks directly
            for ytick in yticks_major[2:-2]:
                axis.annotate(f"{ytick:4.0f}",
                    xy=(self[index].middle,ytick),ha='center',va='center'
                )
            return

        md,tvd = survey[['MD','TVD']].to_numpy().T

        limit = interp1d(md,tvd,kind='linear',fill_value="extrapolate")((md_min,md_max))

        yticks_major = loc_major.tick_values(*limit)
        yticks_minor = loc_minor.tick_values(*limit)

        # axis.tick_params(which='minor',length=0)

        yticks_major = yticks_major[np.logical_and(yticks_major>=limit[0],yticks_major<=limit[1])]
        yticks_minor = yticks_minor[np.logical_and(yticks_minor>=limit[0],yticks_minor<=limit[1])]

        yticks_major_md = interp1d(tvd,md,kind='linear',fill_value="extrapolate")(yticks_major)
        yticks_minor_md = interp1d(tvd,md,kind='linear',fill_value="extrapolate")(yticks_minor)

        axis.set_yticks(yticks_major_md,minor=False)
        axis.set_yticks(yticks_minor_md,minor=True)

        for ytick_md,ytick in zip(yticks_major_md,yticks_major):
            axis.annotate(
                f"{ytick:4.0f}",xy=(self[index].middle,ytick_md),ha='center',va='center')

        # axis.set_yticklabels(yticks_major)

    def add_tops(self,index,tops:pd.DataFrame,**kwargs):

        axis_curve = self.stage(index)

        if tops['depth'].iloc[0]>self._depth.upper:
            upper_row = pd.DataFrame({'formation':["Unknown"],'depth':[self._depth.upper],'facecolor':[None]})
            tops = pd.concat([upper_row,tops]).reset_index(drop=True)

        if tops['depth'].iloc[-1]<self._depth.lower:
            lower_row = pd.DataFrame({'formation':["Unknown"],'depth':[self._depth.lower],'facecolor':[None]})
            tops = pd.concat([tops,lower_row]).reset_index(drop=True)

        shortlist = tops[(tops['depth']>self._depth.upper)&(tops['depth']<self._depth.lower)]

        if shortlist.empty:
            return

        if shortlist.index[0]>0:
            top_row = tops.iloc[[shortlist.index[0]-1]]
            upper_row = pd.DataFrame({'formation':top_row['formation'],'depth':[self._depth.upper],'facecolor':top_row['facecolor']})
            shortlist = pd.concat([upper_row,shortlist])

        for i,row in shortlist.iterrows():

            upper = row['depth'] if row['depth']>self._depth.upper else self._depth.upper
            lower = tops.iloc[i+1,:]['depth'] if tops.iloc[i+1,:]['depth']<self._depth.lower else self._depth.lower

            axis_curve.fill_betweenx((upper,lower),
                (self[index].lower,)*2,self[index].length,facecolor=row['facecolor'],**kwargs)

            if len(row['formation'])*1.5<(lower-upper):

                zorder = None if kwargs.get('zorder') is None else kwargs.get('zorder')+1

                if row['facecolor'] is None:
                    color = 'black'
                else:
                    r,g,b = [x*255 for x in to_rgb(row['facecolor'])]
                    brightness = 0.299*r+0.587*g+0.114*b
                    color = "black" if brightness > 128 else "white"

                axis_curve.text(self[index].middle,(upper+lower)/2,row['formation'],
                    color=color,rotation=90,ha='center',va='center',zorder=zorder)

    def add_curve(self,index:int,mnemo:str,multp:float=1.,shift:float=0.,cycle:int|bool=True,**kwargs):

        axis_curve = self.stage(index)

        curve = self.las.curves[mnemo]
        xvals = curve.data*multp+shift

        axis_curve.plot(xvals,self.las.index,**kwargs)

        if cycle is False:
            return

        if kwargs.get('linewidth') is not None:
            kwargs['linewidth'] *= 2

        self.add_curve_legend(index,mnemo,multp,shift,cycle,**kwargs)

    def add_curve_legend(self,index:int,mnemo:str,multp:float=1.,shift:float=0.,cycle:int|bool=True,**kwargs):

        axis_curve = self.stage(index)
        axis_label = self.label(index)

        curve = self.las.curves[mnemo]

        row = (len(axis_curve.lines) if cycle is True else cycle)*self._label.major

        axis_label.plot(self[index].limit,(row-0.6*self._label.major,)*2,**kwargs)

        axis_label.text(self[index].middle,row-0.5*self._label.major,f"{mnemo}",
            ha='center',fontsize='small',)

        axis_label.text(self[index].middle,row-0.8*self._label.major,f"{curve.unit}",
            ha='center',fontsize='small',)

        xmin,xmax = self[index].limit
        cmin,cmax = (xmin-shift)/multp,(xmax-shift)/multp

        axis_label.text(self[index].lower_off(2.),row-0.5*self._label.major,f"{cmin:.5g}",ha='left')
        axis_label.text(self[index].upper_off(2.),row-0.5*self._label.major,f"{cmax:.5g}",ha='right')

    def add_cut(self,index:int,mnemo:str,cut:float,multp:float=1.,shift:float=0.,left:dict=None,right:dict=None,cycle:int|bool=True,**kwargs):
        
        self.add_curve(index,mnemo,multp,shift,cycle,**kwargs)

        axis_curve = self.stage(index)
        axis_label = self.label(index)

        curve = self.las.curves[mnemo]
        xvals = curve.data*multp+shift

        if left is not None:
            axis_curve.fill_betweenx(self.las.index,xvals,cut,where=xvals<cut,**left)

        if right is not None:
            axis_curve.fill_betweenx(self.las.index,xvals,cut,where=xvals>cut,**right)

        if cycle is False:
            return

        row = (len(axis_curve.lines) if cycle is True else cycle)*self._label.major

        axis_label.fill_between((self[index].lower,cut),(row,)*2,row+self._label.major,facecolor=left.get('facecolor'))
        axis_label.fill_between((cut,self[index].upper),(row,)*2,row+self._label.major,facecolor=right.get('facecolor'))
        axis_label.text(cut,row+self._label.major/2.,'Unknown',ha='center',va='center')

    def add_shade(self,index:int,mnemo:str,x2:float=0,multp:float=1.,shift:float=0.,cycle:int|bool=True,colormap='Reds',vmin=None,vmax=None,**kwargs):

        axis_curve = self.stage(index)

        x1,x2 = self.las.curves[mnemo].data*multp+shift,x2*multp+shift

        # pig.fill_colormap(wv.axes[13],df.index,df['N05M2A'],x2=1,colormap='brg',vmin=2,vmax=15,zorder=5)
        Pigment.fill_colormap(axis_curve,self.las.index,x1,x2,colormap,vmin,vmax,**kwargs)

        if cycle is False:
            return

        self.add_shade_legend(index,mnemo,multp,shift,cycle,**kwargs)

    def add_shade_legend(self):

        pass

    def add_module(self,index,left:int=None,right:int=None,cycle:int|bool=True,**kwargs):

        axis_module = self.stage(index)

        lines = axis_module.lines

        if left is None:
            y = lines[0].get_ydata()
            x1 = np.ones(y.shape)
        else:
            y = lines[left].get_ydata()
            x1 = lines[left].get_xdata()

        if right is None:
            x2 = 0
        elif right>=len(lines):
            x2 = max(axis_module.get_xlim())
        else:
            x2 = lines[right].get_xdata()

        Pigment.fill_solid(axis_module,y,x1,x2,**kwargs)

        if cycle is False:
            return

    def add_module_legend(self): #correction is required

        axis_label = self.label(index)

        row = (len(axis_curve.lines) if cycle is True else cycle)*self._label.major

        rect = patches.Rectangle((self[index].lower,row),self[index].length,self._label.major,
            fill=True,facecolor=kwargs['facecolor'],hatch=kwargs['hatch'])

        axis_label.add_patch(rect)
        
        axis_label.text(self[index].middle,row+0.5*self._label.major,title,
            ha='center',va='center',backgroundcolor='white',fontsize='small',)

    def add_perfs(self,perfs:pd.DataFrame,year_axis:dict):
        """It includes perforated depth."""

        for _,row in perfs.iterrows():

            bottom,top = wellx.items.Interval.tolist(row["interval"])

            if bottom<self._depth.upper or top>self._depth.lower:
                continue

            upper = top if top>self._depth.upper else self._depth.upper
            lower = bottom if bottom<self._depth.lower else self._depth.lower

            index = year_axis[row['date'].year]

            axis_curve = self.stage(index)

            axis_curve.fill_betweenx((top,bottom),(self[index].lower,)*2,self[index].length,facecolor='gray',zorder=5)
            axis_curve.plot(self[index].limit,(top,)*2,color='white',linewidth=2,zorder=6)

    def add_casings(self):
        """It includes casing set depth."""
        pass

    def view(self,top,wspace=0.0,hspace=0.0,height=30,**kwargs):

        if len(self.axes)==0:
            self.set_axes()

        if kwargs.get("figsize") is None:
            kwargs["figsize"] = ((self.columns)*1.5,6.5)

        self.add_figure(**kwargs)

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