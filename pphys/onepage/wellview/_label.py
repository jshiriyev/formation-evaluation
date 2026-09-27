"""The header rows that list the curves of each track."""

from dataclasses import dataclass

SPOTS = ("top", "bottom", None)


@dataclass(frozen=True)
class LabelDict:
	"""The header above (or below) the tracks, one row per curve.

	limit 	: vertical range of the header axes. Defaults to
			(0, ncycle*major), one row per cycle, set by the Layout.

	major 	: height of one row, in the units of limit.

	spot 	: where the header goes: 'top', 'bottom', or None for no header.

	"""
	limit	: tuple[float, float] | None = None

	major 	: float = 10.

	spot 	: str | None = "top"

	def __post_init__(self):

		if self.spot not in SPOTS:
			raise ValueError(f"spot must be one of {SPOTS}, not {self.spot!r}.")

		if self.major<=0:
			raise ValueError("major must be positive.")

		if self.limit is not None:
			object.__setattr__(self,'limit',tuple(sorted(float(value) for value in self.limit)))
