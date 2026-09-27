"""Geothermal temperature model and temperature corrections."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

FT_TO_M = 0.3048  # exact

# Default surface temperature and geothermal gradient per unit system. The
# field values are the metric ones converted (20 degC = 68 degF and
# 0.024 degC/m = 0.024 * 1.8 * 0.3048 degF/ft), so both systems agree.
_DEFAULTS = {
    "metric": (20.0, 0.024),
    "field": (68.0, 0.024 * 1.8 * FT_TO_M),
}

# Accepted depth-unit spellings (case-insensitive) and their unit system.
# "m" and "ft" match lasio's normalized ``LASFile.index_unit``.
_DEPTH_UNITS = {
    **dict.fromkeys(("m", "meter", "meters", "metre", "metres"), "metric"),
    **dict.fromkeys(("ft", "f", "foot", "feet"), "field"),
}


@dataclass(frozen=True)
class Temperature:
    """Linear geothermal model: T = surface + gradient * (depth - surface_depth).

    Parameters
    ----------
    unit_system : {"field", "metric"}, default "field"
        "field" works in feet and degF, "metric" in metres and degC. The
        other parameters and the returned temperatures use this system.
    surface : float, optional
        Temperature at ``surface_depth``. Defaults to 20 degC (68 degF), the
        average sea-surface temperature, which ranges from above 30 degC
        (86 degF) in the tropics to below 0 degC at high latitudes.
    gradient : float, optional
        Geothermal gradient in degF/ft or degC/m. The worldwide average
        ranges from 0.024 to 0.041 degC/m (0.013 to 0.022 degF/ft), with
        extremes outside this range. Defaults to the low end.
    surface_depth : float, default 0
        Depth at which ``surface`` applies, e.g. the mudline offshore.

    See Also
    --------
    Temperature.from_points : Build the model from two measured temperatures.
    """

    unit_system: str = "field"
    surface: float | None = None
    gradient: float | None = None
    surface_depth: float = 0.0

    def __post_init__(self) -> None:
        """Validate the unit system and fill in default values."""
        if self.unit_system not in _DEFAULTS:
            raise ValueError(
                f"unit_system must be 'field' or 'metric', not {self.unit_system!r}."
            )

        surface, gradient = _DEFAULTS[self.unit_system]

        if self.surface is None:
            object.__setattr__(self, "surface", surface)
        if self.gradient is None:
            object.__setattr__(self, "gradient", gradient)

    @classmethod
    def from_points(
        cls,
        depth1: float,
        temp1: float,
        depth2: float,
        temp2: float,
        unit_system: str = "field",
        surface_depth: float = 0.0,
    ) -> Temperature:
        """Build the model through two measured (depth, temperature) points.

        The gradient comes from :meth:`get_gradient`, and ``surface`` is that
        line extrapolated to ``surface_depth``.

        Parameters
        ----------
        depth1, temp1, depth2, temp2 : float
            The two measurements, in the units of ``unit_system``.
        unit_system : {"field", "metric"}, default "field"
            Unit system of the inputs and of the model.
        surface_depth : float, default 0
            Depth at which the model's ``surface`` temperature applies.

        Returns
        -------
        Temperature
            A model that reproduces both measurements.
        """
        gradient = cls.get_gradient(depth1, temp1, depth2, temp2)
        surface = temp1 + gradient * (surface_depth - depth1)
        return cls(unit_system, surface, gradient, surface_depth)

    def __call__(
        self, depths: npt.ArrayLike, depth_unit: str | None = None
    ) -> np.ndarray:
        """Return the temperatures at ``depths``, in degF or degC.

        Parameters
        ----------
        depths : array_like
            Depths to evaluate at.
        depth_unit : str, optional
            Unit of ``depths``: "m" or "ft" (also "meter", "metre", "feet",
            "foot", "f"; any case). Converted to the model's unit system if
            needed. Without it, depths are taken to be in the model's unit.

        Returns
        -------
        numpy.ndarray
            Temperatures in the unit of the model's ``unit_system``.
        """
        depths = np.asarray(depths, dtype=float)

        if depth_unit is not None:
            system = _depth_system(depth_unit)
            if system == "field" and self.unit_system == "metric":
                depths = depths * FT_TO_M
            elif system == "metric" and self.unit_system == "field":
                depths = depths / FT_TO_M

        return self.surface + self.gradient * (depths - self.surface_depth)

    @staticmethod
    def get_gradient(depth1: float, temp1: float, depth2: float, temp2: float) -> float:
        """Return the slope of the straight line through two (depth, temp) points.

        Raises
        ------
        ValueError
            If the two depths are equal.
        """
        if depth1 == depth2:
            raise ValueError("The two depths must differ.")
        return (temp2 - temp1) / (depth2 - depth1)

    @staticmethod
    def f_to_c(values: npt.ArrayLike) -> np.ndarray:
        """Convert temperatures from degF to degC."""
        return (np.asarray(values, dtype=float) - 32.0) * 5.0 / 9.0

    @staticmethod
    def c_to_f(values: npt.ArrayLike) -> np.ndarray:
        """Convert temperatures from degC to degF."""
        return np.asarray(values, dtype=float) * 9.0 / 5.0 + 32.0

    @classmethod
    def resistivity(
        cls,
        res1: npt.ArrayLike,
        temp1: npt.ArrayLike,
        temp2: npt.ArrayLike,
        temp_unit: str = "F",
    ) -> np.ndarray:
        """Convert a resistivity measured at ``temp1`` to ``temp2`` (Arps).

        Uses R2 = R1 * (T1 + 6.77) / (T2 + 6.77) with temperatures in degF.
        Temperatures in degC are converted first, which is the same as using
        about 21.5 as the constant.

        Parameters
        ----------
        res1 : array_like
            Resistivity at ``temp1``, e.g. Rw or Rmf in ohm.m.
        temp1, temp2 : array_like
            Temperature of the measurement and the target temperature.
        temp_unit : {"F", "C"}, default "F"
            Unit of ``temp1`` and ``temp2``.

        Returns
        -------
        numpy.ndarray
            Resistivity at ``temp2``.
        """
        unit = temp_unit.upper()

        if unit == "C":
            temp1, temp2 = cls.c_to_f(temp1), cls.c_to_f(temp2)
        elif unit != "F":
            raise ValueError(f"temp_unit must be 'F' or 'C', not {temp_unit!r}.")

        return (
            np.asarray(res1, dtype=float)
            * (np.asarray(temp1, dtype=float) + 6.77)
            / (np.asarray(temp2, dtype=float) + 6.77)
        )

    @staticmethod
    def horner(
        temps: npt.ArrayLike, delta_time: npt.ArrayLike, cooling_time: float
    ) -> float:
        """Estimate the true formation temperature from BHTs (Horner plot).

        Temperatures logged at increasing times after mud circulation stops
        approach the formation temperature. Plotting them against
        log10((cooling_time + delta_time) / delta_time) gives a straight line
        whose intercept (infinite shut-in time) is the formation temperature.

        Parameters
        ----------
        temps : array_like
            Bottom-hole temperatures at one depth from successive logging runs.
        delta_time : array_like
            Time since circulation stopped for each run.
        cooling_time : float
            How long the fluid circulated (cooled the borehole), in the same
            unit as ``delta_time``.

        Returns
        -------
        float
            Formation temperature, in the unit of ``temps``.

        Raises
        ------
        ValueError
            If there are fewer than two runs, the inputs differ in length, or
            a time is not positive.
        """
        temps = np.asarray(temps, dtype=float)
        delta_time = np.asarray(delta_time, dtype=float)

        if temps.size < 2 or temps.shape != delta_time.shape:
            raise ValueError(
                "Need at least two runs, each with a temperature and a time."
            )
        if cooling_time <= 0 or np.any(delta_time <= 0):
            raise ValueError("delta_time and cooling_time must be positive.")

        horner_time = np.log10((cooling_time + delta_time) / delta_time)
        _, intercept = np.polyfit(horner_time, temps, 1)

        return float(intercept)


def _depth_system(depth_unit: str) -> str:
    """Return the unit system ("field" or "metric") of a depth unit."""
    try:
        return _DEPTH_UNITS[depth_unit.strip().lower()]
    except KeyError:
        raise ValueError(
            f"Unknown depth unit {depth_unit!r}; use 'm' or 'ft'."
        ) from None
