"""Digitize one curve of a scanned log (PDF) into a :class:`pphys.WellLog`.

The pipeline, one curve per call:

1. Render a PDF page (pypdfium2).
2. Mask the curve colour (HSV, red by default) and find the tracks as
   clusters of columns that hold many curve pixels.
3. Calibrate depth: from the depths given, or by reading the depth labels
   between the first and last track with Tesseract OCR and fitting
   ``depth = a * row + b``.
4. Take the median column of the curve pixels in each row and map it linearly
   onto ``[vmin, vmax]`` across the track.
5. Resample to a regular depth step and build the WellLog.

Known limits, left to later roadmap steps: without ``track_edges`` the value
scale spans the curve's own columns plus a margin, not the track edges; one
colour and one curve per call; linear scales; PDF input only.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

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

    The defaults are those of the scans the prototype was built on.

    Parameters
    ----------
    render_scale : float
        PDF render scale; 1.0 renders at 72 dpi.
    hue_bands : tuple of (int, int)
        Curve colour as OpenCV hue ranges (0-180). Red wraps around 0, hence
        two bands by default.
    min_saturation, min_value : int
        Lower HSV saturation and value (0-255) of a curve pixel.
    mask_kernel : int
        Size of the opening and closing that clean the colour mask.
    min_track_width : int
        Tracks, and column clusters of curve pixels, narrower than this are
        ignored.
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
    hue_bands: tuple[tuple[int, int], ...] = ((0, 10), (160, 180))
    min_saturation: int = 70
    min_value: int = 50
    mask_kernel: int = 3
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
            "mask_kernel",
            "min_track_width",
            "min_label_height",
            "label_tolerance",
        )
        for name in positive:
            if not getattr(self, name) > 0:
                raise ValueError(
                    f"{name} must be positive, not {getattr(self, name)!r}."
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
        for name in ("min_saturation", "min_value"):
            if not 0 <= getattr(self, name) <= 255:
                raise ValueError(
                    f"{name} must be in 0-255, not {getattr(self, name)!r}."
                )
        bands = tuple((int(lo), int(hi)) for lo, hi in self.hue_bands)
        if not bands or any(not 0 <= lo <= hi <= 180 for lo, hi in bands):
            raise ValueError(
                f"hue_bands must be (low, high) pairs within 0-180, not {self.hue_bands!r}."
            )
        object.__setattr__(self, "hue_bands", bands)


@dataclass
class Cluster:
    """A run of columns with many curve pixels."""

    x0: int
    x1: int
    score: float


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
    track : (float, float)
        Columns of the left and right edge of the track read, where the
        values are ``vmin`` and ``vmax``.
    track_source : str
        "detected" (found from its frame lines) or "manual" (``track_edges``).
    scale : str
        "linear" or "log10", as given.
    depth_source : str
        "manual" (depths given) or "ocr" (depth labels read).
    depth_fit : (float, float)
        ``(a, b)`` of ``depth = a * row + b``.
    grid : str or None
        What the vertical grid of the track looks like: "linear" (evenly
        spaced), "log10" (bunching toward each decade), or None if unclear.
    curve_clusters : list of (int, int)
        Column ranges of the curve-coloured pixels, left to right.
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
    coverage : float
        Percent of the resampled depths that have a value.
    warnings : list of str
        Things to check before trusting the result.
    """

    scan: str
    page: int
    page_size: tuple[int, int]
    tracks: list[tuple[float, float]]
    track: tuple[float, float]
    track_source: str
    scale: str
    depth_source: str
    depth_fit: tuple[float, float]
    grid: str | None = None
    curve_clusters: list[tuple[int, int]] = field(default_factory=list)
    depth_labels: list[tuple[float, float]] = field(default_factory=list)
    depth_inliers: list[bool] = field(default_factory=list)
    depth_residuals: list[float] = field(default_factory=list)
    depth_rms: float | None = None
    label_columns: tuple[float, float] | None = None
    coverage: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """A few lines for the console."""
        a, b = self.depth_fit
        lines = [
            f"scan: {self.scan} (page {self.page}, {self.page_size[0]} x {self.page_size[1]} px)",
            f"track: columns {self.track[0]:.1f}-{self.track[1]:.1f} ({self.track_source}; "
            f"{len(self.tracks)} track(s) found), {self.scale} scale"
            + (f", grid looks {self.grid}" if self.grid else ""),
            f"depth: {self.depth_source}, depth = {a:.6g} * row + {b:.6g}",
        ]
        if self.depth_source == "ocr":
            used = sum(self.depth_inliers)
            lines.append(
                f"depth labels: {used} of {len(self.depth_labels)} on the line, "
                f"RMS {self.depth_rms:.2f} rows"
            )
        lines.append(f"coverage: {self.coverage:.1f}%")
        lines += [f"warning: {w}" for w in self.warnings]
        return "\n".join(lines)


@dataclass
class DigitizeResult:
    """The outcome of :func:`digitize`.

    Parameters
    ----------
    las : WellLog
        The depth index and the digitized curve, resampled to a regular step.
    qc : QC
        Track, depth calibration, coverage and warnings.
    settings : Settings
        The settings used.
    images : dict of str to numpy.ndarray
        QC images by name: "page", "mask", "track", "track_mask",
        "curve_overlay", and for OCR "depth_labels".
    depth, value : numpy.ndarray
        The curve as read, one sample per page row that holds it, before
        resampling.
    """

    las: WellLog
    qc: QC
    settings: Settings
    images: dict[str, np.ndarray]
    depth: np.ndarray
    value: np.ndarray

    def save(self, outdir: str | os.PathLike, name: str | None = None) -> Path:
        """Write the LAS file, the raw curve, the QC images and ``qc.json``.

        Files: ``<name>.las``, ``<name>.csv`` (depth, value as read),
        ``<image>.png`` for every QC image, and ``qc.json`` (QC and
        settings). ``name`` defaults to the scan's file name. Returns the
        LAS path.
        """
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        name = name or Path(self.qc.scan).stem

        las_path = out / f"{name}.las"
        self.las.write(str(las_path), version=2.0)
        np.savetxt(
            out / f"{name}.csv",
            np.column_stack([self.depth, self.value]),
            delimiter=",",
            header="depth,value",
            comments="",
        )
        for key, image in self.images.items():
            _write_image(out / f"{key}.png", image)
        report = {"qc": asdict(self.qc), "settings": asdict(self.settings)}
        (out / "qc.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return las_path


def digitize(
    scan: str | os.PathLike,
    *,
    curve: str,
    vmin: float,
    vmax: float,
    unit: str = "",
    scale: str = "linear",
    depth: Sequence[float] | Sequence[tuple[float, float]] | None = None,
    depth_unit: str = "m",
    step: float | None = None,
    page: int = 0,
    track: str | int = "auto",
    track_edges: tuple[float, float] | None = None,
    label_columns: tuple[float, float] | None = None,
    well: str | None = None,
    settings: Settings | None = None,
) -> DigitizeResult:
    """Digitize one curve of a scanned log page into a WellLog.

    Parameters
    ----------
    scan : str or path
        A PDF file.
    curve : str
        Mnemonic of the digitized curve, e.g. "GR".
    vmin, vmax : float
        Values at the left and right edge of the track (vmin > vmax for a
        flipped track).
    unit : str
        Unit of the curve, e.g. "gAPI".
    scale : {"linear", "log10"}
        The track's scale, as printed in the log header. A QC warning flags
        a grid that looks like the other kind.
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
    track : "auto", "left", "right" or int
        Which detected track to read: the one holding the most pixels of the
        curve colour ("auto"), the first or last one, or its index from the
        left. Tracks are found from their frame lines (see :func:`find_tracks`).
    track_edges : (float, float), optional
        Columns of the rendered page at the track's left and right edges,
        where the values are ``vmin`` and ``vmax``; overrides the detection
        and ``track``.
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
        ``.las`` (the WellLog), ``.qc`` and the QC images; ``.save(dir)``
        writes them.

    Raises
    ------
    DepthCalibrationError
        If depth cannot be calibrated: no labels found, or fewer than
        ``Settings.min_labels`` of them on one line.
    DigitizeError
        If no curve is found, no track frames are found (pass
        ``track_edges``), the track does not exist, or Tesseract is needed
        but missing.
    """
    settings = Settings() if settings is None else settings
    path = Path(scan)
    if not path.is_file():
        raise FileNotFoundError(f"No such scan: {path}")
    if path.suffix.lower() != ".pdf":
        raise DigitizeError(
            f"{path.name}: only PDF scans are read for now; convert an image to PDF first."
        )
    if not str(curve).strip():
        raise ValueError("curve needs a mnemonic, e.g. curve='GR'.")
    if vmin == vmax:
        raise ValueError("vmin and vmax must differ.")
    if scale not in SCALES:
        raise ValueError(f"scale must be 'linear' or 'log10', not {scale!r}.")
    if scale == "log10" and min(vmin, vmax) <= 0:
        raise ValueError("A log10 scale needs positive vmin and vmax.")
    if depth_unit not in DEPTH_UNITS:
        raise ValueError(f"depth_unit must be 'm' or 'ft', not {depth_unit!r}.")
    step = DEFAULT_STEP[depth_unit] if step is None else float(step)
    if step <= 0:
        raise ValueError(f"step must be positive, not {step!r}.")
    manual = None if depth is None else _parse_depth(depth)

    page_bgr = render_pdf_page(path, page, settings.render_scale)
    height, width = page_bgr.shape[:2]
    mask = curve_mask(page_bgr, settings)
    images = {"page": page_bgr, "mask": mask}

    clusters = find_clusters(mask, settings.min_track_width)
    if not clusters:
        raise DigitizeError(
            "No curve of the chosen colour was found on the page; check "
            "Settings.hue_bands and Settings.render_scale.",
            images,
        )
    warnings: list[str] = []
    tracks = find_tracks(page_bgr, settings, curve=mask)

    # The track's edges, where the values are vmin and vmax.
    if track_edges is not None:
        x0, x1 = sorted(float(v) for v in track_edges)
        if x0 < 0 or x1 > width - 1 or x1 - x0 < 2:
            raise ValueError(
                f"track_edges {tuple(track_edges)} must be two columns within the page (0-{width - 1})."
            )
        track_source = "manual"
        chosen = max(tracks, key=lambda t: _overlap(t, x0, x1), default=None)
        if chosen is not None and _overlap(chosen, x0, x1) <= 0:
            chosen = None
    else:
        if not tracks:
            raise DigitizeError(
                "No track frames (long vertical lines) were found around the curve; "
                "pass track_edges=(left, right) in page columns (see the 'page' image).",
                images,
            )
        chosen, note = _pick_track(tracks, track, mask)
        if note:
            warnings.append(note)
        x0, x1 = chosen.x0, chosen.x1
        track_source = "detected"

    grid = grid_kind(chosen) if chosen is not None else None
    if grid is not None and grid != scale:
        warnings.append(
            f"The track's grid looks {grid} ("
            + ("evenly spaced" if grid == "linear" else "bunching toward each decade")
            + f") but scale='{scale}'; check the scale printed in the log header."
        )

    # Crop whole columns around the edges; values use the exact (sub-pixel) edges.
    c0, c1 = max(0, math.floor(x0)), min(width - 1, math.ceil(x1))
    roi = page_bgr[:, c0 : c1 + 1].copy()
    images["track"] = roi

    labels: list[Label] = []
    inliers: list[bool] = []
    residuals: list[float] = []
    depth_rms = None
    columns = None
    if manual is not None:
        a, b = _manual_fit(manual, height)
        source = "manual"
    else:
        known = tracks or [Track(x0, x1)]
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

    track_mask = curve_mask(roi, settings)
    xs, _ = extract_curve_x_by_row(track_mask)
    images["track_mask"] = track_mask
    images["curve_overlay"] = curve_overlay(roi, xs)

    values = map_x_to_value(xs + c0, x0, x1, vmin, vmax, scale)
    depths = a * np.arange(roi.shape[0], dtype=float) + b
    found = np.isfinite(values)
    if found.sum() < 2:
        raise DigitizeError(
            "The curve was found in fewer than two rows of the track.", images
        )
    raw_depth, raw_value = depths[found], values[found]

    out_depth, out_value = resample_to_step(raw_depth, raw_value, step)
    coverage = (
        100.0 * float(np.isfinite(out_value).sum()) / len(out_value)
        if len(out_value)
        else 0.0
    )

    note = f"Digitized with pphys.digitize from {path.name}, page {page}. Depth " + (
        "from manual calibration."
        if source == "manual"
        else f"from {sum(inliers)} OCR depth labels (linear fit)."
    )
    las = _build_las(
        out_depth,
        out_value,
        curve=str(curve).strip(),
        unit=unit,
        descr=f"Digitized curve, {scale} scale {vmin:g} to {vmax:g}",
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
        track=(float(x0), float(x1)),
        track_source=track_source,
        scale=scale,
        depth_source=source,
        depth_fit=(float(a), float(b)),
        grid=grid,
        curve_clusters=[(c.x0, c.x1) for c in sorted(clusters, key=lambda c: c.x0)],
        depth_labels=[(lb.row, lb.depth) for lb in labels],
        depth_inliers=inliers,
        depth_residuals=residuals,
        depth_rms=depth_rms,
        label_columns=columns,
        coverage=coverage,
        warnings=warnings,
    )
    return DigitizeResult(las, qc, settings, images, raw_depth, raw_value)


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


def curve_mask(bgr: np.ndarray, settings: Settings | None = None) -> np.ndarray:
    """Mask (0 or 255) of the pixels in the curve colour of ``settings``."""
    settings = Settings() if settings is None else settings
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in settings.hue_bands:
        lower = np.array([lo, settings.min_saturation, settings.min_value])
        upper = np.array([hi, 255, 255])
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (settings.mask_kernel, settings.mask_kernel)
    )
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)


def find_clusters(mask: np.ndarray, min_width: int = 30) -> list[Cluster]:
    """Find runs of columns with many curve pixels, left to right."""
    col = mask.sum(axis=0) / 255.0
    # Threshold based on percentiles, to adapt to the page.
    thr = np.percentile(col, 95) * 0.3
    thr = max(thr, np.percentile(col, 90) * 0.5)
    on = col > thr

    clusters: list[Cluster] = []
    start = None
    for i, val in enumerate(on):
        if val and start is None:
            start = i
        elif not val and start is not None:
            if i - start >= min_width:
                clusters.append(Cluster(start, i - 1, float(col[start:i].sum())))
            start = None
    if start is not None and len(on) - start >= min_width:
        clusters.append(Cluster(start, len(on) - 1, float(col[start:].sum())))

    clusters.sort(key=lambda c: (c.x0, -(c.x1 - c.x0)))
    return clusters


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
) -> list[Track]:
    """Tracks found from their frame lines, left to right.

    The darkest long vertical lines are frames, the lighter ones grid lines
    (``Settings.frame_tolerance``). The span between two neighbouring frames
    is a track when it holds grid lines, pixels of ``curve`` (the curve
    mask), or horizontal grid lines running across it; so the depth column
    and margins are skipped and tracks sharing a frame are told apart. When
    all lines are equally dark, a track is a run of lines whose gaps are all
    crossed by horizontal grid lines.
    """
    settings = Settings() if settings is None else settings
    gray, paper, ink = _line_ink(page_bgr, settings, curve)
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
        has_curve = curve is not None and curve[:, inner].any()
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


def extract_curve_x_by_row(curve_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """For each row, the median column of the curve pixels and their count (NaN, 0 if none)."""
    height = curve_mask.shape[0]
    xs = np.full(height, np.nan, dtype=float)
    conf = np.zeros(height, dtype=float)
    for y in range(height):
        cols = np.flatnonzero(curve_mask[y, :])
        if cols.size:
            xs[y] = float(np.median(cols))
            conf[y] = float(cols.size)
    return xs, conf


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


def resample_to_step(
    depth: np.ndarray, value: np.ndarray, step: float
) -> tuple[np.ndarray, np.ndarray]:
    """Resample to a regular depth step by linear interpolation.

    Gaps between the rows that hold the curve are interpolated across.
    """
    order = np.argsort(depth)
    depth = depth[order]
    value = value[order]

    d_new = np.arange(
        float(np.nanmin(depth)), float(np.nanmax(depth)) + 0.5 * step, step
    )
    valid = np.isfinite(depth) & np.isfinite(value)
    if valid.sum() < 2:
        return d_new, np.full_like(d_new, np.nan, dtype=float)
    return d_new, np.interp(d_new, depth[valid], value[valid])


def curve_overlay(roi_bgr: np.ndarray, xs: np.ndarray) -> np.ndarray:
    """The track with the column read in each row marked in cyan."""
    overlay = roi_bgr.copy()
    for y, x in enumerate(xs):
        if np.isfinite(x):
            cv2.circle(overlay, (int(x), y), 1, (255, 255, 0), -1)
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
        int(np.count_nonzero(curve[:, math.ceil(t.x0) : math.floor(t.x1) + 1]))
        for t in tracks
    ]
    order = np.argsort(counts)[::-1]
    best = int(order[0])
    if counts[best] == 0:
        raise DigitizeError(
            f"None of the {len(tracks)} track(s) found holds the curve colour; "
            "check Settings.hue_bands, or pass track_edges."
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


def _build_las(
    depth, value, *, curve, unit, descr, depth_unit, well, null_value, note
) -> WellLog:
    las = WellLog()
    las.well["WELL"].value = well
    las.well["NULL"].value = null_value
    las.append_curve("DEPT", depth, unit=DEPTH_UNITS[depth_unit], descr="Depth")
    las.append_curve(curve, value, unit=unit, descr=descr)
    las.other = note
    return las


def _write_image(path: Path, image: np.ndarray) -> None:
    # cv2.imwrite cannot write to non-ASCII paths on Windows.
    ok, buffer = cv2.imencode(".png", image)
    if not ok:
        raise DigitizeError(f"Could not encode {path.name}.")
    path.write_bytes(buffer.tobytes())
