"""Rounding at the first significant digit, for tidy axis limits.

>>> decimals(0.000532)
4
>>> floor(0.000532), ceil(0.000532)
(0.0005, 0.0006)
>>> floor(1312.0), ceil(1312.0), ceil(1312.0, -2)
(1000.0, 2000.0, 1400.0)

To round to the nearest value at the first significant digit, use the
built-in ``round(x, decimals(x))``.
"""

import math
from collections.abc import Callable

# Decimal places kept when removing floating-point noise from a scaled
# value: 0.29 * 100 is 28.999999999999996, which would floor to 28.
_NOISE_DECIMALS = 9


def decimals(x: float) -> int:
	"""Return the decimal places that reach the first significant digit of x.

	``abs(x) * 10**decimals(x)`` lies in [1, 10), so the result is positive
	below 1 and negative from 10 up: 4 for 0.000532 and -3 for 1312. Zero
	and non-finite values give 0, which leaves them unchanged when rounding.
	"""
	if x == 0 or not math.isfinite(x):
		return 0

	return -math.floor(math.log10(abs(x)))


def ceil(x: float, ndigits: int | None = None) -> float:
	"""Round x up at its first significant digit, or at ndigits decimal places.

	ndigits counts decimal places as in ``round``: 2 keeps hundredths and -2
	keeps hundreds. By default it is ``decimals(x)``, so 0.000532 becomes
	0.0006 and 1312 becomes 2000.
	"""
	return _snap(math.ceil, x, ndigits)


def floor(x: float, ndigits: int | None = None) -> float:
	"""Round x down at its first significant digit, or at ndigits decimal places.

	ndigits counts decimal places as in ``round``: 2 keeps hundredths and -2
	keeps hundreds. By default it is ``decimals(x)``, so 0.000532 becomes
	0.0005 and 1312 becomes 1000.
	"""
	return _snap(math.floor, x, ndigits)


def _snap(function: Callable[[float], int], x: float, ndigits: int | None) -> float:
	"""Apply math.ceil or math.floor to x at ndigits decimal places."""
	if not math.isfinite(x):
		return float(x)

	if ndigits is None:
		ndigits = decimals(x)

	# Scale by an exact power of ten, multiplying or dividing so that it
	# stays an integer: 10**-3 has no exact float.
	scale = 10.0**abs(int(ndigits))

	if ndigits >= 0:
		return function(round(x * scale, _NOISE_DECIMALS)) / scale

	return float(function(round(x / scale, _NOISE_DECIMALS)) * scale)
