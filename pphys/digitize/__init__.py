"""Scanned log (PDF) to LAS.

>>> from pphys.digitize import digitize
>>> result = digitize("scan.pdf", curve="GR", vmin=0, vmax=150, unit="gAPI",
...                   depth=(1500, 1600))                      # doctest: +SKIP
>>> result.las        # pphys.WellLog                           # doctest: +SKIP
>>> result.save("out")                                           # doctest: +SKIP

Several curves at once, each with its colour, scale and track:

>>> from pphys.digitize import Curve
>>> result = digitize("scan.pdf", depth=(1500, 1600), curves=[
...     Curve("GR", 0, 150, unit="gAPI", color="red"),
...     Curve("RT", 0.2, 2000, scale="log10", color="black", track=1),
... ])                                                           # doctest: +SKIP

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
    Settings,
    digitize,
    find_tesseract,
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
    "Score",
    "Settings",
    "SyntheticCurve",
    "SyntheticScan",
    "SyntheticTrack",
    "digitize",
    "find_tesseract",
    "score",
    "synthetic_scan",
]
