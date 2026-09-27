"""Fills for log tracks: colours, hatches, motifs and colour maps.

:class:`Pigment` gathers static methods that paint on a matplotlib axis in
data coordinates, with depth on the y axis:

- :meth:`Pigment.fill_solid` fills between two curves with a colour, a hatch
  and motifs, e.g. ``**Lithology.limestone``;
- :meth:`Pigment.fill_colormap` fills between a curve and a baseline with
  colours that follow the curve, e.g. a gamma-ray shading;
- :meth:`Pigment.add_motifs` tiles motifs inside any fill or patch.

Motifs are sized in points and tiled over the visible part of a fill, so set
the axis limits and the figure layout before filling. The fills are meant for
static figures.
"""

from collections.abc import Iterable

import numpy as np
from matplotlib import colormaps
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.collections import Collection, PolyCollection
from matplotlib.colors import Colormap
from matplotlib.image import AxesImage
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path
from matplotlib.transforms import Affine2D, Bbox
from numpy.typing import ArrayLike

from ._motifs import MotifPattern

# The most image rows a colour-map fill is sampled with.
_MAX_ROWS = 100_000


class Pigment:
    """Static methods that add colours, hatches and motifs to an axis."""

    @staticmethod
    def fill_solid(
        axis: Axes,
        y: ArrayLike,
        x1: ArrayLike,
        x2: ArrayLike = 0.0,
        motifs: MotifPattern | Iterable[MotifPattern] | None = None,
        **kwargs,
    ) -> PolyCollection:
        """Fill between two curves with a colour, a hatch and motifs.

        Parameters
        ----------
        axis : Axes
            The track to draw on.
        y : array_like
            Depths.
        x1, x2 : array_like or float
            The curves, or constant values, to fill between. A missing value
            (NaN) leaves a gap.
        motifs : MotifPattern or iterable of MotifPattern, optional
            Motifs tiled inside the fill, see :meth:`add_motifs`.
        **kwargs
            Passed to :meth:`~matplotlib.axes.Axes.fill_betweenx`, e.g.
            ``facecolor``, ``hatch``, ``label``, ``alpha``, ``zorder`` or
            ``where``. A fill style unpacks into them:
            ``**Lithology.limestone``. Colours are listed at
            https://matplotlib.org/stable/users/explain/colors/colors.html
            and hatches at
            https://matplotlib.org/stable/gallery/shapes_and_collections/hatch_style_reference.html.

        Returns
        -------
        PolyCollection
            The fill.

        Examples
        --------
        Shade the neutron-density crossover, where density porosity exceeds
        neutron porosity:

        >>> Pigment.fill_solid(
        ...     axis, depth, nphi, dphi, where=dphi > nphi, interpolate=True,
        ...     facecolor="gold",
        ... )
        """
        fill = axis.fill_betweenx(y, x1, x2, **kwargs)
        Pigment.add_motifs(axis, fill, motifs)
        return fill

    @staticmethod
    def fill_colormap(
        axis: Axes,
        y: ArrayLike,
        x1: ArrayLike,
        x2: ArrayLike = 0.0,
        colormap: str | Colormap = "Reds",
        vmin: float | None = None,
        vmax: float | None = None,
        **kwargs,
    ) -> AxesImage | None:
        """Fill between a curve and a baseline with colours that follow the curve.

        Each depth is coloured by the curve's value there, e.g. a gamma-ray
        shading from clean to shaly. The colours follow a logarithmic scale
        on a logarithmic track.

        Parameters
        ----------
        axis : Axes
            The track to draw on.
        y : array_like
            Depths, in any order and spacing.
        x1 : array_like
            The curve, which also sets the colours. A missing value (NaN)
            leaves a gap.
        x2 : array_like or float, default 0
            The baseline: a constant or a second curve.
        colormap : str or Colormap, default "Reds"
            The colour map, see
            https://matplotlib.org/stable/users/explain/colors/colormaps.html.
        vmin, vmax : float, optional
            The curve values at the ends of the colour map; by default the
            curve's range.
        **kwargs
            Passed to the :class:`~matplotlib.image.AxesImage`, e.g.
            ``alpha``, ``zorder`` or ``interpolation``.

        Returns
        -------
        AxesImage or None
            The colour image, clipped to the fill; None if the curve has
            fewer than two values.
        """
        y = np.asarray(y, dtype=float)
        x1 = np.asarray(x1, dtype=float)

        known = ~(np.isnan(y) | np.isnan(x1))
        order = np.argsort(y[known], kind="stable")
        depths, values = y[known][order], x1[known][order]

        if depths.size < 2 or depths[0] == depths[-1]:
            return None

        # The outline of the fill, with a gap wherever a value is missing.
        # fill_betweenx also updates the data limits as a fill would.
        outline = axis.fill_betweenx(y, x1, x2, facecolor="none", edgecolor="none")
        region = Path.make_compound_path(*outline.get_paths())
        outline.remove()

        log = axis.get_xscale() == "log" and bool(np.any(values > 0))
        scaled = values[values > 0] if log else values
        norm = (mcolors.LogNorm if log else mcolors.Normalize)(
            vmin=scaled.min() if vmin is None else vmin,
            vmax=scaled.max() if vmax is None else vmax,
        )

        # One image row per sample at the finest spacing, so that descending
        # or unevenly sampled depths get their colours in the right place.
        steps = np.diff(np.unique(depths))
        rows = int(min(np.ceil((depths[-1] - depths[0]) / steps.min()), _MAX_ROWS)) + 1
        grid = np.linspace(depths[0], depths[-1], rows)
        colours = colormaps.get_cmap(colormap)(norm(np.interp(grid, depths, values)))

        # Rows are centred on the grid depths. The image is built directly,
        # as imshow would reset the axis limits (undoing an inverted depth
        # axis) and the aspect ratio.
        half = (grid[1] - grid[0]) / 2
        box = region.get_extents()
        image = AxesImage(
            axis,
            origin="lower",
            extent=(box.x0, box.x1, grid[0] - half, grid[-1] + half),
            **kwargs,
        )
        image.set_data(colours[:, np.newaxis, :])
        image.set_clip_path(region, transform=axis.transData)
        image.set_clip_box(axis.bbox)
        axis.add_image(image)

        return image

    @staticmethod
    def add_motifs(
        axis: Axes,
        fill: Collection | Patch,
        motifs: MotifPattern | Iterable[MotifPattern] | None,
    ) -> list[PathPatch]:
        """Tile motifs inside a fill and return the added patches.

        Parameters
        ----------
        axis : Axes
            The axis the fill is drawn on.
        fill : Collection or Patch
            What ``fill_between``/``fill_betweenx`` returns, or a patch such
            as a Rectangle or Polygon, in any coordinates of ``axis``.
        motifs : MotifPattern, iterable of MotifPattern or None
            The motifs, each drawn as one patch over the fill and at its
            zorder unless the motif's ``params`` set one.

        Returns
        -------
        list of PathPatch
            The added patches; a motif with no symbol inside the axes adds
            none.

        Notes
        -----
        Motifs are sized in points and tiled over the part of the fill inside
        the axes, so set the limits before calling. They do not change the
        data limits.
        """
        if motifs is None:
            return []
        if isinstance(motifs, MotifPattern):
            motifs = (motifs,)

        if isinstance(fill, Patch):
            path = fill.get_path()
        else:
            # A NaN in the curves splits a fill into several polygons; the
            # motifs are clipped to all of them.
            path = Path.make_compound_path(*fill.get_paths())
        region = (fill.get_transform() - axis.transData).transform_path(path)

        added = []
        for motif in motifs:
            patch = Pigment.motif_patch(axis, region, motif)
            if patch is None:
                continue
            if "zorder" not in motif.params:
                patch.set_zorder(fill.get_zorder())
            axis.add_artist(patch)  # add_patch would widen the data limits
            added.append(patch)

        return added

    @staticmethod
    def motif_patch(axis: Axes, region: Path, motif: MotifPattern) -> PathPatch | None:
        """Return one patch with a motif tiled over a region, clipped to it.

        Parameters
        ----------
        axis : Axes
            The axis the patch is for; it is not added to it.
        region : Path
            The area to fill, in data coordinates.
        motif : MotifPattern
            The motif to tile.

        Returns
        -------
        PathPatch or None
            The motif over the part of ``region`` inside the axes, in data
            coordinates and clipped to the region and the axes; None if no
            symbol falls there. The grid is aligned to the lower-left corner
            of the axes, so separate fills line up.
        """
        if len(region.vertices) == 0:
            return None

        # Apply pending autoscaling and a fixed aspect ratio, as drawing
        # would, so that the conversion to points is final.
        axis.get_xlim()
        axis.get_position()

        # data -> points (1/72 inch), the unit of the motif sizes
        points = Affine2D().scale(72.0 / axis.figure.dpi)
        to_points = axis.transData + points

        visible = Bbox.intersection(
            region.get_extents(to_points), axis.bbox.transformed(points)
        )
        if visible is None or visible.width <= 0 or visible.height <= 0:
            return None

        anchor = (axis.transAxes + points).transform((0.0, 0.0))
        pattern = motif.path(
            visible.x0, visible.x1, visible.y0, visible.y1, anchor=tuple(anchor)
        )
        if len(pattern.vertices) == 0:
            return None

        patch = PathPatch(pattern.transformed(to_points.inverted()), **motif.params)
        patch.set_clip_path(region, transform=axis.transData)
        patch.set_clip_box(axis.bbox)

        return patch
