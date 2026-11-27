"""Scanned log (PDF) to LAS.

>>> from pphys.digitize import digitize
>>> result = digitize("scan.pdf", curve="GR", vmin=0, vmax=150, unit="gAPI",
...                   depth=(1500, 1600))                      # doctest: +SKIP
>>> result.las        # pphys.WellLog                           # doctest: +SKIP
>>> result.save("out")                                           # doctest: +SKIP

From the command line: ``pphys-digitize scan.pdf --curve GR --vmin 0 --vmax 150``
(or ``python -m pphys.digitize``). Needs the ``digitize`` extra, and the
Tesseract program to read depth labels.
"""

from ._digitize import (
    QC,
    DepthCalibrationError,
    DigitizeError,
    DigitizeResult,
    Settings,
    digitize,
    find_tesseract,
)

__all__ = [
    "QC",
    "DepthCalibrationError",
    "DigitizeError",
    "DigitizeResult",
    "Settings",
    "digitize",
    "find_tesseract",
]
