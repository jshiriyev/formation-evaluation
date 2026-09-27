"""Fill styles for interpretation outputs: lithologies, minerals and pore space.

A :class:`FillStyle` combines a face colour, a matplotlib hatch and motifs
(repeated symbols such as limestone bricks). Styles are grouped in tables:

- :data:`Lithology`: rock types, following the common graphic lithology key;
- :data:`Mineral`: minerals, for multimineral volume tracks;
- :data:`Porespace`: pore volumes and fluids, for porosity and saturation tracks.

A style unpacks like a dict into the fill functions, e.g.
``Pigment.fill_solid(axis, depth, x1, x2, **Lithology.limestone)``,
``WellView.add_module(2, left=0, right=1, **Mineral.quartz)`` or
``CrossView.add_formation("Top A", **Lithology.shale)``.
"""

from __future__ import annotations

import difflib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from matplotlib import pyplot as plt
from matplotlib.colors import is_color_like
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from ._motifs import MotifPattern, Motifs
from ._pigment import Pigment

# Characters matplotlib accepts in a hatch pattern (repeat one to make it denser).
_HATCH_CHARACTERS = set("/\\|-+xXoO.*")


@dataclass(frozen=True)
class FillStyle:
    """How to fill an interval: face colour, hatch and motifs.

    The style unpacks like a dict (``**style``) into ``facecolor``, ``hatch``,
    ``motifs`` and ``label``, which :meth:`Pigment.fill_solid`,
    :meth:`WellView.add_module` and :meth:`CrossView.add_formation` accept.

    Parameters
    ----------
    facecolor : color, default "white"
        Any matplotlib colour.
    hatch : str, optional
        Matplotlib hatch, e.g. "..." (dots), "xx" (cross-hatch), "--" or
        backslashes (diagonal lines). Repeating a character makes it denser.
    motifs : sequence of MotifPattern, optional
        Symbols drawn on top, in order, e.g. ``(Motifs.brick, Motifs.chert)``.
    label : str, optional
        Display name; a :class:`StyleTable` fills it in from the style's name.
    """

    facecolor: Any = "white"
    hatch: str | None = None
    motifs: tuple[MotifPattern, ...] = ()
    label: str = ""

    def __post_init__(self) -> None:
        """Validate the colour, hatch and motifs."""
        if not is_color_like(self.facecolor):
            raise ValueError(
                f"facecolor {self.facecolor!r} is not a matplotlib colour."
            )
        if self.hatch is not None and not set(self.hatch) <= _HATCH_CHARACTERS:
            allowed = "".join(sorted(_HATCH_CHARACTERS))
            raise ValueError(f"hatch {self.hatch!r} may only use {allowed!r}.")

        motifs = tuple(self.motifs)
        if not all(isinstance(motif, MotifPattern) for motif in motifs):
            raise TypeError("motifs must be MotifPattern objects.")
        object.__setattr__(self, "motifs", motifs)

    def keys(self) -> tuple[str, ...]:
        """Names used when the style is unpacked with ``**``."""
        return ("facecolor", "hatch", "motifs", "label")

    def __getitem__(self, key: str) -> Any:
        if key not in self.keys():
            raise KeyError(key)
        return getattr(self, key)


class StyleTable:
    """A named collection of fill styles.

    Look a style up as ``table["cherty dolomite"]``, ``table.get(...)`` or
    ``table.cherty_dolomite``; case, spaces, hyphens and underscores do not
    matter.

    Parameters
    ----------
    title : str
        Name of the table, used as the default title of :meth:`plot_key`.
    styles : mapping of str to FillStyle
        Styles by name. A style without a label gets its name as label.
    """

    def __init__(self, title: str, styles: Mapping[str, FillStyle]) -> None:
        self.title = title
        self._styles: dict[str, FillStyle] = {}

        for name, style in styles.items():
            key = _key(name)
            if key in self._styles:
                raise ValueError(f"Duplicate style {name!r} in {title}.")
            self._styles[key] = (
                style if style.label else replace(style, label=key.replace("_", " "))
            )

    def get(self, name: str) -> FillStyle:
        """Return the style called ``name``."""
        key = _key(name)
        try:
            return self._styles[key]
        except KeyError:
            close = difflib.get_close_matches(key, self._styles, n=3)
            hint = f" Did you mean {', '.join(close)}?" if close else ""
            raise KeyError(f"No style {name!r} in {self.title}.{hint}") from None

    def __getitem__(self, name: str) -> FillStyle:
        return self.get(name)

    def __getattr__(self, name: str) -> FillStyle:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.get(name)
        except KeyError as error:
            raise AttributeError(error.args[0]) from None

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and _key(name) in self._styles

    def __iter__(self) -> Iterator[str]:
        return iter(self._styles)

    def __len__(self) -> int:
        return len(self._styles)

    def __repr__(self) -> str:
        return f"StyleTable({self.title!r}, {len(self)} styles)"

    def names(self) -> tuple[str, ...]:
        """Return the style names in table order."""
        return tuple(self._styles)

    def items(self) -> Iterator[tuple[str, FillStyle]]:
        """Yield ``(name, style)`` pairs in table order."""
        yield from self._styles.items()

    def plot_key(
        self,
        names: Sequence[str] | Sequence[Sequence[str]] | None = None,
        *,
        ncols: int = 3,
        title: str | None = None,
        swatch: tuple[float, float] = (1.5, 0.45),
    ) -> Figure:
        """Draw a key: a labelled swatch per style, like a graphic lithology key.

        Parameters
        ----------
        names : list of str, or list of rows (lists of str), optional
            Styles to show; all by default. Give rows to control the layout;
            shorter rows are centred.
        ncols : int, default 3
            Swatches per row when ``names`` is a flat list.
        title : str, optional
            Title above the key; the table title by default. "" for none.
        swatch : (float, float), default (1.5, 0.45)
            Swatch width and height in inches.

        Returns
        -------
        matplotlib.figure.Figure
        """
        if names is None:
            names = list(self)
        if names and not isinstance(names[0], str):
            rows = [list(row) for row in names]
        else:
            rows = [list(names[i : i + ncols]) for i in range(0, len(names), ncols)]
        styles = [[self.get(name) for name in row] for row in rows]

        title = self.title if title is None else title
        width, height = swatch
        cell_width, cell_height = width + 0.7, height + 0.55
        top = 0.8 if title else 0.2
        columns = max((len(row) for row in rows), default=1)
        figure_width = columns * cell_width + 0.4
        figure_height = top + len(rows) * cell_height + 0.2

        figure = plt.figure(figsize=(figure_width, figure_height))
        axis = figure.add_axes((0.0, 0.0, 1.0, 1.0))
        axis.set_xlim(0.0, figure_width)  # data coordinates in inches
        axis.set_ylim(figure_height, 0.0)
        axis.set_axis_off()

        if title:
            axis.text(
                figure_width / 2,
                top / 2,
                title,
                ha="center",
                va="center",
                fontsize=16,
                fontweight="bold",
            )

        for number, row in enumerate(styles):
            left = 0.2 + (columns - len(row)) * cell_width / 2
            y = top + number * cell_height
            for position, style in enumerate(row):
                x = left + position * cell_width + 0.35
                box = Rectangle(
                    (x, y),
                    width,
                    height,
                    facecolor=style.facecolor,
                    hatch=style.hatch,
                    edgecolor="black",
                    linewidth=0.8,
                )
                axis.add_patch(box)
                Pigment.add_motifs(axis, box, style.motifs)
                axis.text(
                    x + width / 2,
                    y + height + 0.15,
                    style.label,
                    ha="center",
                    va="top",
                    fontsize=9,
                    fontweight="bold",
                )

        return figure


def _key(name: str) -> str:
    """Normalize a style name: lower case, words joined by underscores."""
    return "_".join(name.strip().lower().replace("-", " ").replace("_", " ").split())


# ---------------------------------------------------------------------------
# Lithologies

_LIMESTONE = "#2BFFFF"
_DOLOMITE = "#FF99FF"
_SHALE = "#C0C0C0"
_SANDSTONE = "#FFCC66"
_HALITE = "#33FF66"
_GYPSUM = "#9999FF"
_ANHYDRITE = "#CC9933"

# Pink, leaning bricks replacing every other limestone brick: the dolomite
# part of a dolomitic limestone. Aligned with Motifs.brick.
_DOLOMITE_BRICKS = MotifPattern(
    "quadrilateral",
    length=12.0,
    height=6.0,
    length_extern=24.0,
    offset_ratio=0.25,
    shift_ratio=-0.25,
    tilted_ratio=0.25,
    params={"facecolor": _DOLOMITE, "edgecolor": "black", "linewidth": 0.6},
)

Lithology = StyleTable(
    "Graphic lithology key",
    {
        "limestone": FillStyle(_LIMESTONE, motifs=(Motifs.brick,)),
        "dolomite": FillStyle(_DOLOMITE, motifs=(Motifs.rhomb,)),
        "chert": FillStyle("white", motifs=(Motifs.chert,)),
        "dolomitic limestone": FillStyle(
            _LIMESTONE, motifs=(Motifs.brick, _DOLOMITE_BRICKS)
        ),
        "cherty dolomite": FillStyle(_DOLOMITE, motifs=(Motifs.rhomb, Motifs.chert)),
        "cherty limestone": FillStyle(_LIMESTONE, motifs=(Motifs.brick, Motifs.chert)),
        "shaly limestone": FillStyle(_LIMESTONE, motifs=(Motifs.brick, Motifs.shale)),
        "shaly dolomite": FillStyle(_DOLOMITE, motifs=(Motifs.rhomb, Motifs.shale)),
        "cherty dolomitic limestone": FillStyle(
            _LIMESTONE, motifs=(Motifs.brick, _DOLOMITE_BRICKS, Motifs.chert)
        ),
        "shale": FillStyle(_SHALE, motifs=(Motifs.shale,)),
        "calcareous shale": FillStyle(_SHALE, motifs=(Motifs.shale, Motifs.tick)),
        "dolomitic shale": FillStyle(_SHALE, motifs=(Motifs.shale, Motifs.slant)),
        "sandstone": FillStyle(_SANDSTONE, hatch="..."),
        "shaly sandstone": FillStyle(_SANDSTONE, hatch="...", motifs=(Motifs.shale,)),
        "sandy shale": FillStyle("#CC9966", hatch="..", motifs=(Motifs.shale,)),
        "ironstone": FillStyle(_SHALE, motifs=(Motifs.ooid,)),
        "coal": FillStyle("black"),
        "gypsum": FillStyle(_GYPSUM, hatch="\\\\"),
        "anhydrite": FillStyle(_ANHYDRITE, hatch="xx"),
        "halite": FillStyle(_HALITE, motifs=(Motifs.plus,)),
        # Interpretation classes and synonyms
        "salt": FillStyle(_HALITE, motifs=(Motifs.plus,)),
        "matrix": FillStyle("gray", hatch="xx"),
        "shale free": FillStyle("navajowhite", hatch="||"),
    },
)

# ---------------------------------------------------------------------------
# Minerals, for multimineral volume tracks

Mineral = StyleTable(
    "Minerals",
    {
        "quartz": FillStyle("#FFFF66", hatch=".."),
        "feldspar": FillStyle("#FFB380", hatch=".."),
        "calcite": FillStyle(_LIMESTONE, motifs=(Motifs.brick,)),
        "dolomite": FillStyle(_DOLOMITE, motifs=(Motifs.rhomb,)),
        "illite": FillStyle("#8C8C3A", hatch="xx"),
        "kaolinite": FillStyle("#D2B48C", hatch="--"),
        "chlorite": FillStyle("#66A266", hatch="--"),
        "smectite": FillStyle("#4F7942", hatch="--"),
        "pyrite": FillStyle("#595959", hatch="**"),
        "anhydrite": FillStyle(_ANHYDRITE, hatch="xx"),
        "gypsum": FillStyle(_GYPSUM, hatch="\\\\"),
        "halite": FillStyle(_HALITE, motifs=(Motifs.plus,)),
        "kerogen": FillStyle("#262626"),
    },
)

# ---------------------------------------------------------------------------
# Pore space: volumes and fluids, for porosity and saturation tracks

Porespace = StyleTable(
    "Pore space",
    {
        "total": FillStyle("white", hatch="OO"),
        "liquid": FillStyle("blue", hatch="OO"),
        "water": FillStyle("steelblue", hatch="OO"),
        "water clay bound": FillStyle("lightskyblue", hatch="XX"),
        "water capillary bound": FillStyle("lightsteelblue", hatch="XX"),
        "water irreducible": FillStyle("lightblue", hatch="XX"),
        "water movable": FillStyle("aqua", hatch=".."),
        "fluid movable": FillStyle("teal", hatch=".."),
        "hydrocarbon": FillStyle("green", hatch="OO"),
        "gas": FillStyle("lightcoral", hatch="OO"),
        "gas residual": FillStyle("indianred", hatch="XX"),
        "gas movable": FillStyle("red", hatch=".."),
        "gas condensate": FillStyle("firebrick", hatch="OO."),
        "oil": FillStyle("seagreen", hatch="oo"),
        "oil residual": FillStyle("forestgreen", hatch="XX"),
        "oil movable": FillStyle("limegreen", hatch=".."),
    },
)
