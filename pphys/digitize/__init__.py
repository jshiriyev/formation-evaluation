"""Scanned log (PDF or image, one page or several) to LAS.

>>> from pphys.digitize import digitize
>>> result = digitize("scan.pdf", curve="GR", vmin=0, vmax=150, unit="gAPI",
...                   depth=(1500, 1600))                      # doctest: +SKIP
>>> result.las        # pphys.WellLog                           # doctest: +SKIP
>>> result.save("out")    # LAS, CSV, qc.png, QC images, qc.json  # doctest: +SKIP
>>> fig = result.plot_qc() # scan + trace | depth-fit residuals | curves  # doctest: +SKIP

Several curves at once, each with its colour, scale and track:

>>> from pphys.digitize import Curve
>>> result = digitize("scan.pdf", depth=(1500, 1600), curves=[
...     Curve("GR", 0, 150, unit="gAPI", color="red"),
...     Curve("RT", 0.2, 2000, scale="log10", color="black", track=1),
... ])                                                           # doctest: +SKIP

Images and several pages, stitched by depth (OCR on each page, or one
``depth`` entry per page):

>>> result = digitize("scan.tif", pages="all", curve="GR", vmin=0, vmax=150,
...                   depth=[(1500, 1600), (1600, 1700)])        # doctest: +SKIP
>>> result = digitize(["top.png", "bottom.jpg"], dpi=300,
...                   curve="GR", vmin=0, vmax=150)              # doctest: +SKIP

From the command line: ``pphys-digitize scan.pdf --curve GR --vmin 0 --vmax 150``
(or ``python -m pphys.digitize``). Needs the ``digitize`` extra, and the
Tesseract program to read depth labels.

Synthetic pages of known values measure the accuracy:

>>> from pphys.digitize import digitize, score, synthetic_scan
>>> page = synthetic_scan("page.pdf")                            # doctest: +SKIP
>>> result = digitize("page.pdf", curve="GR", vmin=0, vmax=150,
...                   track_edges=page.track_edges("GR"),
...                   depth=page.depth_pairs())                  # doctest: +SKIP
>>> print(score(result, page))                                   # doctest: +SKIP

``python -m pphys.digitize.scorecard`` scores every scenario of
:mod:`pphys.digitize.scorecard` against :data:`TARGET`.
"""

from ._digitize import (
    QC,
    Curve,
    CurveQC,
    DepthCalibrationError,
    DigitizeError,
    DigitizeResult,
    PageQC,
    Settings,
    digitize,
    find_tesseract,
    load_pages,
)
from ._synthetic import (
    TARGET,
    Defects,
    Score,
    SyntheticCurve,
    SyntheticScan,
    SyntheticTrack,
    score,
    synthetic_scan,
    write_pages,
)

__all__ = [
    "QC",
    "Curve",
    "CurveQC",
    "TARGET",
    "Defects",
    "DepthCalibrationError",
    "DigitizeError",
    "DigitizeResult",
    "PageQC",
    "Score",
    "Settings",
    "SyntheticCurve",
    "SyntheticScan",
    "SyntheticTrack",
    "digitize",
    "find_tesseract",
    "load_pages",
    "score",
    "synthetic_scan",
    "write_pages",
]
