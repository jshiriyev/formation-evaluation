from typing import cast

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

    def add_depths(self,index:int,survey:pd.DataFrame|None=None,**kwargs):
        """Add depth annotations or MD-transformed ticks to the specified axis."""

        axis = self.stage(index)

        md_min = self._depth.upper
        md_max = self._depth.lower

        loc_major = ticker.MultipleLocator(self._depth.major)
        loc_minor = ticker.MultipleLocator(self._depth.minor)

        if survey is None:
            yticks_major = loc_major.tick_values(md_min,md_max)
            # If no survey is provided, annotate MD ticks directly
            for ytick in yticks_major[2:-2]:
                axis.annotate(f"{ytick:4.0f}",
                    xy=(self[index].middle,ytick),ha='center',va='center',
                    **kwargs
                )
            return

        md,tvd = survey[['MD','TVD']].to_numpy().T

        limit = interp1d(md,tvd,kind='linear',fill_value="extrapolate")((md_min,md_max)) # type: ignore

        yticks_major = loc_major.tick_values(*limit)
        yticks_minor = loc_minor.tick_values(*limit)

        # axis.tick_params(which='minor',length=0)

        yticks_major = yticks_major[np.logical_and(yticks_major>=limit[0],yticks_major<=limit[1])]
        yticks_minor = yticks_minor[np.logical_and(yticks_minor>=limit[0],yticks_minor<=limit[1])]

        yticks_major_md = interp1d(tvd,md,kind='linear',fill_value="extrapolate")(yticks_major) # type: ignore
        yticks_minor_md = interp1d(tvd,md,kind='linear',fill_value="extrapolate")(yticks_minor) # type: ignore

        axis.set_yticks(yticks_major_md,minor=False)
        axis.set_yticks(yticks_minor_md,minor=True)

        for ytick_md,ytick in zip(yticks_major_md,yticks_major):
            axis.annotate(
                f"{ytick:4.0f}",xy=(self[index].middle,ytick_md),ha='center',va='center'
                ,**kwargs
            )

        # axis.set_yticklabels(yticks_major)

    def add_tops(self,index,formation_tops:pd.DataFrame,text_dict=None,**kwargs):

        axis_curve = self.stage(index)

        tops = formation_tops.copy(deep=True)

        if 'formation' not in tops.columns:
            raise Warning("The 'formation' column is required in tops DataFrame.")
        
        tops['formation'] = tops['formation'].astype(str)

        if 'depth' not in tops.columns:
            raise Warning("The 'depth' column is required in tops DataFrame.")
        
        tops['depth'] = tops['depth'].astype(float)

        if 'facecolor' not in tops.columns:
            cmap = plt.get_cmap('tab20')
            tops['facecolor'] = [
                cmap(i % cmap.N) for i in range(len(tops))
            ]

        new_rows = pd.DataFrame([
            {"formation": None, "depth": self._depth.upper, "facecolor": None},
            {"formation": None, "depth": self._depth.lower, "facecolor": None}
        ])

        tops = (
            pd.concat([tops, new_rows], ignore_index=True)
            .sort_values("depth", kind="mergesort")   # stable sort
            .reset_index(drop=True)
            .ffill()
        )

        tops["depth_next"] = tops["depth"].shift(-1)

        mask = (tops["depth"] >= self._depth.upper) & (tops["depth"] < self._depth.lower)
        shortlist = tops.loc[mask].copy()

        for row in shortlist.itertuples():

            upper = cast(float, row.depth)
            lower = cast(float, row.depth_next)

            axis_curve.fill_betweenx((upper,lower),
                (self[index].lower,)*2,self[index].length,facecolor=row.facecolor,**kwargs)

            name = "Unknown" if row.formation is None else str(row.formation)

            if len(name)*1.5<(lower-upper):

                base_zorder = kwargs.get('zorder')
                zorder = None if base_zorder is None else base_zorder + 1

                if row.facecolor is None:
                    color = 'black'
                else:
                    r,g,b = [x*255 for x in to_rgb(cast(str, row.facecolor))]
                    brightness = 0.299*r+0.587*g+0.114*b
                    color = "black" if brightness > 128 else "white"

                axis_curve.text(self[index].middle,(upper+lower)/2,name,
                    color=color,rotation=90,ha='center',va='center',zorder=zorder,**(text_dict or {}))

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

    def add_cut(
        self,
        index : int,
        mnemo : str,
        cut : float,
        multp : float=1.,
        shift : float=0.,
        left : dict | None = None,
        right : dict | None = None,
        cycle : int | bool = True,
        **kwargs
        ):
        
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

        facecolor_left = left.get('facecolor') if left is not None else 'white'
        facecolor_right = right.get('facecolor') if right is not None else 'white'

        axis_label.fill_between((self[index].lower,cut),(row,)*2,row+self._label.major,facecolor=facecolor_left)
        axis_label.fill_between((cut,self[index].upper),(row,)*2,row+self._label.major,facecolor=facecolor_right)

        axis_label.text(cut,row+self._label.major/2.,'Unknown',ha='center',va='center')

    def add_shade(
        self,
        index : int,
        mnemo : str,
        x2 : float = 0,
        multp : float = 1.,
        shift : float = 0.,
        cycle : int|bool = True,
        colormap = 'Reds',
        vmin = None,
        vmax = None,
        **kwargs
        ):

        axis_curve = self.stage(index)
        axis_label = self.label(index)

        x1,x2 = self.las.curves[mnemo].data*multp+shift,x2*multp+shift

        # pig.fill_colormap(wv.axes[13],df.index,df['N05M2A'],x2=1,colormap='brg',vmin=2,vmax=15,zorder=5)
        Pigment.fill_colormap(axis_curve,self.las.index,x1,x2,colormap,vmin,vmax,**kwargs)

        if cycle is False:
            return
        
        row = (len(axis_curve.lines) if cycle is True else cycle)*self._label.major

        axis_label.text(self[index].middle,row-0.5*self._label.major,f"{mnemo}",ha='center',fontsize='small',)

    def add_module(
        self,
        index,
        left:int | None = None,
        right:int | None = None,
        cycle:int | bool=True,
        title:str = "Unknown",
        **kwargs
        ):

        axis_module = self.stage(index)

        lines = axis_module.lines

        if left is None:
            y = cast(np.ndarray, lines[0].get_ydata())
            x1 = np.ones(y.shape)
        else:
            y = cast(np.ndarray, lines[left].get_ydata())
            x1 = cast(np.ndarray, lines[left].get_xdata())

        if right is None:
            x2 = 0
        elif right>=len(lines):
            x2 = max(axis_module.get_xlim())
        else:
            x2 = cast(np.ndarray, lines[right].get_xdata())

        Pigment.fill_solid(axis_module,y,x1,x2,**kwargs)

        if cycle is False:
            return

        axis_label = self.label(index)

        row = (len(axis_module.lines) if cycle is True else cycle)*self._label.major

        rect = patches.Rectangle((self[index].lower,row),self[index].length,self._label.major,
            fill=True,facecolor=kwargs['facecolor'],hatch=kwargs['hatch'])

        axis_label.add_patch(rect)
        
        axis_label.text(self[index].middle,row+0.5*self._label.major,title,
            ha='center',va='center',backgroundcolor='white',fontsize='small',)

    def add_perfs(
        self,
        index:int,
        perfs:pd.DataFrame,
        year_axis:dict|None=None,
        date_text_dict:dict|None=None,
        date_text_coeff:float=1.0,
        sep_line:bool=False,
        **kwargs
        ):
        """It includes perforated depth."""

        perfs = perfs.copy(deep=True)

        if 'top' not in perfs.columns:
            raise Warning("The 'top' column is required in tops DataFrame.")
        
        perfs['top'] = perfs['top'].astype(float)

        if 'base' not in perfs.columns:
            raise Warning("The 'base' column is required in tops DataFrame.")
        
        perfs['base'] = perfs['base'].astype(float)

        no_date_info = True if 'date' not in perfs.columns else False

        for _,row in perfs.iterrows():

            base,top = row['base'],row['top']

            if base<self._depth.upper or top>self._depth.lower:
                continue

            upper = top if top>self._depth.upper else self._depth.upper
            lower = base if base<self._depth.lower else self._depth.lower
            
            if year_axis is not None and not no_date_info:
                index = year_axis[row['date'].year]

            axis_curve = self.stage(index)

            axis_curve.fill_betweenx((upper,lower),(self[index].lower,)*2,self[index].length,**kwargs)

            if not no_date_info:

                if (lower-upper)>10*date_text_coeff:
                    text = f"{row['date'].strftime('%Y-%m-%d')}"
                elif (lower-upper)>7*date_text_coeff:
                    text = f"{row['date'].strftime('%Y-%m')}"
                elif (lower-upper)>4*date_text_coeff:
                    text = f"{row['date'].strftime('%Y')}"
                elif (lower-upper)>2*date_text_coeff:
                    text = f"{row['date'].strftime('%y')}"
                else:
                    text = ""

                axis_curve.text(
                    self[index].middle,(upper+lower)/2.,text,
                    ha='center',va='center',rotation=90,
                    **(date_text_dict or {})
                )

            if sep_line is False:
                continue

            base_zorder = kwargs.get('zorder')
            zorder = None if base_zorder is None else base_zorder + 1
            
            axis_curve.plot(self[index].limit,(upper,)*2,color='white',linewidth=2,zorder=zorder)

    def add_casings(self):
        """It includes casing set depth."""
        pass

    def show(self,top,wspace=0.0,hspace=0.0,height=30,**kwargs):
        pass

    def save(self,filepath,wspace=0.0,hspace=0.0,**kwargs):
        """It saves the WellView as a multipage pdf file."""
        pass