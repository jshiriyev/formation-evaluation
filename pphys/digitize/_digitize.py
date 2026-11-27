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
        Column clusters narrower than this are not tracks.
    track_margin : int
        Columns added on both sides of the curve when no ``track_edges`` are
        given to :func:`digitize`.
    depth_strip_half_width : int
        Half width of the strip, centred between the first and last track,
        that holds the depth labels.
    label_skip : float
        Left fraction of the depth strip that OCR ignores (the labels sit on
        its right).
    ocr_chunk_height, ocr_chunk_overlap : int
        The depth strip is read in chunks of this height and overlap.
    ocr_target_height : int
        Each chunk is shrunk to this height before OCR.
    ocr_min_confidence : float
        Tesseract confidence (0-100) below which a label is ignored.
    fit_tolerance : float
        Smallest residual, in depth units, that the depth fit treats as an
        outlier.
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
    track_margin: int = 60
    depth_strip_half_width: int = 120
    label_skip: float = 0.25
    ocr_chunk_height: int = 4000
    ocr_chunk_overlap: int = 300
    ocr_target_height: int = 1400
    ocr_min_confidence: float = 35.0
    fit_tolerance: float = 5.0
    null_value: float = -999.25
    tesseract: str | None = None

    def __post_init__(self):
        positive = (
            "render_scale",
            "mask_kernel",
            "min_track_width",
            "depth_strip_half_width",
            "ocr_chunk_height",
            "ocr_target_height",
            "fit_tolerance",
        )
        for name in positive:
            if not getattr(self, name) > 0:
                raise ValueError(
                    f"{name} must be positive, not {getattr(self, name)!r}."
                )
        if self.track_margin < 0:
            raise ValueError(
                f"track_margin cannot be negative, not {self.track_margin!r}."
            )
        if not 0 <= self.ocr_chunk_overlap < self.ocr_chunk_height:
            raise ValueError(
                "ocr_chunk_overlap must be at least 0 and less than ocr_chunk_height."
            )
        if not 0 <= self.label_skip < 1:
            raise ValueError(f"label_skip must be in [0, 1), not {self.label_skip!r}.")
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
    """A run of columns with many curve pixels: a track candidate."""

    x0: int
    x1: int
    score: float


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
    tracks : list of (int, int)
        Column ranges of every track candidate found, left to right.
    track : (int, int)
        First and last column of the strip the curve was read from; its
        width spans ``[vmin, vmax]``.
    depth_source : str
        "manual" (depths given) or "ocr" (depth labels read).
    depth_fit : (float, float)
        ``(a, b)`` of ``depth = a * row + b``.
    depth_labels : list of (float, float)
        ``(row, depth)`` of the labels read by OCR (empty for manual depths).
    depth_strip : (int, int) or None
        Column range of the strip the labels were read from.
    coverage : float
        Percent of the resampled depths that have a value.
    warnings : list of str
        Things to check before trusting the result.
    """

    scan: str
    page: int
    page_size: tuple[int, int]
    tracks: list[tuple[int, int]]
    track: tuple[int, int]
    depth_source: str
    depth_fit: tuple[float, float]
    depth_labels: list[tuple[float, float]] = field(default_factory=list)
    depth_strip: tuple[int, int] | None = None
    coverage: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """A few lines for the console."""
        a, b = self.depth_fit
        lines = [
            f"scan: {self.scan} (page {self.page}, {self.page_size[0]} x {self.page_size[1]} px)",
            f"track: columns {self.track[0]}-{self.track[1]} ({len(self.tracks)} track(s) found)",
            f"depth: {self.depth_source}, depth = {a:.6g} * row + {b:.6g}",
        ]
        if self.depth_source == "ocr":
            lines.append(f"depth labels read: {len(self.depth_labels)}")
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
        "curve_overlay", and for OCR "depth_strip" and "depth_labels".
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
    depth: Sequence[float] | Sequence[tuple[float, float]] | None = None,
    depth_unit: str = "m",
    step: float | None = None,
    page: int = 0,
    track: str | int = "left",
    track_edges: tuple[float, float] | None = None,
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
        Values at the left and right edge of the track.
    unit : str
        Unit of the curve, e.g. "gAPI".
    depth : (top, base) or sequence of (row, depth), optional
        Manual depth calibration, which skips OCR. ``(top, base)`` are the
        depths at the first and last row of the rendered page; two or more
        ``(row, depth)`` pairs (rows of the rendered page, see the "page" QC
        image) are fitted with a straight line. Without it, the depth labels
        between the first and last track are read with Tesseract.
    depth_unit : {"m", "ft"}
        Unit of the depths.
    step : float, optional
        Depth step of the output; 0.1524 (m) or 0.5 (ft) by default.
    page : int
        Page of the PDF to digitize, 0-based.
    track : "left", "right" or int
        Which track to read the curve from: the first or last one found, or
        its index from the left.
    track_edges : (float, float), optional
        Columns of the rendered page at the track's left and right edges,
        where the values are ``vmin`` and ``vmax``. Without it, the scale
        spans the curve's own columns plus ``Settings.track_margin``, which
        is only approximate.
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
        If depth cannot be calibrated: too few labels read, or OCR is
        needed but only one track was found.
    DigitizeError
        If no curve is found, the track does not exist, or Tesseract is
        needed but missing.
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
    chosen = _pick_track(clusters, track)
    warnings: list[str] = []

    # The strip the curve is read from; its width spans [vmin, vmax].
    if track_edges is not None:
        x0, x1 = sorted(int(round(float(v))) for v in track_edges)
        if x0 < 0 or x1 >= width or x1 - x0 < 2:
            raise ValueError(
                f"track_edges {tuple(track_edges)} must be two columns within the page (0-{width - 1})."
            )
        roi = page_bgr[:, x0 : x1 + 1].copy()
    else:
        roi, (x0, _, x1, _) = crop_with_margin(
            page_bgr, chosen.x0, chosen.x1, 0, height - 1, settings.track_margin
        )
        warnings.append(
            "Values are scaled across the curve's own columns plus a margin, not "
            "across the track edges, so they are approximate; pass "
            "track_edges=(left, right) in page columns for exact values."
        )
    images["track"] = roi

    labels: list[tuple[float, float]] = []
    strip_columns = None
    if manual is not None:
        a, b = _manual_fit(manual, height)
        source = "manual"
    else:
        ordered = sorted(clusters, key=lambda c: c.x0)
        if len(ordered) < 2:
            raise DepthCalibrationError(
                "Reading the depth labels needs two tracks (the labels sit between "
                "them), but only one was found; pass depth=(top, base) instead.",
                images,
            )
        strip, (sx0, _, sx1, _) = build_depth_strip_roi(
            page_bgr, ordered[0], ordered[-1], settings.depth_strip_half_width
        )
        strip_columns = (sx0, sx1)
        images["depth_strip"] = strip
        labels = ocr_depth_points(strip, settings)
        fit = fit_depth_transform(labels, settings.fit_tolerance)
        images["depth_labels"] = depth_labels_overlay(strip, labels, fit)
        if fit is None:
            raise DepthCalibrationError(
                f"Read {len(labels)} usable depth label(s); at least two are needed "
                "to calibrate depth. Check the 'depth_labels' image in the error's "
                "images, or pass depth=(top, base) instead.",
                images,
            )
        a, b = fit
        source = "ocr"
        if len(labels) < 4:
            warnings.append(
                f"Depth is calibrated from only {len(labels)} labels; check the "
                "depth_labels QC image."
            )

    track_mask = curve_mask(roi, settings)
    xs, _ = extract_curve_x_by_row(track_mask)
    images["track_mask"] = track_mask
    images["curve_overlay"] = curve_overlay(roi, xs)

    values = map_x_to_value(xs, 0.0, float(roi.shape[1] - 1), vmin, vmax)
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
        else f"from {len(labels)} OCR depth labels (linear fit)."
    )
    las = _build_las(
        out_depth,
        out_value,
        curve=str(curve).strip(),
        unit=unit,
        depth_unit=depth_unit,
        well=path.stem if well is None else well,
        null_value=settings.null_value,
        note=note,
    )
    qc = QC(
        scan=str(path),
        page=page,
        page_size=(width, height),
        tracks=[(c.x0, c.x1) for c in sorted(clusters, key=lambda c: c.x0)],
        track=(int(x0), int(x1)),
        depth_source=source,
        depth_fit=(float(a), float(b)),
        depth_labels=labels,
        depth_strip=strip_columns,
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


def crop_with_margin(
    img: np.ndarray, x0: int, x1: int, y0: int, y1: int, margin: int = 40
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Crop columns ``x0-x1`` widened by ``margin`` and rows ``y0-y1``, within the image."""
    height, width = img.shape[:2]
    x0m = max(0, x0 - margin)
    x1m = min(width - 1, x1 + margin)
    y0m = max(0, y0)
    y1m = min(height - 1, y1)
    roi = img[y0m : y1m + 1, x0m : x1m + 1].copy()
    return roi, (x0m, y0m, x1m, y1m)


def build_depth_strip_roi(
    img: np.ndarray, left: Cluster, right: Cluster, half_width: int = 110
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """The full-height strip centred between two tracks, where the depth labels are."""
    height, width = img.shape[:2]
    x_center = int((left.x1 + right.x0) / 2)
    x0 = max(0, x_center - half_width)
    x1 = min(width - 1, x_center + half_width)
    roi = img[:, x0 : x1 + 1].copy()
    return roi, (x0, 0, x1, height - 1)


def ocr_depth_points(
    depth_strip_bgr: np.ndarray, settings: Settings | None = None
) -> list[tuple[float, float]]:
    """Read the depth labels of a strip: ``(row, depth)`` pairs, top to bottom.

    The tall strip is read in overlapping chunks. CLAHE, a black-hat filter
    and an Otsu threshold bring out the digits; Tesseract reads each chunk
    once, and whole-number tokens are kept. A value read several times gets
    its median row, and values that would make depth decrease downward are
    dropped.
    """
    settings = Settings() if settings is None else settings
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = find_tesseract(settings.tesseract)

    gray_full = cv2.cvtColor(depth_strip_bgr, cv2.COLOR_BGR2GRAY)
    gray_full = gray_full[:, int(gray_full.shape[1] * settings.label_skip) :]
    height = gray_full.shape[0]
    config = "--psm 6 -c tessedit_char_whitelist=0123456789"

    pts: list[tuple[float, float]] = []
    y0 = 0
    while y0 < height:
        y1 = min(height, y0 + settings.ocr_chunk_height)
        chunk = gray_full[y0:y1, :]

        scale = settings.ocr_target_height / max(1, chunk.shape[0])
        if scale < 1.0:
            chunk_s = cv2.resize(
                chunk, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
            )
        else:
            chunk_s = chunk
            scale = 1.0

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        c = clahe.apply(chunk_s)
        bh = cv2.morphologyEx(
            c, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        )
        _, bw = cv2.threshold(bh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        inv = 255 - bw  # black text on white

        data = pytesseract.image_to_data(
            inv, output_type=pytesseract.Output.DICT, config=config
        )
        for i in range(len(data.get("text", []))):
            txt = re.sub(r"\s+", "", data["text"][i] or "")
            if not re.fullmatch(r"\d{2,6}", txt):
                continue
            conf = float(data["conf"][i]) if data["conf"][i] != "-1" else -1.0
            if conf < settings.ocr_min_confidence:
                continue
            y_center_small = data["top"][i] + data["height"][i] / 2.0
            pts.append((float(y0 + y_center_small / scale), float(txt)))

        if y1 >= height:
            break
        y0 = y1 - settings.ocr_chunk_overlap

    # One row per depth value: the median of its readings.
    by_depth: dict[float, list[float]] = {}
    for y, d in pts:
        by_depth.setdefault(d, []).append(y)
    merged = sorted(
        ((float(np.median(ys)), d) for d, ys in by_depth.items()), key=lambda t: t[0]
    )

    # Keep depth increasing downward.
    filtered: list[tuple[float, float]] = []
    last_d = None
    for y, d in merged:
        if last_d is None or d >= last_d:
            filtered.append((y, d))
            last_d = d
    return filtered


def fit_depth_transform(
    points: Sequence[tuple[float, float]], tolerance: float = 5.0
) -> tuple[float, float] | None:
    """Fit ``depth = a * row + b`` to ``(row, depth)`` points, dropping outliers.

    Three rounds of fitting drop points whose residual exceeds
    ``max(tolerance, 3 * median residual)``. Returns ``(a, b)``, or None
    with fewer than two points left.
    """
    if len(points) < 2:
        return None
    y = np.array([p[0] for p in points], dtype=float)
    d = np.array([p[1] for p in points], dtype=float)

    keep = np.ones_like(y, dtype=bool)
    for _ in range(3):
        if keep.sum() < 2:
            break
        a, b = np.polyfit(y[keep], d[keep], 1)
        resid = np.abs(a * y + b - d)
        tol = max(tolerance, 3.0 * np.median(resid[keep]))
        keep = resid < tol

    if keep.sum() < 2:
        return None
    a, b = np.polyfit(y[keep], d[keep], 1)
    return float(a), float(b)


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
    x_px: np.ndarray, x_left: float, x_right: float, vmin: float, vmax: float
) -> np.ndarray:
    """Map columns linearly so that ``x_left`` -> ``vmin`` and ``x_right`` -> ``vmax``."""
    return vmin + (x_px - x_left) / (x_right - x_left) * (vmax - vmin)


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
    depth_strip_bgr: np.ndarray,
    points: Sequence[tuple[float, float]],
    fit: tuple[float, float] | None,
) -> np.ndarray:
    """The depth strip with the labels read and the fitted top/base depths."""
    overlay = depth_strip_bgr.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    for y, d in points:
        cv2.circle(overlay, (10, int(y)), 3, (0, 255, 0), -1)
        cv2.putText(overlay, str(int(d)), (20, int(y)), font, 0.6, (0, 255, 0), 2)
    if fit is not None:
        a, b = fit
        bottom = a * (overlay.shape[0] - 1) + b
        cv2.putText(
            overlay, f"fit: d={a:.5f}*y+{b:.2f}", (5, 30), font, 0.7, (255, 0, 0), 2
        )
        cv2.putText(
            overlay,
            f"top~{b:.1f}  bottom~{bottom:.1f}",
            (5, 60),
            font,
            0.7,
            (255, 0, 0),
            2,
        )
    return overlay


def _pick_track(clusters: list[Cluster], track: str | int) -> Cluster:
    ordered = sorted(clusters, key=lambda c: c.x0)
    if track == "left":
        return ordered[0]
    if track == "right":
        return ordered[-1]
    if isinstance(track, (int, np.integer)) and not isinstance(track, bool):
        if 0 <= track < len(ordered):
            return ordered[track]
        raise DigitizeError(
            f"track {track} does not exist: {len(ordered)} track(s) were found."
        )
    raise ValueError(f"track must be 'left', 'right' or an index, not {track!r}.")


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
    depth, value, *, curve, unit, depth_unit, well, null_value, note
) -> WellLog:
    las = WellLog()
    las.well["WELL"].value = well
    las.well["NULL"].value = null_value
    las.append_curve("DEPT", depth, unit=DEPTH_UNITS[depth_unit], descr="Depth")
    las.append_curve(curve, value, unit=unit, descr="Digitized curve")
    las.other = note
    return las


def _write_image(path: Path, image: np.ndarray) -> None:
    # cv2.imwrite cannot write to non-ASCII paths on Windows.
    ok, buffer = cv2.imencode(".png", image)
    if not ok:
        raise DigitizeError(f"Could not encode {path.name}.")
    path.write_bytes(buffer.tobytes())
