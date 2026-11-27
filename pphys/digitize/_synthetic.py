"""Synthetic log pages with known values, to test and score the digitizer.

:func:`synthetic_scan` draws a page like a paper log print: tracks with
linear or log10 grids, a depth column with labels, and curves. It can add
scan defects (noise, blur, JPEG, paper tint and faded ink, rotation), writes
the page as a lossless PDF (or an image), and keeps the ground truth: the
curve values, the track edges and the depth of every page row.
:func:`score` compares a :func:`~pphys.digitize.digitize` result with it.

Pages are drawn at 144 dpi by default, so a PDF rendered at the digitizer's
default ``render_scale=2.0`` has exactly the pixels that were drawn.
"""

from __future__ import annotations

import math
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ._digitize import DigitizeResult, cv2, pdfium

TARGET = {"rms": 1.0, "max": 3.0, "coverage": 98.0, "depth": 0.5}
"""Accuracy that counts as robust: value errors in percent of the track width
(RMS and maximum), coverage of the logged interval in percent, and the
largest depth error in percent of the depth span."""

SCALES = ("linear", "log10")
Values = Sequence[float] | np.ndarray | Callable[[np.ndarray], np.ndarray] | None


@dataclass(frozen=True, eq=False)
class SyntheticCurve:
    """A curve to draw on a synthetic page.

    Parameters
    ----------
    name : str
        Mnemonic, e.g. "GR".
    values : array or callable, optional
        One value per depth sample of the page, or a function of the depth
        array. None draws a random smooth curve inside the track's scale.
    color : str
        Any matplotlib colour.
    linewidth : float
        Line width in points.
    linestyle : str
        Matplotlib line style.
    unit : str
        Unit of the curve.
    vmin, vmax : float, optional
        The curve's own scale; the track's by default.
    """

    name: str = "GR"
    values: Values = None
    color: str = "red"
    linewidth: float = 1.2
    linestyle: str = "-"
    unit: str = ""
    vmin: float | None = None
    vmax: float | None = None

    def __post_init__(self):
        if not str(self.name).strip():
            raise ValueError("A curve needs a name.")
        if not self.linewidth > 0:
            raise ValueError(f"linewidth must be positive, not {self.linewidth!r}.")
        if (self.vmin is None) != (self.vmax is None):
            raise ValueError(
                "Give both vmin and vmax for a curve's own scale, or neither."
            )


@dataclass(frozen=True, eq=False)
class SyntheticTrack:
    """A track of a synthetic page: a scale, a grid and its curves.

    Parameters
    ----------
    curves : tuple of SyntheticCurve
        Drawn in order.
    vmin, vmax : float
        Values at the left and right edge (vmin > vmax flips the track).
    scale : {"linear", "log10"}
        Linear tracks get ``divisions`` vertical grid lines; log10 tracks
        get decade and 2-9 lines.
    divisions : int
        Number of grid divisions across a linear track.
    """

    curves: tuple[SyntheticCurve, ...] = (SyntheticCurve(),)
    vmin: float = 0.0
    vmax: float = 150.0
    scale: str = "linear"
    divisions: int = 10

    def __post_init__(self):
        curves = (
            (self.curves,)
            if isinstance(self.curves, SyntheticCurve)
            else tuple(self.curves)
        )
        if not curves or not all(isinstance(c, SyntheticCurve) for c in curves):
            raise ValueError("A track needs at least one SyntheticCurve.")
        object.__setattr__(self, "curves", curves)
        if self.scale not in SCALES:
            raise ValueError(f"scale must be 'linear' or 'log10', not {self.scale!r}.")
        if self.vmin == self.vmax:
            raise ValueError("vmin and vmax must differ.")
        for curve in curves:
            lo, hi = self.range_of(curve)
            if lo == hi:
                raise ValueError(f"{curve.name}: vmin and vmax must differ.")
            if self.scale == "log10" and min(lo, hi) <= 0:
                raise ValueError(f"{curve.name}: a log10 scale needs positive limits.")
        if self.divisions < 1:
            raise ValueError(f"divisions must be at least 1, not {self.divisions!r}.")

    def range_of(self, curve: SyntheticCurve) -> tuple[float, float]:
        """The ``(vmin, vmax)`` a curve is drawn with."""
        if curve.vmin is None:
            return float(self.vmin), float(self.vmax)
        return float(curve.vmin), float(curve.vmax)

    def fraction(self, values, curve: SyntheticCurve) -> np.ndarray:
        """Position across the track (0 at the left edge, 1 at the right) of ``values``."""
        lo, hi = self.range_of(curve)
        v = np.asarray(values, dtype=float)
        if self.scale == "log10":
            v = np.log10(np.clip(v, 1e-300, None))
            lo, hi = math.log10(lo), math.log10(hi)
        return (v - lo) / (hi - lo)

    def value_at(self, fraction, curve: SyntheticCurve) -> np.ndarray:
        """Inverse of :meth:`fraction`."""
        lo, hi = self.range_of(curve)
        f = np.asarray(fraction, dtype=float)
        if self.scale == "log10":
            return 10 ** (math.log10(lo) + f * (math.log10(hi) - math.log10(lo)))
        return lo + f * (hi - lo)


def _default_tracks() -> tuple[SyntheticTrack, ...]:
    return (
        SyntheticTrack((SyntheticCurve("GR", unit="gAPI"),), 0.0, 150.0),
        SyntheticTrack(
            (SyntheticCurve("RT", unit="ohm.m"),), 0.2, 2000.0, scale="log10"
        ),
    )


@dataclass(frozen=True)
class Defects:
    """Scan defects added to a synthetic page, in this order.

    Parameters
    ----------
    fade : float
        0-1: how far the ink fades toward white (lower contrast and
        saturation).
    tint : str, optional
        Paper colour, any matplotlib colour (e.g. "#f1e4c4" for yellowed
        paper). White stays white when None.
    rotation : float
        Degrees, counter-clockwise, about the page centre.
    blur : float
        Gaussian blur sigma in pixels.
    noise : float
        Standard deviation of Gaussian noise, on the 0-255 scale.
    jpeg : int, optional
        JPEG quality (1-100) of a compress-decompress round.
    """

    fade: float = 0.0
    tint: str | None = None
    rotation: float = 0.0
    blur: float = 0.0
    noise: float = 0.0
    jpeg: int | None = None

    def __post_init__(self):
        if not 0 <= self.fade < 1:
            raise ValueError(f"fade must be in [0, 1), not {self.fade!r}.")
        if self.blur < 0 or self.noise < 0:
            raise ValueError("blur and noise cannot be negative.")
        if self.jpeg is not None and not 1 <= self.jpeg <= 100:
            raise ValueError(f"jpeg quality must be in 1-100, not {self.jpeg!r}.")
        if self.tint is not None:
            from matplotlib.colors import is_color_like

            if not is_color_like(self.tint):
                raise ValueError(f"tint must be a colour, not {self.tint!r}.")


@dataclass(eq=False)
class SyntheticScan:
    """A synthetic page and its ground truth.

    Pixel positions below are on the page as drawn (``image``), before
    rotation. Methods taking ``render_scale`` give them on the page that
    :func:`~pphys.digitize.digitize` renders from the PDF.

    Parameters
    ----------
    image : numpy.ndarray
        The page, BGR, with the defects applied.
    dpi : int
        Drawing resolution.
    depth : numpy.ndarray
        Depth samples of the truth, top to base.
    values : dict of str to numpy.ndarray
        True value of every curve at each depth sample.
    tracks : tuple of SyntheticTrack
        The tracks, left to right.
    track_columns : tuple of (float, float)
        Left and right edge of each track, in pixel-index columns.
    depth_fit : (float, float)
        ``(a, b)`` of ``depth = a * row + b`` in pixel-index rows.
    depth_unit : str
        "m" or "ft".
    defects : Defects
        The defects applied.
    path : Path or None
        Where the page was written.
    """

    image: np.ndarray
    dpi: int
    depth: np.ndarray
    values: dict[str, np.ndarray]
    tracks: tuple[SyntheticTrack, ...]
    track_columns: tuple[tuple[float, float], ...]
    depth_fit: tuple[float, float]
    depth_unit: str
    defects: Defects = field(default_factory=Defects)
    path: Path | None = None

    def zoom(self, render_scale: float = 2.0) -> float:
        """Rendered pixels per drawn pixel for a PDF rendered at ``render_scale``."""
        return render_scale * 72.0 / self.dpi

    def curve(self, name: str) -> tuple[SyntheticTrack, SyntheticCurve]:
        """The track and the curve called ``name``."""
        for track in self.tracks:
            for curve in track.curves:
                if curve.name == name:
                    return track, curve
        raise KeyError(f"No curve {name!r}; the page has {list(self.values)}.")

    def track_edges(
        self, curve: str | int, render_scale: float = 2.0
    ) -> tuple[float, float]:
        """Rendered columns of the left and right edge of a track, chosen by curve name or index."""
        if isinstance(curve, str):
            track, _ = self.curve(curve)
            index = self.tracks.index(track)
        else:
            index = curve
        k = self.zoom(render_scale)
        x0, x1 = self.track_columns[index]
        return _to_zoomed(x0, k), _to_zoomed(x1, k)

    def row_of(self, depth, render_scale: float = 2.0) -> np.ndarray:
        """Rendered row (pixel index) of ``depth``."""
        a, b = self.depth_fit
        return _to_zoomed(
            (np.asarray(depth, dtype=float) - b) / a, self.zoom(render_scale)
        )

    def depth_of(self, row, render_scale: float = 2.0) -> np.ndarray:
        """True depth of a rendered row."""
        a, b = self.depth_fit
        k = self.zoom(render_scale)
        return a * ((np.asarray(row, dtype=float) + 0.5) / k - 0.5) + b

    def depth_pairs(self, render_scale: float = 2.0) -> list[tuple[float, float]]:
        """``(row, depth)`` at the top and base of the logged interval, for ``digitize(depth=...)``."""
        top, base = float(self.depth[0]), float(self.depth[-1])
        rows = self.row_of([top, base], render_scale)
        return [(float(rows[0]), top), (float(rows[1]), base)]

    def save(self, path: str | os.PathLike, dpi_tag: bool = True) -> Path:
        """Write the page: a lossless PDF (".pdf") or an image (".png", ".jpg",
        ".tif", ".bmp") that stores its DPI unless ``dpi_tag`` is False.
        See :func:`write_pages` for several pages in one file."""
        return write_pages(path, [self], dpi_tag=dpi_tag)


def synthetic_scan(
    path: str | os.PathLike | None = None,
    *,
    tracks: Sequence[SyntheticTrack] | None = None,
    depth: tuple[float, float] = (1000.0, 1100.0),
    step: float = 0.1524,
    depth_unit: str = "m",
    depth_column: int = 1,
    label_every: float = 10.0,
    grid_every: float = 2.0,
    grid_color: str = "0.6",
    size: tuple[float, float] = (6.0, 10.0),
    dpi: int = 144,
    defects: Defects | None = None,
    seed: int = 0,
) -> SyntheticScan:
    """Draw a synthetic log page with known values.

    Parameters
    ----------
    path : str or path, optional
        Write the page here (see :meth:`SyntheticScan.save`).
    tracks : sequence of SyntheticTrack, optional
        Left to right. By default a gamma ray track (0-150, linear) and a
        resistivity track (0.2-2000, log10), both curves red.
    depth : (float, float)
        Top and base of the logged interval.
    step : float
        Depth sampling of the truth and of the drawn curves.
    depth_unit : {"m", "ft"}
        Unit of the depths and labels.
    depth_column : int
        Position of the depth column among the tracks (0: left of all).
        The default puts it between the first two, as on classic prints.
    label_every, grid_every : float
        Depth label spacing, and spacing of the horizontal grid lines (the
        lines at labels are heavier).
    grid_color : str
        Matplotlib colour of the grid lines.
    size : (float, float)
        Page width and height in inches.
    dpi : int
        Drawing resolution.
    defects : Defects, optional
        Scan defects to add.
    seed : int
        Seed of the random curves drawn for curves without values.

    Returns
    -------
    SyntheticScan
    """
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    tracks = _default_tracks() if tracks is None else tuple(tracks)
    if not tracks:
        raise ValueError("A page needs at least one track.")
    top, base = sorted(float(d) for d in depth)
    if top == base:
        raise ValueError("depth needs two different depths.")
    if depth_unit not in ("m", "ft"):
        raise ValueError(f"depth_unit must be 'm' or 'ft', not {depth_unit!r}.")
    if not step > 0 or not label_every > 0 or not grid_every > 0:
        raise ValueError("step, label_every and grid_every must be positive.")
    if not 0 <= depth_column <= len(tracks):
        raise ValueError(
            f"depth_column must be in 0-{len(tracks)}, not {depth_column!r}."
        )
    names = [c.name for t in tracks for c in t.curves]
    if len(set(names)) != len(names):
        raise ValueError(f"Curve names must be unique, not {names}.")
    defects = Defects() if defects is None else defects

    samples = np.arange(top, base + 0.5 * step, step)
    rng = np.random.default_rng(seed)
    values = {}
    for track in tracks:
        for curve in track.curves:
            values[curve.name] = _curve_values(curve, track, samples, rng)

    width_px, height_px = round(size[0] * dpi), round(size[1] * dpi)
    fig = Figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi, facecolor="white")
    canvas = FigureCanvasAgg(fig)

    # Layout in figure fractions: margins, the depth column and equal tracks.
    margin_x, margin_y, depth_width = 0.05, 0.03, 0.12
    track_width = (1 - 2 * margin_x - depth_width) / len(tracks)
    bottom, height = margin_y, 1 - 2 * margin_y
    columns, x = [], margin_x
    slots = [*range(len(tracks))]
    slots.insert(depth_column, None)
    depth_box = None
    for slot in slots:
        if slot is None:
            depth_box = (x, depth_width)
            x += depth_width
        else:
            columns.append((x, track_width))
            x += track_width

    for track, (left, width) in zip(tracks, columns):
        ax = fig.add_axes((left, bottom, width, height))
        _draw_track(
            ax, track, samples, values, top, base, label_every, grid_every, grid_color
        )
    ax = fig.add_axes((depth_box[0], bottom, depth_box[1], height))
    _draw_depth_column(ax, top, base, label_every)

    canvas.draw()
    rgb = np.asarray(canvas.buffer_rgba())[..., :3]
    image = _apply_defects(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), defects, seed)

    # Truth in pixel-index coordinates (pixel i covers [i, i + 1)).
    track_columns = tuple(
        (left * width_px - 0.5, (left + width) * width_px - 0.5)
        for left, width in columns
    )
    row_top = (1 - (bottom + height)) * height_px - 0.5
    row_base = (1 - bottom) * height_px - 0.5
    a = (base - top) / (row_base - row_top)
    depth_fit = (a, top - a * row_top)

    scan = SyntheticScan(
        image=image,
        dpi=dpi,
        depth=samples,
        values=values,
        tracks=tracks,
        track_columns=track_columns,
        depth_fit=depth_fit,
        depth_unit=depth_unit,
        defects=defects,
    )
    if path is not None:
        scan.save(path)
    return scan


@dataclass
class Score:
    """How close a digitized curve is to its truth.

    Parameters
    ----------
    curve : str
        The curve scored.
    rms, max : float
        Value error in percent of the track width.
    coverage : float
        Percent of the page rows of the logged interval where the curve was
        found, counted before resampling (which interpolates across gaps).
    depth : float
        Largest error of the depth calibration over the logged interval,
        in percent of its depth span.
    samples : int
        Digitized samples compared.
    target : dict
        Thresholds of :attr:`passed`.
    """

    curve: str
    rms: float
    max: float
    coverage: float
    depth: float
    samples: int
    target: dict = field(default_factory=lambda: dict(TARGET))

    @property
    def passed(self) -> bool:
        """Whether every number meets the target (to within rounding)."""
        t, eps = self.target, 1e-9
        return bool(
            self.rms <= t["rms"] + eps
            and self.max <= t["max"] + eps
            and self.coverage >= t["coverage"] - eps
            and self.depth <= t["depth"] + eps
        )

    def __str__(self) -> str:
        return (
            f"{self.curve}: rms {self.rms:.2f}%, max {self.max:.2f}%, coverage "
            f"{self.coverage:.1f}%, depth {self.depth:.3f}% -> "
            + ("pass" if self.passed else "FAIL")
        )


def score(
    result: DigitizeResult,
    scan: SyntheticScan | Sequence[SyntheticScan],
    curve: str | None = None,
    target: dict | None = None,
) -> Score:
    """Compare a digitized curve with the truth of its synthetic page(s).

    Parameters
    ----------
    result : DigitizeResult
        What :func:`~pphys.digitize.digitize` returned for the page(s).
    scan : SyntheticScan or sequence of SyntheticScan
        The page, or the pages in the order digitized (``result.qc.pages``).
        Values are compared over every page's interval, coverage counts the
        rows of all pages, and the depth error is the worst page's.
    curve : str, optional
        Name of the curve, both on the page and in the result; the first
        digitized curve by default.
    target : dict, optional
        Thresholds; :data:`TARGET` by default.

    Returns
    -------
    Score
        Errors are measured across the track, so a log10 track is scored in
        log space; a value on the wrong side of a log scale counts as far off.
    """
    scans = [scan] if isinstance(scan, SyntheticScan) else list(scan)
    las = result.las
    name = las.curves[1].mnemonic if curve is None else curve
    track, spec = scans[0].curve(name)
    intervals = [(float(s.depth[0]), float(s.depth[-1])) for s in scans]

    depths = np.asarray(las.index, dtype=float)
    digitized = np.asarray(las[name], dtype=float)
    true_here = np.full(depths.shape, np.nan)
    for s, (top, base) in zip(scans, intervals):
        here = np.isnan(true_here) & (depths >= top) & (depths <= base)
        true_here[here] = np.interp(depths[here], s.depth, s.values[name])
    inside = np.isfinite(true_here) & np.isfinite(digitized)
    if inside.sum() == 0:
        nan = float("nan")
        return Score(name, nan, nan, 0.0, nan, 0, dict(target or TARGET))
    error = 100 * np.abs(
        track.fraction(digitized[inside], spec)
        - track.fraction(true_here[inside], spec)
    )

    render_scale = result.settings.render_scale
    reading = result.raw[name] if name in getattr(result, "raw", {}) else result
    raw_depth = np.asarray(reading.depth, dtype=float)
    raw_found = np.isfinite(np.asarray(reading.value, dtype=float))
    pages = getattr(result.qc, "pages", None) or [result.qc]
    rows_total, found, depth_error = 0, 0, 0.0
    for k, (s, (top, base)) in enumerate(zip(scans, intervals)):
        row_top, row_base = s.row_of([top, base], render_scale)
        rows_total += max(1, math.floor(row_base) - math.ceil(row_top) + 1)
        found += np.count_nonzero(raw_found & (raw_depth >= top) & (raw_depth <= base))
        rows = np.linspace(row_top, row_base, 200)
        a, b = pages[min(k, len(pages) - 1)].depth_fit
        worst = np.abs(a * rows + b - s.depth_of(rows, render_scale)).max()
        depth_error = max(depth_error, float(100 * worst / (base - top)))

    return Score(
        curve=name,
        rms=float(np.sqrt(np.mean(error**2))),
        max=float(error.max()),
        coverage=min(100.0, 100.0 * found / rows_total),
        depth=depth_error,
        samples=int(inside.sum()),
        target=dict(target or TARGET),
    )


def _to_zoomed(index, k: float):
    """A pixel index on the drawn page -> the pixel index after scaling by ``k``."""
    return (index + 0.5) * k - 0.5


def _curve_values(curve, track, samples, rng) -> np.ndarray:
    if curve.values is None:
        values = track.value_at(_smooth_fraction(len(samples), rng), curve)
    elif callable(curve.values):
        values = np.asarray(curve.values(samples), dtype=float)
    else:
        values = np.asarray(curve.values, dtype=float)
    if values.shape != samples.shape:
        raise ValueError(
            f"{curve.name}: {values.size} values for {samples.size} depth samples "
            "(one per step from top to base)."
        )
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{curve.name}: values must be finite.")
    f = track.fraction(values, curve)
    if f.min() < -1e-9 or f.max() > 1 + 1e-9:
        lo, hi = track.range_of(curve)
        raise ValueError(
            f"{curve.name}: values must lie within the track's scale {lo}-{hi}."
        )
    values.setflags(write=False)
    return values


def _smooth_fraction(n: int, rng) -> np.ndarray:
    """A random smooth curve across 10-90 % of the track: a few sine waves plus fine texture."""
    x = np.linspace(0.0, 1.0, n)
    y = np.zeros(n)
    for k in range(1, 7):
        cycles = k * rng.uniform(1.0, 2.5)
        y += rng.normal(0.0, 1.0 / k) * np.sin(
            2 * np.pi * cycles * x + rng.uniform(0, 2 * np.pi)
        )
    y += 0.15 * np.convolve(rng.normal(0.0, 1.0, n), np.ones(9) / 9, mode="same")
    y = (y - y.min()) / (y.max() - y.min())
    return 0.1 + 0.8 * y


def _draw_track(
    ax, track, samples, values, top, base, label_every, grid_every, grid_color
):
    if track.scale == "log10":
        ax.set_xscale("log")
    ax.set_xlim(track.vmin, track.vmax)
    ax.set_ylim(base, top)
    lo, hi = sorted((track.vmin, track.vmax))
    if track.scale == "log10":
        lines = [
            m * 10.0**e
            for e in range(math.floor(math.log10(lo)), math.ceil(math.log10(hi)) + 1)
            for m in range(1, 10)
        ]
        heavy = {10.0**e for e in range(-20, 21)}
        for v in lines:
            if lo < v < hi:
                ax.axvline(v, color=grid_color, lw=0.8 if v in heavy else 0.4, zorder=1)
    else:
        for v in np.linspace(lo, hi, track.divisions + 1)[1:-1]:
            ax.axvline(v, color=grid_color, lw=0.4, zorder=1)
    for d in np.arange(
        math.ceil(top / grid_every) * grid_every, base + 1e-9, grid_every
    ):
        major = abs(d / label_every - round(d / label_every)) < 1e-9
        ax.axhline(d, color=grid_color, lw=0.8 if major else 0.4, zorder=1)
    for curve in track.curves:
        ax.plot(
            values[curve.name]
            if curve.vmin is None
            else _rescale(values[curve.name], track, curve),
            samples,
            color=curve.color,
            lw=curve.linewidth,
            ls=curve.linestyle,
            zorder=3,
        )
    ax.set_xticks([])
    ax.set_yticks([])
    ax.minorticks_off()
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        spine.set_color("black")


def _rescale(values, track, curve):
    """Values on a curve's own scale -> the track's axis, so they plot at the right place."""
    own = SyntheticCurve(curve.name)
    return track.value_at(track.fraction(values, curve), own)


def _draw_depth_column(ax, top, base, label_every):
    ax.set_xlim(0, 1)
    ax.set_ylim(base, top)
    ax.axis("off")
    for d in np.arange(
        math.ceil(top / label_every) * label_every, base + 1e-9, label_every
    ):
        ax.text(0.5, d, f"{d:g}", ha="center", va="center", fontsize=8, color="black")


def _apply_defects(bgr: np.ndarray, defects: Defects, seed: int) -> np.ndarray:
    img = bgr.astype(np.float32)
    if defects.fade:
        img = img + defects.fade * (255.0 - img)
    paper = (255.0, 255.0, 255.0)
    if defects.tint is not None:
        from matplotlib.colors import to_rgb

        r, g, b = to_rgb(defects.tint)
        paper = (255.0 * b, 255.0 * g, 255.0 * r)
        img = img * (np.array(paper, dtype=np.float32) / 255.0)
    if defects.rotation:
        h, w = img.shape[:2]
        m = cv2.getRotationMatrix2D(
            ((w - 1) / 2.0, (h - 1) / 2.0), defects.rotation, 1.0
        )
        img = cv2.warpAffine(
            img,
            m,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=paper,
        )
    if defects.blur:
        img = cv2.GaussianBlur(img, (0, 0), defects.blur)
    if defects.noise:
        img = img + np.random.default_rng(seed + 1).normal(
            0.0, defects.noise, img.shape
        )
    out = np.clip(np.rint(img), 0, 255).astype(np.uint8)
    if defects.jpeg is not None:
        ok, buffer = cv2.imencode(
            ".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, int(defects.jpeg)]
        )
        out = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    return out


def write_pages(
    path: str | os.PathLike, scans: Sequence[SyntheticScan], dpi_tag: bool = True
) -> Path:
    """Write synthetic pages into one file.

    A PDF (lossless) or TIFF (deflate) holds any number of pages; PNG, JPG
    (quality 92) and BMP hold one. Images store the pages' DPI unless
    ``dpi_tag`` is False. All pages must share one DPI.
    """
    from PIL import Image

    path = Path(path)
    suffix = path.suffix.lower()
    scans = list(scans)
    if not scans:
        raise ValueError("No pages to write.")
    dpis = {s.dpi for s in scans}
    if len(dpis) != 1:
        raise ValueError(f"All pages must share one DPI, not {sorted(dpis)}.")
    dpi = dpis.pop()
    pictures = [Image.fromarray(s.image[..., ::-1]) for s in scans]
    meta = {"dpi": (dpi, dpi)} if dpi_tag else {}
    if suffix == ".pdf":
        _write_pdf(path, [s.image for s in scans], dpi)
    elif suffix in (".tif", ".tiff"):
        pictures[0].save(
            path,
            save_all=True,
            append_images=pictures[1:],
            compression="tiff_deflate",
            **meta,
        )
    elif suffix in (".png", ".jpg", ".jpeg", ".bmp"):
        if len(pictures) > 1:
            raise ValueError(
                f"A {suffix} file holds one page; use .pdf or .tif for several."
            )
        extra = {"quality": 92} if suffix in (".jpg", ".jpeg") else {}
        pictures[0].save(path, **meta, **extra)
    else:
        raise ValueError(
            f"Unknown page format {suffix!r}; use .pdf, .png, .jpg, .tif or .bmp."
        )
    for s in scans:
        s.path = path
    return path


def _write_pdf(path: Path, images: Sequence[np.ndarray], dpi: int) -> None:
    """One page per image, each held losslessly and sized so that 1 pixel is 72/dpi points."""
    from PIL import Image

    pdf = pdfium.PdfDocument.new()
    try:
        for bgr in images:
            height, width = bgr.shape[:2]
            w_pt, h_pt = width * 72.0 / dpi, height * 72.0 / dpi
            page = pdf.new_page(w_pt, h_pt)
            image = pdfium.PdfImage.new(pdf)
            image.set_bitmap(pdfium.PdfBitmap.from_pil(Image.fromarray(bgr[..., ::-1])))
            image.set_matrix(pdfium.PdfMatrix().scale(w_pt, h_pt))
            page.insert_obj(image)
            page.gen_content()
        pdf.save(str(path))
    finally:
        pdf.close()
