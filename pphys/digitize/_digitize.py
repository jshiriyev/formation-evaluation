"""Digitize the curves of a scanned log page (PDF) into a :class:`pphys.WellLog`.

The pipeline:

1. Render a PDF page (pypdfium2).
2. Mask each curve's colour: by hue for coloured curves, by darkness for
   black and grey ones (:func:`curve_mask`).
3. Find the tracks from their frame lines (:func:`find_tracks`) and pick
   each curve's track.
4. Calibrate depth once: from the depths given, or from the depth labels,
   found and read with Tesseract and fitted with a robust straight line
   (:func:`find_depth_labels`, :func:`fit_depth`).
5. For each curve: clean its mask in the track (grid lines, frames, specks;
   :func:`clean_track_mask`), follow it row by row (:func:`trace_curve`),
   bridge short gaps (:func:`bridge_gaps`) and map columns to values across
   the track edges on a linear or log10 scale (:func:`map_x_to_value`).
6. Resample all curves onto one depth grid, keeping long gaps empty
   (:func:`resample`), and build the WellLog.

Known limits: curves of one colour in one track are not told apart (a QC
warning flags them); rotated pages are not deskewed; PDF input only.
"""

from __future__ import annotations

import functools
import json
import math
import os
import re
import shutil
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import NamedTuple

import numpy as np
from matplotlib.colors import is_color_like, to_rgb

try:
    import cv2
    import pypdfium2 as pdfium
except ModuleNotFoundError as exc:  # depends on the install
    raise ModuleNotFoundError(
        "pphys.digitize needs the 'digitize' extra: "
        'pip install "pphys[digitize] @ git+https://github.com/jshiriyev/formation-evaluation"'
    ) from exc

from .._lasio import WellLog

DEPTH_UNITS = {"m": "M", "ft": "FT"}
DEFAULT_STEP = {"m": 0.1524, "ft": 0.5}
SCALES = ("linear", "log10")
GRAY_SATURATION = 64  # colours less saturated than this are black or grey


class DigitizeError(RuntimeError):
    """The scan could not be digitized with the inputs given.

    ``images`` holds the QC images made before the failure (name -> BGR or
    mask array), to see what went wrong.
    """

    def __init__(self, message: str, images: dict[str, np.ndarray] | None = None):
        super().__init__(message)
        self.images = images or {}


class DepthCalibrationError(DigitizeError):
    """Depth could not be calibrated, e.g. too few depth labels were read."""


@dataclass(frozen=True)
class Settings:
    """Tuning of the pipeline. Sizes are pixels of the rendered page.

    Parameters
    ----------
    render_scale : float
        PDF render scale; 1.0 renders at 72 dpi.
    hue_tolerance : int
        How far (OpenCV hue, 0-90) a pixel's hue may be from a coloured
        curve's.
    min_saturation, min_value : int
        Lower HSV saturation and value (0-255) of a coloured curve's pixel.
    gray_saturation : int
        Upper HSV saturation (0-255) of a black or grey curve's pixel.
    gray_tolerance : int
        How much brighter (HSV value, 0-255) than its colour a black or grey
        curve's pixel may be.
    min_blob : int
        Connected pieces of a colour mask smaller than this many pixels are
        specks, not curve.
    max_gap : int
        Gaps in a curve of up to this many rows (where another curve is drawn
        over it, between dashes) are bridged by interpolation; longer gaps
        stay empty.
    min_track_width : int
        Tracks narrower than this are ignored.
    ink_contrast : int
        How much darker than the paper (median grey, 0-255) a pixel must be
        to count as a printed line.
    min_line_fraction : float
        Fraction of the page height a column of line pixels must cover to be
        a vertical line (a track frame or grid line).
    frame_tolerance : float
        Lines at least this fraction as dark (against the paper) as the
        darkest line are track frames; lighter ones are grid lines.
    min_label_height, max_label_height : int
        Height range of a depth label's text, in pixels.
    ocr_min_confidence : float
        Tesseract confidence (0-100) below which a label is ignored.
    label_tolerance : float
        Largest distance, in rows, between a label and the fitted depth line
        for the label to count; farther ones are treated as misreads.
    min_labels : int
        Labels that must agree on the fitted line for OCR depth to be used.
    null_value : float
        LAS null value.
    tesseract : str, optional
        Tesseract executable. When None, :func:`find_tesseract` looks for it.
    """

    render_scale: float = 2.0
    hue_tolerance: int = 12
    min_saturation: int = 70
    min_value: int = 50
    gray_saturation: int = 60
    gray_tolerance: int = 90
    min_blob: int = 6
    max_gap: int = 8
    min_track_width: int = 30
    ink_contrast: int = 40
    min_line_fraction: float = 0.5
    frame_tolerance: float = 0.5
    min_label_height: int = 6
    max_label_height: int = 60
    ocr_min_confidence: float = 30.0
    label_tolerance: float = 3.0
    min_labels: int = 3
    null_value: float = -999.25
    tesseract: str | None = None

    def __post_init__(self):
        positive = (
            "render_scale",
            "min_track_width",
            "min_label_height",
            "label_tolerance",
        )
        for name in positive:
            if not getattr(self, name) > 0:
                raise ValueError(
                    f"{name} must be positive, not {getattr(self, name)!r}."
                )
        for name in ("min_blob", "max_gap"):
            if getattr(self, name) < 0:
                raise ValueError(
                    f"{name} cannot be negative, not {getattr(self, name)!r}."
                )
        if not 0 <= self.hue_tolerance <= 90:
            raise ValueError(
                f"hue_tolerance must be in 0-90, not {self.hue_tolerance!r}."
            )
        if not 0 < self.ink_contrast < 255:
            raise ValueError(
                f"ink_contrast must be in 1-254, not {self.ink_contrast!r}."
            )
        if not 0 < self.min_line_fraction <= 1:
            raise ValueError(
                f"min_line_fraction must be in (0, 1], not {self.min_line_fraction!r}."
            )
        if not 0 < self.frame_tolerance < 1:
            raise ValueError(
                f"frame_tolerance must be in (0, 1), not {self.frame_tolerance!r}."
            )
        if self.max_label_height < self.min_label_height:
            raise ValueError("max_label_height must be at least min_label_height.")
        if self.min_labels < 2:
            raise ValueError(f"min_labels must be at least 2, not {self.min_labels!r}.")
        for name in (
            "min_saturation",
            "min_value",
            "gray_saturation",
            "gray_tolerance",
        ):
            if not 0 <= getattr(self, name) <= 255:
                raise ValueError(
                    f"{name} must be in 0-255, not {getattr(self, name)!r}."
                )


@dataclass(frozen=True)
class Curve:
    """A curve to digitize.

    Parameters
    ----------
    name : str
        Mnemonic, e.g. "GR".
    vmin, vmax : float
        Values at the left and right edge of its track (vmin > vmax for a
        flipped track).
    unit : str
        Unit, e.g. "gAPI".
    scale : {"linear", "log10"}
        The track's scale, as printed in the log header.
    color : str
        Any matplotlib colour ("red", "#1f77b4", "black"). Coloured curves
        are matched by hue, so faded ink still counts; black and greys by
        darkness.
    track : "auto", "left", "right" or int
        The detected track that holds it: the one with the most pixels of its
        colour ("auto"), the first or last one, or its index from the left.
    track_edges : (float, float), optional
        Columns of the rendered page at its track's left and right edges;
        overrides ``track`` and the detection.
    """

    name: str
    vmin: float
    vmax: float
    unit: str = ""
    scale: str = "linear"
    color: str = "red"
    track: str | int = "auto"
    track_edges: tuple[float, float] | None = None

    def __post_init__(self):
        name = str(self.name).strip()
        if not name:
            raise ValueError("A curve needs a mnemonic, e.g. curve='GR'.")
        object.__setattr__(self, "name", name)
        if self.vmin == self.vmax:
            raise ValueError(f"{name}: vmin and vmax must differ.")
        if self.scale not in SCALES:
            raise ValueError(
                f"{name}: scale must be 'linear' or 'log10', not {self.scale!r}."
            )
        if self.scale == "log10" and min(self.vmin, self.vmax) <= 0:
            raise ValueError(f"{name}: a log10 scale needs positive vmin and vmax.")
        if not is_color_like(self.color):
            raise ValueError(
                f"{name}: color must be a colour name or hex, not {self.color!r}."
            )
        _, saturation, value = _hsv_of(self.color)
        if saturation < GRAY_SATURATION and value > 200:
            raise ValueError(
                f"{name}: a {self.color!r} curve cannot be told from the paper."
            )
        named = isinstance(self.track, str) and self.track in ("auto", "left", "right")
        index = isinstance(self.track, (int, np.integer)) and not isinstance(
            self.track, bool
        )
        if not (named or index):
            raise ValueError(
                f"{name}: track must be 'auto', 'left', 'right' or an index, not {self.track!r}."
            )
        if self.track_edges is not None:
            x0, x1 = sorted(float(v) for v in self.track_edges)
            if x1 - x0 < 2:
                raise ValueError(
                    f"{name}: track_edges must be two columns at least 2 apart."
                )
            object.__setattr__(self, "track_edges", (x0, x1))

    @property
    def dark(self) -> bool:
        """Whether the colour is black or grey, matched by darkness rather than hue."""
        return _hsv_of(self.color)[1] < GRAY_SATURATION


@dataclass
class Line:
    """A long vertical line on the page: a track frame or a grid line.

    ``x`` is its centre column; ``strength`` how much darker than the paper
    it is (0-255).
    """

    x: float
    width: int
    strength: float


@dataclass
class Track:
    """A track found on the page: the columns of its two frame lines and of
    the grid lines between them."""

    x0: float
    x1: float
    grid: list[float] = field(default_factory=list)


@dataclass
class Label:
    """A depth label read on the page.

    ``row`` is the centre row of its text, ``box`` its ``(x0, y0, x1, y1)``
    on the page, ``depth`` the number read (None when it is not a number),
    ``text`` what OCR returned and ``confidence`` its confidence (0-100).
    """

    row: float
    depth: float | None
    text: str
    confidence: float
    box: tuple[int, int, int, int]


@dataclass
class CurveQC:
    """What :func:`digitize` found for one curve.

    Parameters
    ----------
    name, color, scale : str
        As given.
    track : (float, float)
        Columns of the left and right edge of its track, where its values
        are ``vmin`` and ``vmax``.
    track_source : str
        "detected" (from the frame lines) or "manual" (``track_edges``).
    grid : str or None
        What the track's vertical grid looks like: "linear" (evenly spaced),
        "log10" (bunching toward each decade), or None if unclear.
    rows_found : int
        Page rows where the curve was found.
    rows_bridged : int
        Rows filled in by interpolation across short gaps (up to
        ``Settings.max_gap``).
    rows_ambiguous : int
        Rows holding two or more separate runs of the curve's colour.
    coverage : float
        Percent of the resampled depths, between its first and last reading,
        that have a value.
    """

    name: str
    color: str
    scale: str
    track: tuple[float, float]
    track_source: str
    grid: str | None = None
    rows_found: int = 0
    rows_bridged: int = 0
    rows_ambiguous: int = 0
    coverage: float = 0.0


@dataclass
class QC:
    """What :func:`digitize` found, for checking the result.

    Pixel positions are on the rendered page.

    Parameters
    ----------
    scan : str
        The scan file.
    page : int
        The page digitized (0-based).
    page_size : (int, int)
        Width and height of the rendered page.
    tracks : list of (float, float)
        Frame columns of every track found, left to right.
    depth_source : str
        "manual" (depths given) or "ocr" (depth labels read).
    depth_fit : (float, float)
        ``(a, b)`` of ``depth = a * row + b``.
    curves : list of CurveQC
        One per curve, in order. ``track``, ``track_source``, ``scale``,
        ``grid`` and ``coverage`` are shortcuts to the first.
    depth_labels : list of (float, float)
        ``(row, depth)`` of the labels read by OCR (empty for manual depths).
    depth_inliers : list of bool
        Whether each label agrees with the fitted line (False: a misread,
        ignored).
    depth_residuals : list of float
        Rows between each label and the fitted line.
    depth_rms : float or None
        RMS of the agreeing labels' residuals, in rows.
    label_columns : (float, float) or None
        Column range the labels were read from.
    warnings : list of str
        Things to check before trusting the result.
    """

    scan: str
    page: int
    page_size: tuple[int, int]
    tracks: list[tuple[float, float]]
    depth_source: str
    depth_fit: tuple[float, float]
    curves: list[CurveQC] = field(default_factory=list)
    depth_labels: list[tuple[float, float]] = field(default_factory=list)
    depth_inliers: list[bool] = field(default_factory=list)
    depth_residuals: list[float] = field(default_factory=list)
    depth_rms: float | None = None
    label_columns: tuple[float, float] | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def track(self) -> tuple[float, float]:
        return self.curves[0].track

    @property
    def track_source(self) -> str:
        return self.curves[0].track_source

    @property
    def scale(self) -> str:
        return self.curves[0].scale

    @property
    def grid(self) -> str | None:
        return self.curves[0].grid

    @property
    def coverage(self) -> float:
        return self.curves[0].coverage

    def summary(self) -> str:
        """A few lines for the console."""
        a, b = self.depth_fit
        lines = [
            f"scan: {self.scan} (page {self.page}, {self.page_size[0]} x {self.page_size[1]} px), "
            f"{len(self.tracks)} track(s) found",
            f"depth: {self.depth_source}, depth = {a:.6g} * row + {b:.6g}",
        ]
        if self.depth_source == "ocr":
            used = sum(self.depth_inliers)
            lines.append(
                f"depth labels: {used} of {len(self.depth_labels)} on the line, "
                f"RMS {self.depth_rms:.2f} rows"
            )
        for c in self.curves:
            lines.append(
                f"{c.name} ({c.color}): track columns {c.track[0]:.1f}-{c.track[1]:.1f} "
                f"({c.track_source}), {c.scale} scale"
                + (f", grid looks {c.grid}" if c.grid else "")
                + f"; found in {c.rows_found} rows, {c.rows_bridged} bridged; "
                f"coverage {c.coverage:.1f}%"
            )
        lines += [f"warning: {w}" for w in self.warnings]
        return "\n".join(lines)


class Reading(NamedTuple):
    """A curve as read: one sample per page row that holds it, before
    resampling; ``bridged`` marks rows interpolated across a short gap."""

    depth: np.ndarray
    value: np.ndarray
    bridged: np.ndarray


@dataclass
class DigitizeResult:
    """The outcome of :func:`digitize`.

    Parameters
    ----------
    las : WellLog
        The depth index and the digitized curves, resampled to a regular step.
    qc : QC
        Tracks, depth calibration, per-curve findings and warnings.
    settings : Settings
        The settings used.
    images : dict of str to numpy.ndarray
        QC images by name: "page", and per curve ``mask_<name>``,
        ``track_<name>``, ``track_mask_<name>`` and ``curve_overlay_<name>``;
        for OCR also "depth_labels".
    raw : dict of str to Reading
        Each curve as read, before resampling. ``depth`` and ``value`` are
        shortcuts to the first curve's.
    """

    las: WellLog
    qc: QC
    settings: Settings
    images: dict[str, np.ndarray]
    raw: dict[str, Reading]

    @property
    def depth(self) -> np.ndarray:
        return next(iter(self.raw.values())).depth

    @property
    def value(self) -> np.ndarray:
        return next(iter(self.raw.values())).value

    def save(self, outdir: str | os.PathLike, name: str | None = None) -> Path:
        """Write the LAS file, the raw readings, the QC images and ``qc.json``.

        Files: ``<name>.las``; ``<name>.csv`` with the readings before
        resampling (columns curve, depth, value, bridged); ``<image>.png``
        for every QC image; and ``qc.json`` (QC and settings). ``name``
        defaults to the scan's file name. Returns the LAS path.
        """
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        name = name or Path(self.qc.scan).stem

        las_path = out / f"{name}.las"
        self.las.write(str(las_path), version=2.0)
        lines = ["curve,depth,value,bridged"]
        for curve, reading in self.raw.items():
            lines += [
                f"{curve},{d:.6f},{v:.6f},{int(bridged)}"
                for d, v, bridged in zip(reading.depth, reading.value, reading.bridged)
            ]
        (out / f"{name}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        for key, image in self.images.items():
            _write_image(out / f"{key}.png", image)
        report = {"qc": asdict(self.qc), "settings": asdict(self.settings)}
        (out / "qc.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return las_path


def digitize(
    scan: str | os.PathLike,
    *,
    curves: Sequence[Curve] | None = None,
    curve: str | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
    unit: str = "",
    scale: str = "linear",
    color: str = "red",
    track: str | int = "auto",
    track_edges: tuple[float, float] | None = None,
    depth: Sequence[float] | Sequence[tuple[float, float]] | None = None,
    depth_unit: str = "m",
    step: float | None = None,
    page: int = 0,
    label_columns: tuple[float, float] | None = None,
    well: str | None = None,
    settings: Settings | None = None,
) -> DigitizeResult:
    """Digitize curves of a scanned log page into a WellLog.

    Give the curves as ``curves=[Curve(...), ...]``, or one curve with the
    shorthand ``curve``, ``vmin``, ``vmax``, ``unit``, ``scale``, ``color``,
    ``track`` and ``track_edges`` (the fields of :class:`Curve`). The tracks
    and the depth calibration are found once for all curves.

    Parameters
    ----------
    scan : str or path
        A PDF file.
    curves : sequence of Curve, optional
        The curves, each with its scale, colour and track.
    curve, vmin, vmax, unit, scale, color, track, track_edges
        One curve, when ``curves`` is not given; see :class:`Curve`.
    depth : (top, base) or sequence of (row, depth), optional
        Manual depth calibration, which skips OCR. ``(top, base)`` are the
        depths at the first and last row of the rendered page; two or more
        ``(row, depth)`` pairs (rows of the rendered page, see the "page" QC
        image) are fitted with a straight line. Without it, the depth labels
        are found and read with Tesseract (see :func:`find_depth_labels`):
        at least ``Settings.min_labels`` must agree on one straight line, and
        the others are ignored as misreads.
    depth_unit : {"m", "ft"}
        Unit of the depths.
    step : float, optional
        Depth step of the output; 0.1524 (m) or 0.5 (ft) by default.
    page : int
        Page of the PDF to digitize, 0-based.
    label_columns : (float, float), optional
        Columns of the rendered page between which the depth labels are;
        by default every band outside the tracks is searched.
    well : str, optional
        Well name for the LAS header; the scan's file name by default.
    settings : Settings, optional
        Pipeline tuning.

    Returns
    -------
    DigitizeResult
        ``.las`` (the WellLog, one column per curve), ``.qc``, ``.raw`` and
        the QC images; ``.save(dir)`` writes them.

    Raises
    ------
    DepthCalibrationError
        If depth cannot be calibrated: no labels found, or fewer than
        ``Settings.min_labels`` of them on one line.
    DigitizeError
        If a curve's colour is not found, no track frames are found (pass
        ``track_edges``), a track does not exist, or Tesseract is needed but
        missing.
    """
    settings = Settings() if settings is None else settings
    path = Path(scan)
    if not path.is_file():
        raise FileNotFoundError(f"No such scan: {path}")
    if path.suffix.lower() != ".pdf":
        raise DigitizeError(
            f"{path.name}: only PDF scans are read for now; convert an image to PDF first."
        )
    curves = _curve_list(
        curves, curve, vmin, vmax, unit, scale, color, track, track_edges
    )
    if depth_unit not in DEPTH_UNITS:
        raise ValueError(f"depth_unit must be 'm' or 'ft', not {depth_unit!r}.")
    step = DEFAULT_STEP[depth_unit] if step is None else float(step)
    if step <= 0:
        raise ValueError(f"step must be positive, not {step!r}.")
    manual = None if depth is None else _parse_depth(depth)

    page_bgr = render_pdf_page(path, page, settings.render_scale)
    height, width = page_bgr.shape[:2]
    images: dict[str, np.ndarray] = {"page": page_bgr}
    masks = {}
    for c in curves:
        masks[c.name] = curve_mask(page_bgr, c.color, settings)
        images[f"mask_{c.name}"] = masks[c.name]
        if not masks[c.name].any():
            raise DigitizeError(
                f"No {c.color} pixels were found on the page for {c.name}; check its "
                "color= and the Settings colour tolerances.",
                images,
            )
    warnings: list[str] = []
    every = functools.reduce(np.bitwise_or, masks.values())
    coloured = [masks[c.name] for c in curves if not c.dark]
    # Black curves share the frames' colour, so only coloured curves are kept out of the lines.
    exclude = (
        functools.reduce(np.bitwise_or, coloured) if coloured else np.zeros_like(every)
    )
    tracks = find_tracks(page_bgr, settings, curve=every, exclude=exclude)

    picks = {}
    for c in curves:
        x0, x1, source, chosen, note = _curve_track(
            c, tracks, masks[c.name], width, images
        )
        if note:
            warnings.append(f"{c.name}: {note}")
        grid = grid_kind(chosen) if chosen is not None else None
        if grid is not None and grid != c.scale:
            warnings.append(
                f"{c.name}: the track's grid looks {grid} ("
                + (
                    "evenly spaced"
                    if grid == "linear"
                    else "bunching toward each decade"
                )
                + f") but scale='{c.scale}'; check the scale printed in the log header."
            )
        picks[c.name] = (x0, x1, source, grid)

    labels: list[Label] = []
    inliers: list[bool] = []
    residuals: list[float] = []
    depth_rms = None
    columns = None
    if manual is not None:
        a, b = _manual_fit(manual, height)
        source = "manual"
    else:
        known = tracks or [Track(p[0], p[1]) for p in picks.values()]
        columns, labels = find_depth_labels(page_bgr, known, settings, label_columns)
        numbers = [lb for lb in labels if lb.depth is not None]
        fit = fit_depth(
            [(lb.row, lb.depth) for lb in numbers], settings.label_tolerance
        )
        if columns is not None:
            band = page_bgr[
                :, max(0, math.floor(columns[0])) : math.ceil(columns[1]) + 1
            ]
            images["depth_labels"] = depth_labels_overlay(
                band, columns[0], numbers, fit
            )
        used = 0 if fit is None else int(np.count_nonzero(fit[2]))
        if used < settings.min_labels:
            read = (
                ", ".join(f"'{lb.text}' at row {lb.row:.0f}" for lb in labels[:12])
                or "none"
            )
            raise DepthCalibrationError(
                f"Found {len(labels)} depth label(s) ({read}); {used} agree on one "
                f"line, but {settings.min_labels} are needed. Check the "
                "'depth_labels' image in the error's images, pass label_columns=, "
                "or pass depth=(top, base) instead.",
                images,
            )
        a, b, keep = fit
        source = "ocr"
        labels = numbers
        inliers = [bool(k) for k in keep]
        residuals = [float((lb.depth - b) / a - lb.row) for lb in labels]
        depth_rms = float(
            np.sqrt(np.mean([r * r for r, k in zip(residuals, inliers) if k]))
        )
        misread = [
            f"'{lb.text}' at row {lb.row:.0f}"
            for lb, k in zip(labels, inliers)
            if not k
        ]
        if misread:
            warnings.append(
                f"{len(misread)} depth label(s) disagree with the others and were "
                f"ignored as misreads: {', '.join(misread)}."
            )
        if used < 4:
            warnings.append(
                f"Depth rests on only {used} labels; check the depth_labels QC image."
            )
        if depth_rms > 1.5:
            warnings.append(
                f"The depth labels scatter {depth_rms:.1f} rows (RMS) about a straight "
                "line; the scan may be stretched."
            )

    depths = a * np.arange(height, dtype=float) + b
    raw: dict[str, Reading] = {}
    curve_qcs = []
    for c in curves:
        x0, x1, track_source, grid = picks[c.name]
        c0, c1 = max(0, math.floor(x0)), min(width - 1, math.ceil(x1))
        roi = page_bgr[:, c0 : c1 + 1]
        clean = clean_track_mask(
            masks[c.name][:, c0 : c1 + 1], x0 - c0, x1 - c0, settings, frames=c.dark
        )
        xs, ambiguous = trace_curve(clean)
        found = int(np.isfinite(xs).sum())
        xs, bridged = bridge_gaps(xs, settings.max_gap)
        values = map_x_to_value(xs + c0, x0, x1, c.vmin, c.vmax, c.scale)
        ok = np.isfinite(values)
        images[f"track_{c.name}"] = roi.copy()
        images[f"track_mask_{c.name}"] = clean.astype(np.uint8) * 255
        images[f"curve_overlay_{c.name}"] = curve_overlay(roi, xs, bridged)
        if ok.sum() < 2:
            raise DigitizeError(
                f"{c.name} was found in fewer than two rows of its track (columns "
                f"{x0:.0f}-{x1:.0f}); check its color= and track.",
                images,
            )
        raw[c.name] = Reading(depths[ok], values[ok], bridged[ok])
        if ambiguous > 0.1 * max(1, found):
            warnings.append(
                f"{c.name}: {ambiguous} rows hold two or more separate runs of {c.color}; "
                "another curve of that colour may be mixed in (curves of one colour "
                "in one track are not told apart)."
            )
        curve_qcs.append(
            CurveQC(
                c.name,
                c.color,
                c.scale,
                (float(x0), float(x1)),
                track_source,
                grid,
                found,
                int(bridged.sum()),
                int(ambiguous),
            )
        )

    spacing = (settings.max_gap + 1.5) * abs(a)
    top = min(float(r.depth.min()) for r in raw.values())
    base = max(float(r.depth.max()) for r in raw.values())
    out_depth = np.arange(top, base + 0.5 * step, step)
    outputs = []
    for c, cq in zip(curves, curve_qcs):
        reading = raw[c.name]
        values = resample(out_depth, reading.depth, reading.value, spacing)
        inside = (out_depth >= reading.depth.min()) & (out_depth <= reading.depth.max())
        cq.coverage = (
            100.0 * float(np.isfinite(values[inside]).mean()) if inside.any() else 0.0
        )
        outputs.append((c, values))

    note = f"Digitized with pphys.digitize from {path.name}, page {page}. Depth " + (
        "from manual calibration."
        if source == "manual"
        else f"from {sum(inliers)} OCR depth labels (linear fit)."
    )
    las = _build_las(
        out_depth,
        outputs,
        depth_unit=depth_unit,
        well=path.stem if well is None else well,
        null_value=settings.null_value,
        note=note,
    )
    qc = QC(
        scan=str(path),
        page=page,
        page_size=(width, height),
        tracks=[(t.x0, t.x1) for t in tracks],
        depth_source=source,
        depth_fit=(float(a), float(b)),
        curves=curve_qcs,
        depth_labels=[(lb.row, lb.depth) for lb in labels],
        depth_inliers=inliers,
        depth_residuals=residuals,
        depth_rms=depth_rms,
        label_columns=columns,
        warnings=warnings,
    )
    return DigitizeResult(las, qc, settings, images, raw)


def _curve_list(
    curves, curve, vmin, vmax, unit, scale, color, track, track_edges
) -> list[Curve]:
    """The curves to digitize, from ``curves`` or the one-curve shorthand."""
    if curves is not None:
        if curve is not None or vmin is not None or vmax is not None:
            raise ValueError("Give curves=[...] or curve/vmin/vmax, not both.")
        curves = list(curves)
        if not curves or not all(isinstance(c, Curve) for c in curves):
            raise ValueError("curves must be a non-empty list of Curve.")
    else:
        if curve is None or vmin is None or vmax is None:
            raise ValueError(
                "Name the curve and its scale: curve=, vmin= and vmax= (or curves=[Curve(...)])."
            )
        curves = [
            Curve(
                curve,
                vmin,
                vmax,
                unit=unit,
                scale=scale,
                color=color,
                track=track,
                track_edges=track_edges,
            )
        ]
    names = [c.name for c in curves]
    if len(set(names)) != len(names) or "DEPT" in names:
        raise ValueError(f"Curve names must be unique and not DEPT, not {names}.")
    return curves


def _curve_track(curve, tracks, mask, width, images):
    """Edges, their source, the detected track (for the grid check) and any
    warning, for one curve."""
    if curve.track_edges is not None:
        x0, x1 = curve.track_edges
        if x0 < 0 or x1 > width - 1:
            raise ValueError(
                f"{curve.name}: track_edges {curve.track_edges} must lie within the page "
                f"(0-{width - 1})."
            )
        chosen = max(tracks, key=lambda t: _overlap(t, x0, x1), default=None)
        if chosen is not None and _overlap(chosen, x0, x1) <= 0:
            chosen = None
        return x0, x1, "manual", chosen, None
    if not tracks:
        raise DigitizeError(
            "No track frames (long vertical lines) were found around the curve; "
            "pass track_edges=(left, right) in page columns (see the 'page' image).",
            images,
        )
    chosen, note = _pick_track(tracks, curve.track, mask)
    return chosen.x0, chosen.x1, "detected", chosen, note


def find_tesseract(path: str | os.PathLike | None = None) -> str:
    """Return the Tesseract executable to use.

    Looks, in order, at ``path``, the ``TESSERACT_CMD`` environment variable,
    the PATH, and on Windows the default install folders (``Program Files``
    and ``%LOCALAPPDATA%\\Programs``).

    Raises
    ------
    DigitizeError
        If none of them holds Tesseract.
    """
    if path is not None:
        if Path(path).is_file():
            return str(path)
        raise DigitizeError(f"Tesseract was not found at {path}.")
    candidates = [os.environ.get("TESSERACT_CMD"), shutil.which("tesseract")]
    if os.name == "nt":
        for base in (
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
        ):
            if base:
                candidates.append(os.path.join(base, "Tesseract-OCR", "tesseract.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise DigitizeError(
        "Tesseract OCR is needed to read the depth labels but was not found. "
        "Install it (https://github.com/tesseract-ocr/tesseract) and put it on "
        "the PATH, set TESSERACT_CMD or Settings(tesseract=...), or pass "
        "depth=(top, base) to skip OCR."
    )


def render_pdf_page(
    pdf_path: str | os.PathLike, page_index: int = 0, scale: float = 2.0
) -> np.ndarray:
    """Render a PDF page to a BGR image (OpenCV)."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        if not 0 <= page_index < len(pdf):
            raise DigitizeError(
                f"{Path(pdf_path).name} has {len(pdf)} page(s); page {page_index} does not exist."
            )
        rgb = np.array(pdf[page_index].render(scale=scale).to_pil())
    finally:
        pdf.close()
    if rgb.ndim == 2:
        return cv2.cvtColor(rgb, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(rgb[..., :3], cv2.COLOR_RGB2BGR)


def curve_mask(
    bgr: np.ndarray, color: str = "red", settings: Settings | None = None
) -> np.ndarray:
    """Mask (0 or 255) of the pixels in ``color``.

    Coloured curves are matched by hue (within ``Settings.hue_tolerance``,
    with enough saturation and brightness), so faded ink still counts; black
    and greys by darkness (low saturation, at most ``gray_tolerance``
    brighter than the colour). Specks smaller than ``Settings.min_blob``
    pixels are dropped.
    """
    settings = Settings() if settings is None else settings
    hue, saturation, value = _hsv_of(color)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    if saturation < GRAY_SATURATION:
        mask = (hsv[..., 1] <= settings.gray_saturation) & (
            hsv[..., 2] <= min(255, value + settings.gray_tolerance)
        )
    else:
        dh = np.abs(hsv[..., 0].astype(np.int16) - hue)
        dh = np.minimum(dh, 180 - dh)
        mask = (
            (dh <= settings.hue_tolerance)
            & (hsv[..., 1] >= settings.min_saturation)
            & (hsv[..., 2] >= settings.min_value)
        )
    return _drop_blobs(mask, settings.min_blob).astype(np.uint8) * 255


def clean_track_mask(
    mask: np.ndarray,
    left: float,
    right: float,
    settings: Settings | None = None,
    frames: bool = False,
) -> np.ndarray:
    """The curve's pixels in a track crop (boolean).

    Removed: lines running across the track (rows 70 % covered), full-height
    lines when there are three or more (a grid in the curve's colour; one
    alone may be a constant curve), the frame columns at ``left``/``right``
    (crop columns) when ``frames`` (dark curves share the frames' colour),
    and specks.
    """
    settings = Settings() if settings is None else settings
    m = mask > 0
    if frames:
        m[:, : max(0, math.floor(left) + 3)] = False
        m[:, max(0, math.ceil(right) - 2) :] = False
    m[m.mean(axis=1) >= 0.7] = False
    lines = _runs(m.mean(axis=0) >= settings.min_line_fraction)
    if len(lines) >= 3:
        for start, stop in lines:
            m[:, start:stop] = False
    return _drop_blobs(m, settings.min_blob)


def trace_curve(mask: np.ndarray, join: int = 3) -> tuple[np.ndarray, int]:
    """Follow a curve down a track mask, one column per row.

    In each row, runs of pixels closer than ``join`` columns are joined and a
    run's centre is its column. A row with one run takes it; a row with
    several takes the one nearest the curve in the neighbouring rows, so
    stray marks don't pull the curve off. Returns the columns (NaN where the
    row is empty) and the number of rows that held several runs.
    """
    centres = []
    for row in mask:
        merged: list[list[int]] = []
        for start, stop in _runs(row):
            if merged and start - merged[-1][1] <= join:
                merged[-1][1] = stop
            else:
                merged.append([start, stop])
        centres.append([(start + stop - 1) / 2.0 for start, stop in merged])

    xs = np.full(len(centres), np.nan)
    for y, found in enumerate(centres):
        if len(found) == 1:
            xs[y] = found[0]
    several = [y for y, found in enumerate(centres) if len(found) > 1]
    if several and not np.isfinite(xs).any():
        first = centres[several[0]]
        xs[several[0]] = first[len(first) // 2]  # no single-run row to start from
    if several:
        for order in (range(len(xs)), range(len(xs) - 1, -1, -1)):
            last = np.nan
            for y in order:
                if np.isfinite(xs[y]):
                    last = xs[y]
                elif len(centres[y]) > 1 and np.isfinite(last):
                    xs[y] = min(centres[y], key=lambda x, last=last: abs(x - last))
                    last = xs[y]
    return xs, len(several)


def bridge_gaps(xs: np.ndarray, max_gap: int) -> tuple[np.ndarray, np.ndarray]:
    """Interpolate across gaps of up to ``max_gap`` empty rows.

    Returns the filled columns (longer gaps stay NaN) and which rows were
    filled.
    """
    xs = np.array(xs, dtype=float)
    bridged = np.zeros(len(xs), dtype=bool)
    rows = np.flatnonzero(np.isfinite(xs))
    for a, b in zip(rows[:-1], rows[1:]):
        if 1 < b - a <= max_gap + 1:
            xs[a + 1 : b] = np.interp(np.arange(a + 1, b), [a, b], [xs[a], xs[b]])
            bridged[a + 1 : b] = True
    return xs, bridged


def find_vertical_lines(
    page_bgr: np.ndarray,
    settings: Settings | None = None,
    exclude: np.ndarray | None = None,
) -> list[Line]:
    """Long vertical printed lines (track frames and grid lines), left to right.

    A pixel is line ink when it is ``Settings.ink_contrast`` darker than the
    paper (the median grey) and not in ``exclude`` (e.g. the curve mask); a
    run of columns whose ink covers ``Settings.min_line_fraction`` of the
    page height is one line.
    """
    settings = Settings() if settings is None else settings
    gray, paper, ink = _line_ink(page_bgr, settings, exclude)
    return _vertical_lines(gray, paper, ink, settings)


def find_tracks(
    page_bgr: np.ndarray,
    settings: Settings | None = None,
    curve: np.ndarray | None = None,
    exclude: np.ndarray | None = None,
) -> list[Track]:
    """Tracks found from their frame lines, left to right.

    The darkest long vertical lines are frames, the lighter ones grid lines
    (``Settings.frame_tolerance``). The span between two neighbouring frames
    is a track when it holds grid lines, ``curve`` pixels (the curve mask)
    in at least 30 % of its rows, or horizontal grid lines running across it; so the depth column
    and margins are skipped and tracks sharing a frame are told apart. When
    all lines are equally dark, a track is a run of lines whose gaps are all
    crossed by horizontal grid lines. ``exclude`` (``curve`` by default) is
    kept out of the line ink: coloured curves, not black ones, which share
    the frames' colour.
    """
    settings = Settings() if settings is None else settings
    gray, paper, ink = _line_ink(
        page_bgr, settings, curve if exclude is None else exclude
    )
    lines = _vertical_lines(gray, paper, ink, settings)
    if len(lines) < 2:
        return []
    strongest = max(line.strength for line in lines)
    frames = [ln for ln in lines if ln.strength >= settings.frame_tolerance * strongest]
    grid = [ln.x for ln in lines if ln.strength < settings.frame_tolerance * strongest]
    if not grid and len(frames) > 6:
        return _tracks_by_crossing([ln.x for ln in lines], ink, settings)

    tracks = []
    for left, right in zip(frames, frames[1:]):
        if right.x - left.x < settings.min_track_width:
            continue
        inside = [x for x in grid if left.x < x < right.x]
        inner = slice(math.floor(left.x) + 2, math.ceil(right.x) - 1)
        # A curve runs down most of its track; text in a curve's colour (black
        # depth labels, for a black curve) covers only a few rows.
        has_curve = curve is not None and curve[:, inner].any(axis=1).mean() >= 0.3
        if inside or has_curve or _crossed(ink, left.x, right.x):
            tracks.append(Track(left.x, right.x, inside))
    return tracks


def grid_kind(track: Track) -> str | None:
    """What a track's vertical grid looks like: "linear", "log10" or None (unclear).

    Evenly spaced lines read as linear. Spacing that keeps shrinking (or
    growing, on a flipped track) and jumps back once per decade reads as
    log10. Needs at least four grid lines.
    """
    if len(track.grid) < 4:
        return None
    gaps = np.diff([track.x0, *sorted(track.grid), track.x1])
    spread = gaps.std() / gaps.mean()
    if spread < 0.15:
        return "linear"
    ratios = gaps[1:] / gaps[:-1]
    monotone = max(np.mean(ratios < 1.0), np.mean(ratios > 1.0))
    if spread > 0.3 and monotone >= 0.6:
        return "log10"
    return None


def label_bands(
    tracks: list[Track], width: int, columns: tuple[float, float] | None = None
) -> list[tuple[float, float]]:
    """Column bands that may hold the depth labels: ``columns`` when given,
    otherwise every band between the tracks and in the margins."""
    if columns is not None:
        x0, x1 = sorted(float(c) for c in columns)
        return [(max(0.0, x0), min(width - 1.0, x1))]
    bands, left = [], 0.0
    for x0, x1 in sorted((t.x0, t.x1) for t in tracks):
        if x0 - left >= 8:
            bands.append((left, x0))
        left = max(left, x1)
    if width - 1 - left >= 8:
        bands.append((left, width - 1.0))
    return bands


def find_depth_labels(
    page_bgr: np.ndarray,
    tracks: list[Track],
    settings: Settings | None = None,
    columns: tuple[float, float] | None = None,
) -> tuple[tuple[float, float] | None, list[Label]]:
    """Find and read the depth labels.

    Every band of :func:`label_bands` is read with :func:`read_labels`; the
    band whose numbers best agree on one straight line wins. A label's row
    is snapped onto the horizontal grid line it marks when one runs across a
    track within half its text height (labels sit on, above or beside their
    line). Returns that band's columns (None if no band holds text) and its
    labels, top to bottom.
    """
    settings = Settings() if settings is None else settings
    grid = _grid_rows(page_bgr, tracks, settings)
    best_band, best_labels, best_key = None, [], (-1, -1)
    for band in label_bands(tracks, page_bgr.shape[1], columns):
        labels = _snap_labels(read_labels(page_bgr, band, settings), grid)
        if not labels:
            continue
        points = [(lb.row, lb.depth) for lb in labels if lb.depth is not None]
        fit = fit_depth(points, settings.label_tolerance)
        key = (0 if fit is None else int(np.count_nonzero(fit[2])), len(labels))
        if key > best_key:
            best_band, best_labels, best_key = band, labels, key
    return best_band, best_labels


def read_labels(
    page_bgr: np.ndarray, band: tuple[float, float], settings: Settings | None = None
) -> list[Label]:
    """Read the numbers printed in a column band, top to bottom.

    Text blobs are found as connected ink (lines across the band removed,
    characters merged sideways), enlarged to about 32 pixels high, stacked
    into one sheet and read by Tesseract in a single call, allowing digits,
    '.' and '-'. Blobs read with less than ``Settings.ocr_min_confidence``
    are dropped.
    """
    settings = Settings() if settings is None else settings
    c0 = max(0, math.ceil(band[0]) + 2)
    c1 = min(page_bgr.shape[1], math.floor(band[1]) - 1)
    if c1 - c0 < 4:
        return []
    gray = cv2.cvtColor(page_bgr[:, c0:c1], cv2.COLOR_BGR2GRAY)
    paper = float(np.median(gray))
    ink = (gray < paper - settings.ink_contrast).astype(np.uint8)
    ink[ink.mean(axis=1) > 0.6] = 0  # lines across the band are not text
    boxes = _text_boxes(ink, settings)
    if not boxes:
        return []
    labels = []
    for (x, y, w, h), (text, conf) in zip(boxes, _ocr_boxes(gray, boxes, settings)):
        if not text or conf < settings.ocr_min_confidence:
            continue
        labels.append(
            Label(
                row=y + (h - 1) / 2.0,
                depth=_parse_number(text),
                text=text,
                confidence=conf,
                box=(c0 + x, y, c0 + x + w - 1, y + h - 1),
            )
        )
    return labels


def fit_depth(
    points: Sequence[tuple[float, float]], tolerance: float = 3.0
) -> tuple[float, float, np.ndarray] | None:
    """Fit ``depth = a * row + b`` to ``(row, depth)`` points, ignoring misreads.

    Every pair of points proposes a line with depth increasing downward
    (``a > 0``); the line that the most points lie within ``tolerance`` rows
    of wins and is refitted to them by least squares. Returns ``(a, b,
    inliers)``, or None without two usable points.
    """
    if len(points) < 2:
        return None
    rows = np.array([p[0] for p in points], dtype=float)
    depths = np.array([p[1] for p in points], dtype=float)
    best_key, best = None, None
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            dr, dd = rows[j] - rows[i], depths[j] - depths[i]
            if dr == 0 or dd / dr <= 0:
                continue
            a = dd / dr
            b = depths[i] - a * rows[i]
            residual = np.abs((depths - b) / a - rows)
            keep = residual <= tolerance
            key = (int(keep.sum()), -float(residual[keep].sum()))
            if best_key is None or key > best_key:
                best_key, best = key, keep
    if best is None:
        return None
    for _ in range(2):
        a, b = np.polyfit(rows[best], depths[best], 1)
        if a <= 0:
            return None
        refit = np.abs((depths - b) / a - rows) <= tolerance
        if refit.sum() < 2 or np.array_equal(refit, best):
            break
        best = refit
    a, b = np.polyfit(rows[best], depths[best], 1)
    return float(a), float(b), best


def map_x_to_value(
    x_px: np.ndarray,
    x_left: float,
    x_right: float,
    vmin: float,
    vmax: float,
    scale: str = "linear",
) -> np.ndarray:
    """Map columns so that ``x_left`` -> ``vmin`` and ``x_right`` -> ``vmax``.

    Linearly, or for ``scale="log10"`` linearly in the logarithm of the value.
    """
    fraction = (np.asarray(x_px, dtype=float) - x_left) / (x_right - x_left)
    if scale == "log10":
        lo, hi = math.log10(vmin), math.log10(vmax)
        return 10.0 ** (lo + fraction * (hi - lo))
    return vmin + fraction * (vmax - vmin)


def resample(
    depth: np.ndarray,
    raw_depth: np.ndarray,
    raw_value: np.ndarray,
    max_spacing: float = np.inf,
) -> np.ndarray:
    """A reading's values at ``depth``, by linear interpolation.

    NaN outside the reading, and inside gaps where neighbouring readings are
    more than ``max_spacing`` apart, so a curve's gaps stay gaps.
    """
    order = np.argsort(raw_depth)
    d = np.asarray(raw_depth, dtype=float)[order]
    v = np.asarray(raw_value, dtype=float)[order]
    out = np.interp(depth, d, v, left=np.nan, right=np.nan)
    if len(d) > 1:
        i = np.clip(np.searchsorted(d, depth), 1, len(d) - 1)
        out[(d[i] - d[i - 1]) > max_spacing] = np.nan
    return out


def curve_overlay(
    roi_bgr: np.ndarray, xs: np.ndarray, bridged: np.ndarray | None = None
) -> np.ndarray:
    """The track with the column read in each row marked: cyan where the curve
    was found, magenta where a short gap was bridged."""
    overlay = roi_bgr.copy()
    bridged = np.zeros(len(xs), dtype=bool) if bridged is None else bridged
    for y, (x, filled) in enumerate(zip(xs, bridged)):
        if np.isfinite(x):
            color = (255, 0, 255) if filled else (255, 255, 0)
            cv2.circle(overlay, (int(round(x)), y), 1, color, -1)
    return overlay


def depth_labels_overlay(
    band_bgr: np.ndarray,
    x_offset: float,
    labels: Sequence[Label],
    fit: tuple[float, float, np.ndarray] | None,
) -> np.ndarray:
    """The label band, widened, with each label boxed and annotated: green
    when on the fitted line, red when ignored, and the depth the line gives
    at the label's row."""
    height, width = band_bgr.shape[:2]
    canvas = np.full((height, width + 150, 3), 255, dtype=np.uint8)
    canvas[:, :width] = band_bgr
    font, off = cv2.FONT_HERSHEY_SIMPLEX, math.floor(x_offset)
    keep = fit[2] if fit is not None else [True] * len(labels)
    for label, inlier in zip(labels, keep):
        x0, y0, x1, y1 = label.box
        color = (0, 160, 0) if inlier else (0, 0, 220)
        cv2.rectangle(canvas, (x0 - off - 1, y0 - 1), (x1 - off + 1, y1 + 1), color, 1)
        note = label.text
        if fit is not None:
            note += f" -> {fit[0] * label.row + fit[1]:.2f}"
        cv2.putText(canvas, note, (width + 4, int(label.row) + 4), font, 0.4, color, 1)
    if fit is not None:
        cv2.putText(
            canvas,
            f"d={fit[0]:.5f}*row+{fit[1]:.2f}",
            (4, 14),
            font,
            0.4,
            (200, 0, 0),
            1,
        )
    return canvas


def _pick_track(
    tracks: list[Track], track: str | int, curve: np.ndarray
) -> tuple[Track, str | None]:
    """The track chosen by ``track``, and a warning when "auto" was a close call."""
    if track == "left":
        return tracks[0], None
    if track == "right":
        return tracks[-1], None
    if isinstance(track, (int, np.integer)) and not isinstance(track, bool):
        if 0 <= track < len(tracks):
            return tracks[track], None
        raise DigitizeError(
            f"track {track} does not exist: {len(tracks)} track(s) were found."
        )
    if track != "auto":
        raise ValueError(
            f"track must be 'auto', 'left', 'right' or an index, not {track!r}."
        )
    counts = [
        int(np.count_nonzero(curve[:, math.ceil(t.x0) + 3 : math.floor(t.x1) - 2]))
        for t in tracks
    ]
    order = np.argsort(counts)[::-1]
    best = int(order[0])
    if counts[best] == 0:
        raise DigitizeError(
            f"None of the {len(tracks)} track(s) found holds the curve colour; "
            "check the curve's color=, or pass track_edges."
        )
    note = None
    if len(tracks) > 1 and counts[int(order[1])] >= 0.5 * counts[best]:
        note = (
            f"Tracks {best} and {int(order[1])} both hold the curve colour; read track "
            f"{best}, which holds more. Pass track= to choose."
        )
    return tracks[best], note


def _overlap(track: Track, x0: float, x1: float) -> float:
    """Columns shared by a track and the span ``x0-x1``."""
    return min(track.x1, x1) - max(track.x0, x0)


def _runs(on: np.ndarray):
    """``(start, stop)`` of every run of True values."""
    edges = np.flatnonzero(np.diff(np.concatenate([[0], on.astype(np.int8), [0]])))
    return list(zip(edges[::2], edges[1::2]))


def _line_ink(page_bgr, settings, exclude):
    """Grey page, paper level, and the mask of printed-line pixels."""
    gray = cv2.cvtColor(page_bgr, cv2.COLOR_BGR2GRAY)
    paper = float(np.median(gray))
    ink = gray < paper - settings.ink_contrast
    if exclude is not None:
        ink &= exclude == 0
    return gray, paper, ink


def _vertical_lines(gray, paper, ink, settings) -> list[Line]:
    fraction = ink.mean(axis=0)
    lines = []
    for start, stop in _runs(fraction >= settings.min_line_fraction):
        weights = fraction[start:stop]
        x = float((np.arange(start, stop) * weights).sum() / weights.sum())
        darkest = gray[:, start:stop].min(axis=1)
        lines.append(Line(x, int(stop - start), paper - float(np.median(darkest))))
    return lines


def _crossed(ink: np.ndarray, x0: float, x1: float, runs: int = 3) -> bool:
    """Whether at least ``runs`` horizontal lines run across the gap ``x0-x1``,
    as a track's depth grid does (the depth column and margins have none)."""
    c0, c1 = math.floor(x0) + 2, math.ceil(x1) - 1
    if c1 - c0 < 3:
        return True  # lines this close belong together
    full = ink[:, c0:c1].mean(axis=1) >= 0.9
    return len(_runs(full)) >= runs


def _tracks_by_crossing(
    xs: list[float], ink: np.ndarray, settings: Settings
) -> list[Track]:
    """Tracks as runs of lines whose gaps are all crossed by horizontal grid lines."""
    xs = sorted(xs)
    groups, current = [], [xs[0]]
    for a, b in zip(xs, xs[1:]):
        if _crossed(ink, a, b):
            current.append(b)
        else:
            groups.append(current)
            current = [b]
    groups.append(current)
    return [
        Track(g[0], g[-1], g[1:-1])
        for g in groups
        if len(g) >= 2 and g[-1] - g[0] >= settings.min_track_width
    ]


def _text_boxes(ink: np.ndarray, settings: Settings) -> list[tuple[int, int, int, int]]:
    """``(x, y, w, h)`` of text blobs in an ink mask, top to bottom: characters
    merged sideways, then kept when their height fits a label."""
    reach = max(1, settings.min_label_height // 2)
    merged = cv2.dilate(ink, np.ones((1, 2 * reach + 1), np.uint8))
    _, _, stats, _ = cv2.connectedComponentsWithStats(merged, connectivity=8)
    boxes = []
    for x, y, w, h, _area in stats[1:]:
        x, w = x + reach, w - 2 * reach  # undo the sideways merge
        if settings.min_label_height <= h <= settings.max_label_height and w >= 0.4 * h:
            boxes.append((int(x), int(y), int(w), int(h)))
    return sorted(boxes, key=lambda b: b[1])


def _ocr_boxes(gray: np.ndarray, boxes, settings: Settings) -> list[tuple[str, float]]:
    """Read each box with one Tesseract call: the boxes, enlarged and
    binarized, are stacked on a white sheet and the words mapped back."""
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = find_tesseract(settings.tesseract)
    gap, pieces, spans, y = 24, [], [], 24
    for x, yb, w, h in boxes:
        pad = max(2, h // 4)
        crop = gray[max(0, yb - pad) : yb + h + pad, max(0, x - pad) : x + w + pad]
        zoom = min(6.0, max(1.0, 32.0 / h))
        big = cv2.resize(crop, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_CUBIC)
        _, bw = cv2.threshold(big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        pieces.append(bw)
        spans.append((y, y + bw.shape[0]))
        y += bw.shape[0] + gap
    sheet = np.full((y, max(p.shape[1] for p in pieces) + 2 * gap), 255, dtype=np.uint8)
    for piece, (y0, y1) in zip(pieces, spans):
        sheet[y0:y1, gap : gap + piece.shape[1]] = piece

    config = "--psm 6 -c tessedit_char_whitelist=0123456789.-"
    data = pytesseract.image_to_data(
        sheet, output_type=pytesseract.Output.DICT, config=config
    )
    words = [[] for _ in boxes]
    for i, text in enumerate(data["text"]):
        text = (text or "").strip()
        if not text:
            continue
        centre = data["top"][i] + data["height"][i] / 2.0
        for k, (y0, y1) in enumerate(spans):
            if y0 <= centre < y1:
                words[k].append((data["left"][i], text, float(data["conf"][i])))
                break
    out = []
    for found in words:
        found.sort()
        out.append(
            ("".join(t for _, t, _ in found), min((c for *_, c in found), default=-1.0))
        )
    return out


def _parse_number(text: str) -> float | None:
    """The number a label reads, or None ("12-5", "." and the like)."""
    return float(text) if re.fullmatch(r"-?\d+(\.\d+)?", text) else None


def _grid_rows(
    page_bgr: np.ndarray, tracks: list[Track], settings: Settings
) -> np.ndarray:
    """Centre rows of the horizontal lines that run across a track (its depth grid)."""
    gray = cv2.cvtColor(page_bgr, cv2.COLOR_BGR2GRAY)
    # Half the usual contrast: a row must also cover 80 % of the track to count,
    # so faint (faded) grid lines are found without picking up noise.
    ink = gray < float(np.median(gray)) - settings.ink_contrast / 2.0
    rows: list[float] = []
    for track in tracks:
        c0, c1 = math.ceil(track.x0) + 2, math.floor(track.x1) - 1
        if c1 - c0 < 5:
            continue
        full = ink[:, c0:c1].mean(axis=1) >= 0.8
        rows += [(start + stop - 1) / 2.0 for start, stop in _runs(full)]
    return np.unique(np.round(rows, 1))


def _snap_labels(labels: list[Label], grid: np.ndarray) -> list[Label]:
    """Move each label's row onto the grid line it marks: the nearest line
    within half its text height plus a pixel; others keep their text centre."""
    if grid.size == 0:
        return labels
    out = []
    for label in labels:
        reach = (label.box[3] - label.box[1] + 1) / 2.0 + 1.0
        nearest = grid[np.abs(grid - label.row).argmin()]
        row = float(nearest) if abs(nearest - label.row) <= reach else label.row
        out.append(Label(row, label.depth, label.text, label.confidence, label.box))
    return out


def _parse_depth(depth) -> tuple[str, list]:
    """Validate a manual depth calibration: ("page", [top, base]) or ("rows", pairs)."""
    try:
        values = [float(v) for v in depth]
    except TypeError:
        values = None
    if values is not None:
        if len(values) != 2 or values[0] == values[1]:
            raise ValueError("depth=(top, base) needs two different depths.")
        return "page", values
    pairs = [(float(row), float(d)) for row, d in depth]
    if len(pairs) < 2 or len({row for row, _ in pairs}) < 2:
        raise ValueError(
            "depth as (row, depth) pairs needs at least two different rows."
        )
    return "rows", pairs


def _manual_fit(manual: tuple[str, list], height: int) -> tuple[float, float]:
    kind, data = manual
    if kind == "page":
        top, base = data
        return (base - top) / max(1.0, float(height - 1)), top
    rows, depths = np.array(data, dtype=float).T
    a, b = np.polyfit(rows, depths, 1)
    return float(a), float(b)


def _build_las(depth, outputs, *, depth_unit, well, null_value, note) -> WellLog:
    las = WellLog()
    las.well["WELL"].value = well
    las.well["NULL"].value = null_value
    las.append_curve("DEPT", depth, unit=DEPTH_UNITS[depth_unit], descr="Depth")
    for curve, values in outputs:
        las.append_curve(
            curve.name,
            values,
            unit=curve.unit,
            descr=f"Digitized {curve.color} curve, {curve.scale} scale {curve.vmin:g} to {curve.vmax:g}",
        )
    las.other = note
    return las


def _hsv_of(color: str) -> tuple[int, int, int]:
    """OpenCV HSV (hue 0-180, saturation and value 0-255) of a matplotlib colour."""
    r, g, b = to_rgb(color)
    pixel = np.uint8([[[round(b * 255), round(g * 255), round(r * 255)]]])
    h, s, v = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0, 0]
    return int(h), int(s), int(v)


def _drop_blobs(mask: np.ndarray, min_area: int) -> np.ndarray:
    """``mask`` (boolean) without connected pieces smaller than ``min_area`` pixels."""
    mask = mask > 0
    if min_area <= 1 or not mask.any():
        return mask
    _, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8
    )
    keep = stats[:, cv2.CC_STAT_AREA] >= min_area
    keep[0] = False
    return keep[labels]


def _write_image(path: Path, image: np.ndarray) -> None:
    # cv2.imwrite cannot write to non-ASCII paths on Windows.
    ok, buffer = cv2.imencode(".png", image)
    if not ok:
        raise DigitizeError(f"Could not encode {path.name}.")
    path.write_bytes(buffer.tobytes())
