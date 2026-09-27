"""Repeating symbols ("motifs") drawn inside lithology fills.

Sizes are in points (1/72 inch), like matplotlib line widths and marker
sizes, so a pattern looks the same on any track whatever its depth range or
value scale. :meth:`pphys.onepage.Pigment.fill_solid` converts them to data
coordinates when it draws them.
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Mapping
from dataclasses import KW_ONLY, dataclass, field
from types import MappingProxyType
from typing import Any

import numpy as np
from matplotlib.path import Path

ELEMENTS = ("circle", "ellipse", "line", "cross", "triangle", "quadrilateral")

# Former names still accepted.
_ELEMENT_ALIASES = {"quadrupe": "quadrilateral"}


def _pair(
    ratio_arg: tuple[str, float | None],
    size_arg: tuple[str, float | None],
    reference: float,
    *,
    default_ratio: float = 1.0,
    positive: bool = True,
) -> tuple[float, float]:
    """Return a consistent ``(ratio, size)`` with ``size = ratio * reference``.

    Each argument is ``(name, value)``, the value None when not given. A
    zero ``reference`` (the height of a line) needs an explicit size.
    """
    (ratio_name, ratio), (size_name, size) = ratio_arg, size_arg

    if ratio is not None and size is not None:
        if not math.isclose(size, ratio * reference, rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError(
                f"{ratio_name}={ratio} and {size_name}={size} disagree; give only one."
            )
    elif size is not None:
        ratio = size / reference if reference else math.nan
    else:
        ratio = default_ratio if ratio is None else ratio
        size = ratio * reference

    if positive and not size > 0:
        raise ValueError(f"{size_name} must be positive, got {size}.")
    return ratio, size


@dataclass(frozen=True)
class MotifPattern:
    """A symbol repeated on a staggered grid, e.g. the bricks of limestone.

    Each symbol sits centred in a cell of ``length_extern`` by
    ``height_extern`` points; every other row is shifted sideways by
    ``offset_ratio`` of a cell. Of each pair such as ``length_ratio`` and
    ``length_extern``, give at most one; the other is derived.

    Parameters
    ----------
    element : {"circle", "ellipse", "line", "cross", "triangle", "quadrilateral"}
        Shape of the symbol. A "line" runs from the lower-left to the
        upper-right corner of its box, a "cross" is a plus sign, and an
        "ellipse" fills its box.
    length, height : float
        Width and height of the symbol in points. For a "line" either may be
        0 (horizontal or vertical line), but not both.
    length_ratio, height_ratio : float, optional
        Cell size as a multiple of the symbol size (default 1: touching).
    length_extern, height_extern : float, optional
        Cell size in points, instead of the ratios.
    offset_ratio : float, default 0.5
        Sideways shift of every other row as a fraction of the cell width
        (0: aligned columns, 0.5: brick-wall stagger).
    shift_ratio : float, default 0
        Sideways shift of the whole grid as a fraction of the cell width,
        e.g. 0.5 to put symbols in the gaps of another motif with the same
        cell size.
    tilted_ratio : float, optional
        Sideways shift of the top edge as a fraction of ``length``, which
        turns bricks into rhombs and leans triangles (default 0).
    tilted_length : float, optional
        The same shift in points, instead of ``tilted_ratio``.
    radius : float, optional
        Circle radius in points; defaults to ``sqrt(length * height) / 2``.
    params : mapping, optional
        Keyword arguments for :class:`matplotlib.patches.PathPatch`, e.g.
        ``edgecolor``, ``facecolor``, ``fill`` or ``linewidth``.
    """

    element: str
    _: KW_ONLY
    length: float = 12.0
    height: float = 6.0
    length_ratio: float | None = None
    height_ratio: float | None = None
    length_extern: float | None = None
    height_extern: float | None = None
    offset_ratio: float = 0.5
    shift_ratio: float = 0.0
    tilted_ratio: float | None = None
    tilted_length: float | None = None
    radius: float | None = None
    params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the sizes and derive the dependent values."""
        element = _ELEMENT_ALIASES.get(self.element, self.element)
        if element not in ELEMENTS:
            raise ValueError(
                f"element must be one of {', '.join(ELEMENTS)}, not {self.element!r}."
            )

        if element == "line":
            if not (
                self.length >= 0 and self.height >= 0 and self.length + self.height > 0
            ):
                raise ValueError(
                    "a line needs a non-negative length and height, not both 0."
                )
        elif not self.length > 0:
            raise ValueError("length must be positive.")
        elif not self.height > 0:
            raise ValueError(f"height of a {element} must be positive.")

        length_ratio, length_extern = _pair(
            ("length_ratio", self.length_ratio),
            ("length_extern", self.length_extern),
            self.length,
        )
        height_ratio, height_extern = _pair(
            ("height_ratio", self.height_ratio),
            ("height_extern", self.height_extern),
            self.height,
        )
        tilted_ratio, tilted_length = _pair(
            ("tilted_ratio", self.tilted_ratio),
            ("tilted_length", self.tilted_length),
            self.length,
            default_ratio=0.0,
            positive=False,
        )

        radius = (
            math.sqrt(self.length * self.height) / 2
            if self.radius is None
            else self.radius
        )
        if element == "circle" and not radius > 0:
            raise ValueError("radius must be positive.")
        for name in ("offset_ratio", "shift_ratio"):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be a finite number.")

        values = {
            "element": element,
            "length_ratio": length_ratio,
            "height_ratio": height_ratio,
            "length_extern": length_extern,
            "height_extern": height_extern,
            "tilted_ratio": tilted_ratio,
            "tilted_length": tilted_length,
            "radius": radius,
            "params": MappingProxyType(dict(self.params)),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @property
    def pitch(self) -> tuple[float, float]:
        """Cell size ``(length_extern, height_extern)`` in points."""
        return (self.length_extern, self.height_extern)

    def path(
        self,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        anchor: tuple[float, float] = (0.0, 0.0),
    ) -> Path:
        """Return the symbols covering the box ``[x0, x1] x [y0, y1]``.

        Coordinates are in the units of the motif sizes (points). The grid
        is aligned to ``anchor``, so fills drawn separately line up. Symbols
        overlapping the box edges are included; clip the result to the fill.

        Returns
        -------
        matplotlib.path.Path
            One compound path with a sub-path per symbol.
        """
        pitch_x, pitch_y = self.pitch
        anchor_x, anchor_y = anchor

        rows = np.arange(
            math.floor((y0 - anchor_y) / pitch_y) - 1,
            math.ceil((y1 - anchor_y) / pitch_y) + 1,
        )
        columns = np.arange(
            math.floor((x0 - anchor_x) / pitch_x) - 2,
            math.ceil((x1 - anchor_x) / pitch_x) + 1,
        )
        column, row = np.meshgrid(columns, rows)

        shift = (self.shift_ratio + (row % 2) * self.offset_ratio) * pitch_x
        left = anchor_x + column * pitch_x + (pitch_x - self.length) / 2 + shift
        bottom = anchor_y + row * pitch_y + (pitch_y - self.height) / 2

        tilt = abs(self.tilted_length)
        inside = (left + self.length + tilt >= x0) & (left - tilt <= x1)
        inside &= (bottom + self.height >= y0) & (bottom <= y1)
        origins = np.column_stack([left[inside], bottom[inside]])

        shape, codes = self._shape()
        vertices = (origins[:, None, :] + shape[None, :, :]).reshape(-1, 2)
        return Path(vertices, np.tile(codes, len(origins)))

    def _shape(self) -> tuple[np.ndarray, np.ndarray]:
        """Return the vertices and codes of one symbol at the origin."""
        length, height, tilt = self.length, self.height, self.tilted_length

        if self.element == "circle":
            circle = Path.unit_circle()
            center = np.array([length / 2, height / 2])
            return circle.vertices * self.radius + center, circle.codes

        if self.element == "ellipse":
            circle = Path.unit_circle()
            center = np.array([length / 2, height / 2])
            return circle.vertices * center + center, circle.codes

        if self.element == "line":
            vertices = [(0.0, 0.0), (length, height)]
            return np.array(vertices), np.array([Path.MOVETO, Path.LINETO])

        if self.element == "cross":
            vertices = [
                (0.0, height / 2),
                (length, height / 2),
                (length / 2, 0.0),
                (length / 2, height),
            ]
            codes = [Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO]
            return np.array(vertices), np.array(codes)

        if self.element == "triangle":
            vertices = [
                (0.0, 0.0),
                (length, 0.0),
                (length / 2 + tilt, height),
                (0.0, 0.0),
            ]
        else:
            vertices = [
                (0.0, 0.0),
                (length, 0.0),
                (length + tilt, height),
                (tilt, height),
                (0.0, 0.0),
            ]

        codes = [Path.MOVETO] + [Path.LINETO] * (len(vertices) - 2) + [Path.CLOSEPOLY]
        return np.array(vertices), np.array(codes)


class Motifs:
    """Predefined motifs for lithology fills (sizes in points).

    Use them by attribute, e.g. ``Motifs.brick``, or by name with
    :meth:`get`.
    """

    brick = MotifPattern(
        "quadrilateral",
        length=12.0,
        height=6.0,
        offset_ratio=0.5,
        params={"edgecolor": "black", "fill": False, "linewidth": 0.6},
    )
    rhomb = MotifPattern(
        "quadrilateral",
        length=12.0,
        height=6.0,
        offset_ratio=0.5,
        tilted_ratio=0.25,
        params={"edgecolor": "black", "fill": False, "linewidth": 0.6},
    )
    shale = MotifPattern(
        "line",
        length=8.0,
        height=0.0,
        length_extern=16.0,
        height_extern=5.0,
        offset_ratio=0.5,
        params={"edgecolor": "black", "fill": False, "linewidth": 0.6},
    )
    chert = MotifPattern(
        "triangle",
        length=5.0,
        height=4.0,
        length_ratio=3.0,
        height_ratio=2.0,
        offset_ratio=0.5,
        params={"edgecolor": "black", "facecolor": "white", "linewidth": 0.6},
    )
    irons = MotifPattern(
        "circle",
        length=3.0,
        height=3.0,
        length_ratio=4.0,
        height_ratio=2.5,
        offset_ratio=0.5,
        params={"edgecolor": "black", "facecolor": "red", "linewidth": 0.4},
    )
    # Vertical joints in the gaps between shale dashes (calcareous rocks).
    tick = MotifPattern(
        "line",
        length=0.0,
        height=5.0,
        length_extern=16.0,
        offset_ratio=0.5,
        shift_ratio=0.5,
        params={"edgecolor": "black", "fill": False, "linewidth": 0.6},
    )
    # Slanted joints in the gaps between shale dashes (dolomitic rocks).
    slant = MotifPattern(
        "line",
        length=3.0,
        height=5.0,
        length_extern=16.0,
        height_extern=5.0,
        offset_ratio=0.5,
        shift_ratio=0.5,
        params={"edgecolor": "black", "fill": False, "linewidth": 0.6},
    )
    # Plus signs (halite).
    plus = MotifPattern(
        "cross",
        length=5.0,
        height=5.0,
        length_extern=14.0,
        height_extern=10.0,
        offset_ratio=0.5,
        params={"edgecolor": "black", "fill": False, "linewidth": 0.8},
    )
    # Oval grains (ironstone ooids).
    ooid = MotifPattern(
        "ellipse",
        length=9.0,
        height=6.0,
        length_extern=16.0,
        height_extern=10.0,
        offset_ratio=0.5,
        params={"edgecolor": "black", "facecolor": "#FF6633", "linewidth": 0.5},
    )

    @classmethod
    def get(cls, name: str) -> MotifPattern:
        """Return the motif called ``name``, e.g. "brick"."""
        motif = vars(cls).get(name)
        if not isinstance(motif, MotifPattern):
            raise KeyError(f"No motif {name!r}; available: {', '.join(cls.names())}.")
        return motif

    @classmethod
    def names(cls) -> tuple[str, ...]:
        """Return the names of the predefined motifs."""
        return tuple(name for name, _ in cls.items())

    @classmethod
    def items(cls) -> Iterator[tuple[str, MotifPattern]]:
        """Yield ``(name, motif)`` for every predefined motif."""
        for name, value in vars(cls).items():
            if isinstance(value, MotifPattern):
                yield name, value
