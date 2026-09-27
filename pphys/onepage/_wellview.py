"""WellView: a one-page display of a well's logs.

The layout (tracks, header rows and depth window) comes from
:class:`~pphys.onepage.wellview.Layout` and the axes from
:class:`~pphys.onepage.wellview.Builder`; WellView adds the well data. See
``doc/wellview.md`` for a guide.
"""

import copy
import functools
import itertools
import warnings
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from fractions import Fraction
from typing import Any

import lasio
import numpy as np
import pandas as pd
from matplotlib import cbook, colormaps, patches, ticker
from matplotlib import colors as mcolors
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import PolyCollection
from matplotlib.colors import Colormap
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.transforms import Transform, blended_transform_factory
from scipy.interpolate import interp1d

from ._pigment import Pigment
from .wellview import Builder

# Metres per unit of the depth index, for the scale of the depth track.
_METRES = {"M": 1.0, "FT": 0.3048, "F": 0.3048}

# Date formats tried in turn to label a perforation, longest first.
_DATE_FORMATS = ("%Y-%m-%d", "%Y-%m", "%Y", "%y")


def _drawing(method: Callable) -> Callable:
    """Record a drawing call, so that ``page`` can draw it again.

    Only the outermost call is recorded: ``add_cut`` draws its curve with
    ``add_curve``, and replaying ``add_cut`` draws it again.
    """

    @functools.wraps(method)
    def wrapper(self: "WellView", *args, **kwargs):
        if self._drawing_now:
            return method(self, *args, **kwargs)

        call = (method.__name__, args, dict(kwargs))
        self._drawing_now = True
        try:
            result = method(self, *args, **kwargs)
        finally:
            self._drawing_now = False

        self._calls.append(call)
        return result

    return wrapper


class WellView(Builder):
    """A one-page log display: a Layout, its axes and the well data.

    Parameters
    ----------
    las : lasio.LASFile
        The well log, e.g. from :func:`pphys.read`. Curves are plotted
        against its depth index.
    **kwargs
        Layout keywords: ``ntrail``, ``ncycle``, ``label``, ``depth``,
        ``widths`` and ``heights``.

    Examples
    --------
    >>> view = WellView(read("well.las"), ntrail=3, depth={"limit": (1500, 1600)})
    >>> view.set(1, limit=(0, 150))
    >>> view.set(2, limit=(0.2, 2000), scale="log10")
    >>> view(plt.figure(figsize=(6, 10)))
    >>> view.add_depths(0)
    >>> view.add_curve(1, "GR", color="green")
    >>> view.add_curve(2, "RT", color="black")
    """

    def __init__(self, las: lasio.LASFile, **kwargs):
        self._las = las

        super().__init__(**kwargs)

        self.figure: Figure | None = None
        self._rows: list[set[int]] = []
        self._calls: list[tuple[str, tuple, dict]] = []
        self._drawing_now = False

    @property
    def las(self) -> lasio.LASFile:
        """The well log."""
        return self._las

    def __call__(self, figure: Figure) -> "WellView":
        """Build the tracks on a figure and return the view, ready to draw on."""
        self.axes = super().__call__(figure)
        self.figure = figure

        self._rows = [set() for _ in range(self.ntrail)]
        self._calls = []

        return self

    def label(self, index: int) -> Axes:
        """Return the header axis of a track."""
        if self._label.spot is None:
            raise ValueError("This layout has no header: its label spot is None.")

        if not self.heads:
            raise RuntimeError("Call the WellView with a figure before drawing on it.")

        return self.heads[index]

    def stage(self, index: int) -> Axes:
        """Return the axis of a track, where curves and fills go."""
        if not self.bodies:
            raise RuntimeError("Call the WellView with a figure before drawing on it.")

        return self.bodies[index]

    # Depths, tops, perforations and casings

    @_drawing
    def add_depths(
        self,
        index: int,
        survey: pd.DataFrame | None = None,
        title: str | None = None,
        cycle: int | bool = True,
        scale: bool = True,
        **kwargs,
    ):
        """Write depth values down a depth track.

        Parameters
        ----------
        index : int
            The track, usually one of the depth spots.
        survey : DataFrame, optional
            ``MD`` and ``TVD`` columns. The track then shows TVD values at
            their measured depths, and its ticks follow TVD.
        title : str, optional
            Header text, by default ``MD (unit)`` or ``TVD (unit)``.
        cycle : int or bool, default True
            Header row, see :meth:`add_curve`.
        scale : bool, default True
            Add the print scale, e.g. ``1:500``, under the title.
        **kwargs
            Text properties of the depth values.
        """
        axis = self.stage(index)
        top, base = self._depth.upper, self._depth.lower

        if survey is None:
            values = _inside(
                ticker.MultipleLocator(self._depth.major).tick_values(top, base),
                top,
                base,
            )
            positions = values
            kind = "MD"
        else:
            md, tvd = survey[["MD", "TVD"]].to_numpy(dtype=float).T
            to_tvd = interp1d(md, tvd, fill_value="extrapolate")
            to_md = interp1d(tvd, md, fill_value="extrapolate")

            tvd_top, tvd_base = sorted(to_tvd([top, base]))
            values = _inside(
                ticker.MultipleLocator(self._depth.major).tick_values(
                    tvd_top, tvd_base
                ),
                tvd_top,
                tvd_base,
            )
            minor = ticker.MultipleLocator(self._depth.minor).tick_values(
                tvd_top, tvd_base
            )
            positions = to_md(values)

            axis.set_yticks(positions)
            axis.set_yticks(to_md(minor), minor=True)
            kind = "TVD"

        across = _across(axis)
        for position, value in zip(positions, values, strict=True):
            axis.text(
                0.5,
                position,
                f"{value:.10g}",
                transform=across,
                ha="center",
                va="center",
                **kwargs,
            )

        row = self._row(index, cycle)
        if row is None:
            return

        unit = self.las.curves[0].unit
        text = f"{kind} ({unit})" if title is None else title
        ratio = self._print_scale(axis, unit)
        if scale and ratio is not None:
            text = f"{text}\n1:{ratio:.0f}"

        head = self.label(index)
        head.text(
            0.5,
            self._row_y(row, 0.5),
            text,
            transform=_across(head),
            ha="center",
            va="center",
            fontsize="small",
        )

    @_drawing
    def add_tops(
        self,
        index: int,
        tops: Mapping[str, float] | pd.Series | pd.DataFrame,
        title: str | None = None,
        text_dict: dict | None = None,
        **kwargs,
    ):
        """Colour the formations between tops across a track and name them.

        Parameters
        ----------
        index : int
            The track.
        tops : dict, Series or DataFrame
            ``{name: depth}``, a Series of depths indexed by name, or a
            DataFrame with ``formation`` and ``depth`` columns and optionally
            ``facecolor``. Each formation runs to the next top, the last one
            to the base of the window. Nothing is drawn above the first top.
        title : str, optional
            Header text, written vertically.
        text_dict : dict, optional
            Text properties of the names, which are written vertically where
            they fit, in black or white for contrast.
        **kwargs
            Patch properties of the fills, e.g. ``alpha`` or ``hatch``.
        """
        axis = self.stage(index)
        frame = _tops_table(tops)
        bases = frame["depth"].shift(-1).fillna(self._depth.lower)

        text_dict = {"fontsize": "small", "fontweight": "bold", **(text_dict or {})}

        for name, top, facecolor, base in zip(
            frame["formation"], frame["depth"], frame["facecolor"], bases, strict=True
        ):
            upper, lower = max(top, self._depth.upper), min(base, self._depth.lower)
            if lower <= upper:
                continue

            span = axis.axhspan(upper, lower, **{"facecolor": facecolor, **kwargs})

            if self._fits(axis, upper, lower, name, text_dict["fontsize"]):
                axis.text(
                    0.5,
                    (upper + lower) / 2,
                    name,
                    transform=_across(axis),
                    rotation=90,
                    ha="center",
                    va="center",
                    color=_text_color(span.get_facecolor()),
                    zorder=span.get_zorder() + 1,
                    **text_dict,
                )

        if title is not None:
            self._title(index, title)

    @_drawing
    def add_perfs(
        self,
        index: int,
        perfs: pd.DataFrame,
        year_axis: dict[int, int] | None = None,
        date_text_dict: dict | None = None,
        date_text_coeff: float = 1.0,
        sep_line: bool = False,
        title: str | None = None,
        **kwargs,
    ):
        """Mark perforated intervals across a track.

        Parameters
        ----------
        index : int
            The track.
        perfs : DataFrame
            ``top`` and ``base`` columns and optionally ``date``. Each
            interval is labelled with its date in the longest form that fits:
            2024-05-17, 2024-05, 2024 or 24.
        year_axis : dict, optional
            ``{year: track}`` to put each perforation in the track of its
            year; other years, and intervals without a date, go to ``index``.
        date_text_dict : dict, optional
            Text properties of the dates.
        date_text_coeff : float, default 1
            Scales the room a date needs; above 1 writes fewer dates.
        sep_line : bool, default False
            Draw a white line at the top of each interval, to separate
            adjacent ones.
        title : str, optional
            Header text, written vertically. With ``year_axis``, each year
            track gets ``"title year"``.
        **kwargs
            Patch properties of the intervals; ``facecolor`` defaults to
            black.
        """
        frame = _table(perfs, ("top", "base"), "perfs", numeric=("top", "base"))
        dates = (
            pd.to_datetime(frame["date"])
            if "date" in frame
            else pd.Series(pd.NaT, index=frame.index)
        )

        kwargs.setdefault("facecolor", "black")
        text_dict = {
            "fontsize": "x-small",
            "color": _text_color(kwargs["facecolor"]),
            **(date_text_dict or {}),
        }

        for top, base, date in zip(frame["top"], frame["base"], dates, strict=True):
            upper = max(min(top, base), self._depth.upper)
            lower = min(max(top, base), self._depth.lower)
            if lower <= upper:
                continue

            track = index
            if year_axis is not None and not pd.isna(date):
                track = year_axis.get(date.year, index)

            axis = self.stage(track)
            span = axis.axhspan(upper, lower, **kwargs)

            if not pd.isna(date):
                for form in _DATE_FORMATS:
                    text = date.strftime(form)
                    if self._fits(
                        axis, upper, lower, text, text_dict["fontsize"], date_text_coeff
                    ):
                        axis.text(
                            0.5,
                            (upper + lower) / 2,
                            text,
                            transform=_across(axis),
                            rotation=90,
                            ha="center",
                            va="center",
                            zorder=span.get_zorder() + 1,
                            **text_dict,
                        )
                        break

            if sep_line:
                axis.axhline(
                    upper, color="white", linewidth=2, zorder=span.get_zorder() + 1
                )

        if title is not None:
            titles = {
                track: f"{title} {year}" for year, track in (year_axis or {}).items()
            }
            titles.setdefault(index, title)
            for track, text in titles.items():
                self._title(track, text)

    @_drawing
    def add_casings(
        self,
        index: int,
        casings: pd.DataFrame | Iterable[Mapping[str, Any]],
        title: str | None = None,
        **kwargs,
    ):
        """Sketch the casing strings in a track: walls, shoes and diameters.

        Parameters
        ----------
        index : int
            The track.
        casings : DataFrame or list of dicts
            ``od`` (outside diameter in inches, a number or text such as
            ``"9 5/8"``) and ``base`` (shoe depth), and optionally ``top``
            (the hanger depth of a liner; by default the string runs from
            above the window). Strings are nested by diameter, the largest
            outermost.
        title : str, optional
            Header text, written vertically.
        **kwargs
            Line properties of the walls; the shoes take their colour.
        """
        frame = _table(
            pd.DataFrame(casings), ("od", "base"), "casings", ("base", "top")
        )
        frame["inches"] = frame["od"].map(_inches)
        frame = frame.sort_values("inches", ascending=False)

        kwargs = cbook.normalize_kwargs(kwargs, Line2D)
        kwargs.setdefault("color", "black")
        kwargs.setdefault("linewidth", 1.5)

        axis = self.stage(index)
        across = _across(axis)
        largest = frame["inches"].max()
        shoe = 0.015 * self._depth.length

        for row in frame.itertuples():
            top = self._depth.upper if pd.isna(getattr(row, "top", np.nan)) else row.top
            upper, lower = max(top, self._depth.upper), min(row.base, self._depth.lower)
            if lower <= upper:
                continue

            half = 0.4 * row.inches / largest
            for side in (-1, 1):
                wall = 0.5 + side * half
                axis.plot((wall, wall), (upper, lower), transform=across, **kwargs)

                if row.base <= self._depth.lower:
                    axis.add_patch(
                        patches.Polygon(
                            [
                                (wall, row.base),
                                (wall + side * 0.08, row.base),
                                (wall, row.base - shoe),
                            ],
                            closed=True,
                            transform=across,
                            facecolor=kwargs["color"],
                            edgecolor=kwargs["color"],
                        )
                    )

            if row.base <= self._depth.lower:
                axis.text(
                    0.5,
                    row.base,
                    f'{_od_text(row.od)}"',
                    transform=across,
                    ha="center",
                    va="bottom",
                    fontsize="x-small",
                )

        if title is not None:
            self._title(index, title)

    def add_title(self, index: int, text: str, rotation: float = 90, **kwargs):
        """Write a title across a track's whole header, vertical by default."""
        head = self.label(index)
        head.text(
            0.5,
            0.5,
            text,
            transform=head.transAxes,
            rotation=rotation,
            ha="center",
            va="center",
            **{"fontsize": "small", **kwargs},
        )

    # Curves and fills

    @_drawing
    def add_curve(
        self,
        index: int,
        mnemo: str,
        multp: float = 1.0,
        shift: float = 0.0,
        cycle: int | bool = True,
        title: str | None = None,
        **kwargs,
    ) -> Line2D:
        """Plot a curve in a track and list it in the header.

        Parameters
        ----------
        index : int
            The track.
        mnemo : str
            The curve mnemonic.
        multp, shift : float
            The curve is plotted as ``value * multp + shift``, to put it on
            another track's scale; the header shows the curve values at the
            track edges.
        cycle : int or bool, default True
            The header row: True takes the next free row, an int takes that
            row (0 is next to the track), False writes no header entry.
        title : str, optional
            Header name, by default the mnemonic.
        **kwargs
            Line properties, e.g. ``color`` or ``linewidth``.

        Returns
        -------
        Line2D
            The curve.
        """
        values = self._values(mnemo, multp, shift)
        (line,) = self.stage(index).plot(values, self.las.index, **kwargs)

        legend = {
            **cbook.normalize_kwargs(kwargs, Line2D),
            "color": line.get_color(),
            "linewidth": 2 * line.get_linewidth(),
        }
        self.add_curve_legend(index, mnemo, multp, shift, cycle, title, **legend)

        return line

    @_drawing
    def add_curve_legend(
        self,
        index: int,
        mnemo: str,
        multp: float = 1.0,
        shift: float = 0.0,
        cycle: int | bool = True,
        title: str | None = None,
        **kwargs,
    ):
        """Write a curve's header row: its line, name, unit and edge values."""
        row = self._row(index, cycle)
        if row is None:
            return

        self._legend(index, row, mnemo, multp, shift, title, **kwargs)

    @_drawing
    def add_cut(
        self,
        index: int,
        mnemo: str,
        cut: float,
        multp: float = 1.0,
        shift: float = 0.0,
        left: Mapping[str, Any] | None = None,
        right: Mapping[str, Any] | None = None,
        cycle: int | bool = True,
        title: str | None = None,
        **kwargs,
    ) -> Line2D:
        """Plot a curve and shade it on either side of a cut-off.

        For example sand and shale either side of a gamma-ray cut-off.

        Parameters
        ----------
        index, mnemo, multp, shift, title
            As in :meth:`add_curve`.
        cut : float
            The cut-off, in curve units.
        left, right : dict or FillStyle, optional
            Fill style of the area between the curve and the cut-off where the
            curve lies left or right of it on screen, e.g.
            ``{"facecolor": "gold"}`` or ``Lithology.sandstone``.
        cycle : int or bool, default True
            Header row, split at the cut-off into the two fill styles.
        **kwargs
            Line properties of the curve.

        Returns
        -------
        Line2D
            The curve.
        """
        line = self.add_curve(index, mnemo, multp, shift, False, title, **kwargs)

        values = np.asarray(line.get_xdata(), dtype=float)
        edge = cut * multp + shift
        with np.errstate(invalid="ignore"):
            below, above = values < edge, values > edge
        on_left, on_right = (above, below) if self[index].flipped else (below, above)

        axis = self.stage(index)
        for style, where in ((left, on_left), (right, on_right)):
            if style is not None:
                Pigment.fill_solid(
                    axis,
                    self.las.index,
                    values,
                    edge,
                    where=where,
                    interpolate=True,
                    **style,
                )

        row = self._row(index, cycle)
        if row is None:
            return line

        head = self.label(index)
        first, last = self[index].limit
        for style, span in ((left, (first, edge)), (right, (edge, last))):
            if style is not None:
                self._box(head, row, *span, dict(**style))

        legend = {"color": line.get_color(), "linewidth": 2 * line.get_linewidth()}
        self._legend(index, row, mnemo, multp, shift, title, **legend)

        return line

    @_drawing
    def add_shade(
        self,
        index: int,
        mnemo: str,
        x2: float | np.ndarray = 0.0,
        multp: float = 1.0,
        shift: float = 0.0,
        cycle: int | bool = True,
        colormap: str | Colormap = "Reds",
        vmin: float | None = None,
        vmax: float | None = None,
        title: str | None = None,
        **kwargs,
    ) -> AxesImage | None:
        """Fill between a curve and a baseline with colours that follow the curve.

        Parameters
        ----------
        index, mnemo, multp, shift, cycle
            As in :meth:`add_curve`.
        x2 : float or array, default 0
            The baseline, in curve units.
        colormap : str or Colormap, default "Reds"
            The colour map; logarithmic on a log10 track.
        vmin, vmax : float, optional
            Curve values at the ends of the colour map, by default the
            curve's range.
        title : str, optional
            Header text over the colour bar, by default the mnemonic.
        **kwargs
            Image properties, e.g. ``alpha``.

        Returns
        -------
        AxesImage or None
            The colour fill; None if the curve has fewer than two values.
        """
        values = self._values(mnemo, multp, shift)
        baseline = np.asarray(x2, dtype=float) * multp + shift
        norm = self._norm(index, values, vmin, vmax, multp, shift)

        image = Pigment.fill_colormap(
            self.stage(index),
            self.las.index,
            values,
            baseline,
            colormap,
            norm.vmin,
            norm.vmax,
            **kwargs,
        )

        row = self._row(index, cycle)
        if row is not None and image is not None:
            self._colour_bar(
                index, row, colormap, norm, mnemo if title is None else title
            )

        return image

    @_drawing
    def add_module(
        self,
        index: int,
        left: int | None = None,
        right: int | None = None,
        cycle: int | bool = True,
        title: str | None = None,
        **kwargs,
    ) -> PolyCollection:
        """Fill between two plotted curves, or a curve and a track edge.

        Parameters
        ----------
        index : int
            The track.
        left, right : int, optional
            The curves bounding the fill, as indices of the lines already
            plotted on the track (in plotting order). None is the left or the
            right edge of the track.
        cycle : int or bool, default True
            The header row, see :meth:`add_curve`. It shows the fill style.
        title : str, optional
            Header text, by default the style's label.
        **kwargs
            A fill style, e.g. ``**Lithology.limestone``, or the keywords of
            :meth:`Pigment.fill_solid`.

        Returns
        -------
        PolyCollection
            The fill.
        """
        axis = self.stage(index)
        first, last = self[index].limit

        if left is None and right is None:
            depth = self.las.index
        else:
            depth = _line(axis, index, right if left is None else left).get_ydata()

        x1 = first if left is None else _line(axis, index, left).get_xdata()
        x2 = last if right is None else _line(axis, index, right).get_xdata()

        fill = Pigment.fill_solid(axis, depth, x1, x2, **kwargs)

        row = self._row(index, cycle)
        if row is None:
            return fill

        head = self.label(index)
        self._box(
            head,
            row,
            first,
            last,
            {
                "facecolor": fill.get_facecolor()[0],
                "hatch": fill.get_hatch(),
                "motifs": kwargs.get("motifs"),
            },
        )

        text = kwargs.get("label", "") if title is None else title
        if text:
            head.text(
                0.5,
                self._row_y(row, 0.5),
                text,
                transform=_across(head),
                ha="center",
                va="center",
                fontsize="small",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
            )

        return fill

    # Pages

    def page(self, top: float, base: float, figure: Figure | None = None) -> "WellView":
        """Return a view of another depth window with the same drawings.

        Everything drawn with WellView methods is drawn again for the new
        window, so motifs, colour fills and text are sized for it. Artists
        added straight to the axes are not carried over.

        Parameters
        ----------
        top, base : float
            The depth window.
        figure : Figure, optional
            Where to draw, by default a new figure of the same size.
        """
        if self.figure is None:
            raise RuntimeError("Call the WellView with a figure before paging it.")

        view = copy.copy(self)
        view._depth = replace(self._depth, limit=(top, base))
        view._xaxes = list(self._xaxes)
        view._calls = []
        view._drawing_now = False

        if figure is None:
            figure = plt.figure(figsize=self.figure.get_size_inches())

        view(figure)

        for name, args, kwargs in self._calls:
            getattr(view, name)(*args, **kwargs)

        return view

    def save(self, filepath, step: float | None = None, **kwargs):
        """Save the view to a file.

        Parameters
        ----------
        filepath : str or path
            The file; its extension sets the format.
        step : float, optional
            Split the depth window into pages of this length, written to one
            PDF. Every page is drawn again for its window and has the same
            size, so the depth scale is the same on all of them.
        **kwargs
            Passed to ``savefig``, e.g. ``dpi`` or ``bbox_inches``.
        """
        if self.figure is None:
            raise RuntimeError("Call the WellView with a figure before saving it.")

        if step is None:
            self.figure.savefig(filepath, **kwargs)
            return

        if step <= 0:
            raise ValueError("step must be positive.")

        size = self.figure.get_size_inches()
        with PdfPages(filepath) as pdf:
            for top in np.arange(self._depth.upper, self._depth.lower, step):
                page = self.page(top, top + step, figure=Figure(figsize=size))
                pdf.savefig(page.figure, **kwargs)

    # Helpers

    def _curve(self, mnemo: str) -> lasio.CurveItem:
        """Return a curve of the log, with a helpful error if it is missing."""
        try:
            return self.las.curves[mnemo]
        except KeyError:
            names = ", ".join(curve.mnemonic for curve in self.las.curves)
            raise KeyError(f"No curve {mnemo!r} in the log; it has {names}.") from None

    def _values(self, mnemo: str, multp: float, shift: float) -> np.ndarray:
        """Return a curve's values on its track's scale."""
        if multp == 0:
            raise ValueError("multp must not be zero.")

        return np.asarray(self._curve(mnemo).data, dtype=float) * multp + shift

    def _row(self, index: int, cycle: int | bool) -> int | None:
        """Reserve a header row of a track; None for no header entry."""
        if cycle is False or self._label.spot is None:
            return None

        used = self._rows[index]
        if cycle is True:
            row = next(row for row in itertools.count() if row not in used)
        else:
            row = int(cycle)

        used.add(row)

        if not 0 <= row < self.ncycle:
            warnings.warn(
                f"Header row {row} of track {index} is not shown: the header has "
                f"{self.ncycle} rows (ncycle).",
                stacklevel=3,
            )

        return row

    def _row_y(self, row: int, fraction: float) -> float:
        """Return the header y at a fraction of a row's height, upwards on screen."""
        if self._label.spot == "bottom":  # the header axis is flipped
            return (row + 1 - fraction) * self._label.major

        return (row + fraction) * self._label.major

    def _legend(
        self,
        index: int,
        row: int,
        mnemo: str,
        multp: float,
        shift: float,
        title: str | None,
        **kwargs,
    ):
        """Draw a curve's line, name, unit and edge values in a header row."""
        head = self.label(index)
        across = _across(head)

        kwargs.setdefault("color", "black")
        head.plot((0.0, 1.0), (self._row_y(row, 0.4),) * 2, transform=across, **kwargs)

        text = {"transform": across, "fontsize": "small", "color": kwargs["color"]}
        upper, lower = self._row_y(row, 0.45), self._row_y(row, 0.35)

        head.text(
            0.5,
            upper,
            mnemo if title is None else title,
            ha="center",
            va="bottom",
            **text,
        )
        head.text(0.5, lower, self._curve(mnemo).unit, ha="center", va="top", **text)

        first, last = ((value - shift) / multp for value in self[index].limit)
        head.text(0.02, upper, f"{first:.5g}", ha="left", va="bottom", **text)
        head.text(0.98, upper, f"{last:.5g}", ha="right", va="bottom", **text)

    def _box(self, head: Axes, row: int, x0: float, x1: float, style: dict):
        """Draw a fill style from x0 to x1 (track values) over a header row."""
        major = self._label.major
        box = patches.Rectangle(
            (x0, row * major),
            x1 - x0,
            major,
            facecolor=style.get("facecolor"),
            hatch=style.get("hatch"),
            alpha=style.get("alpha"),
        )
        head.add_patch(box)
        Pigment.add_motifs(head, box, style.get("motifs"))

    def _norm(
        self,
        index: int,
        values: np.ndarray,
        vmin: float | None,
        vmax: float | None,
        multp: float,
        shift: float,
    ) -> mcolors.Normalize:
        """Return the colour scale of a shade, in track values."""
        log = self[index].scale == "log10"
        known = values[np.isfinite(values) & (values > 0 if log else True)]

        lower = known.min() if vmin is None and known.size else np.nan
        upper = known.max() if vmax is None and known.size else np.nan
        if vmin is not None:
            lower = vmin * multp + shift
        if vmax is not None:
            upper = vmax * multp + shift

        lower, upper = sorted((lower, upper))

        return (mcolors.LogNorm if log else mcolors.Normalize)(vmin=lower, vmax=upper)

    def _colour_bar(
        self,
        index: int,
        row: int,
        colormap: str | Colormap,
        norm: mcolors.Normalize,
        title: str,
    ):
        """Draw a shade's colours along a header row, under its title.

        Each position has the colour a curve value there would get.
        """
        head = self.label(index)
        first, last = self[index].limit
        spread = np.geomspace if self[index].scale == "log10" else np.linspace
        colours = colormaps.get_cmap(colormap)(norm(spread(first, last, 256)))

        major = self._label.major
        bar = AxesImage(
            head, extent=(0.0, 1.0, row * major, (row + 1) * major), origin="lower"
        )
        bar.set_transform(_across(head))
        bar.set_data(colours[np.newaxis, :, :])
        head.add_image(bar)

        head.text(
            0.5,
            self._row_y(row, 0.5),
            title,
            transform=_across(head),
            ha="center",
            va="center",
            fontsize="small",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
        )

    def _title(self, index: int, text: str):
        """Write a vertical title in a track's header, if there is a header."""
        if self._label.spot is not None:
            self.add_title(index, text)

    def _fits(
        self,
        axis: Axes,
        upper: float,
        lower: float,
        text: str,
        fontsize: float | str,
        coeff: float = 1.0,
    ) -> bool:
        """Return whether text written vertically fits between two depths."""
        x = axis.get_xlim()[0]
        (_, y0), (_, y1) = axis.transData.transform([(x, upper), (x, lower)])
        room = abs(y1 - y0) * 72.0 / axis.figure.dpi

        size = FontProperties(size=fontsize).get_size_in_points()

        return room >= coeff * size * (0.6 * len(text) + 1.0)

    def _print_scale(self, axis: Axes, unit: str) -> float | None:
        """Return the depth scale of the print, e.g. 500 for 1:500."""
        metres = _METRES.get(str(unit).strip().upper())
        if metres is None:
            return None

        height = axis.get_window_extent().height / axis.figure.dpi * 0.0254

        return self._depth.length * metres / height


def _across(axis: Axes) -> Transform:
    """Return a transform with x in axes fractions and y in data units."""
    return blended_transform_factory(axis.transAxes, axis.transData)


def _inside(values: np.ndarray, lower: float, upper: float) -> np.ndarray:
    """Return the values strictly between two limits."""
    return values[(values > lower) & (values < upper)]


def _line(axis: Axes, index: int, number: int) -> Line2D:
    """Return a line plotted on a track, with a helpful error if it is missing."""
    try:
        return axis.lines[number]
    except IndexError:
        raise IndexError(
            f"Track {index} has {len(axis.lines)} lines, no line {number}: plot the "
            f"curves before filling between them."
        ) from None


def _table(
    frame: pd.DataFrame,
    columns: tuple[str, ...],
    name: str,
    numeric: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Return a copy of a table after checking its columns.

    The numeric columns are converted to float.
    """
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} needs the columns {missing}.")

    frame = frame.copy()
    for column in numeric:
        if column in frame:
            frame[column] = frame[column].astype(float)

    return frame


def _tops_table(tops: Mapping[str, float] | pd.Series | pd.DataFrame) -> pd.DataFrame:
    """Return tops as formation, depth and facecolor columns, sorted by depth."""
    if isinstance(tops, pd.DataFrame):
        frame = _table(tops, ("formation", "depth"), "tops")
    elif isinstance(tops, pd.Series):
        frame = pd.DataFrame(
            {"formation": tops.index, "depth": tops.to_numpy(dtype=float)}
        )
    elif isinstance(tops, Mapping):
        frame = pd.DataFrame({"formation": list(tops), "depth": list(tops.values())})
    else:
        raise TypeError("tops must be a dict, Series or DataFrame.")

    frame["formation"] = frame["formation"].astype(str)
    frame["depth"] = frame["depth"].astype(float)

    palette = colormaps["tab20"]
    defaults = pd.Series(
        [palette(n % palette.N) for n in range(len(frame))], index=frame.index
    )
    if "facecolor" in frame:
        frame["facecolor"] = frame["facecolor"].where(
            frame["facecolor"].notna(), defaults
        )
    else:
        frame["facecolor"] = defaults

    return frame.sort_values("depth", kind="stable").reset_index(drop=True)


def _text_color(facecolor) -> str:
    """Return black or white, whichever reads better on a colour."""
    red, green, blue, alpha = mcolors.to_rgba(facecolor)
    if alpha < 0.5:
        return "black"

    return "black" if 0.299 * red + 0.587 * green + 0.114 * blue > 0.5 else "white"


def _inches(od: float | str) -> float:
    """Return a diameter in inches from a number or text such as '9 5/8'."""
    if isinstance(od, str):
        parts = od.replace('"', "").replace("-", " ").split()
        return float(sum(Fraction(part) for part in parts))

    return float(od)


def _od_text(od: float | str) -> str:
    """Return a diameter as casing people write it, e.g. 9 5/8."""
    if isinstance(od, str):
        return od.replace('"', "").strip()

    whole, part = divmod(Fraction(float(od)).limit_denominator(16), 1)

    return f"{whole} {part}" if part else f"{whole}"
