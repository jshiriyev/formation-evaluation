"""Well-log container built on :class:`lasio.LASFile`."""

from __future__ import annotations

from copy import deepcopy

import lasio
import numpy as np
import numpy.typing as npt
import pandas as pd


class WellLog(lasio.LASFile):
    """A LAS file with depth-interval selection, resampling and cropped copies.

    The first curve is the depth index (``self.index``). Construct it like
    :class:`lasio.LASFile`: ``WellLog("well.las")`` reads a file and
    ``WellLog()`` creates an empty log.
    """

    def mask(self, dmin: float | None = None, dmax: float | None = None) -> np.ndarray:
        """Return a boolean array selecting the depths within ``[dmin, dmax]``.

        Parameters
        ----------
        dmin, dmax : float, optional
            Inclusive interval bounds. A missing bound leaves that side open.

        Returns
        -------
        numpy.ndarray
            Boolean array aligned with ``self.index``.
        """
        mask = np.ones(self.index.shape, dtype=bool)

        if dmin is not None:
            mask &= self.index >= dmin
        if dmax is not None:
            mask &= self.index <= dmax

        return mask

    def crop(
        self,
        dmin: float | None = None,
        dmax: float | None = None,
        key: str | None = None,
    ) -> pd.DataFrame | np.ndarray:
        """Return the data within ``[dmin, dmax]``.

        Parameters
        ----------
        dmin, dmax : float, optional
            Inclusive interval bounds. A missing bound leaves that side open.
        key : str, optional
            Curve mnemonic. If given, only that curve's values are returned.

        Returns
        -------
        pandas.DataFrame or numpy.ndarray
            Depth-indexed frame of all curves, or the values of ``key``.
        """
        mask = self.mask(dmin, dmax)

        if key is None:
            return self.df()[mask]

        return self[key][mask]

    def resample(
        self, depths: npt.ArrayLike, key: str | None = None
    ) -> pd.DataFrame | np.ndarray:
        """Linearly interpolate curve values at new depths.

        Depths outside the logged interval return NaN instead of the edge
        value. A NaN sample makes the interpolated values next to it NaN, so
        gaps in the log are not bridged. Descending depth indexes are handled.

        Parameters
        ----------
        depths : array_like
            Depths to interpolate at, in the unit of the depth index.
        key : str, optional
            Curve mnemonic. If given, only that curve is resampled.

        Returns
        -------
        pandas.DataFrame or numpy.ndarray
            Frame of all curves indexed by ``depths``, or the values of ``key``.
        """
        depths = np.asarray(depths, dtype=float)

        order = np.argsort(self.index)  # np.interp needs increasing depths
        xp = self.index[order]

        def interp(values: np.ndarray) -> np.ndarray:
            fp = np.asarray(values, dtype=float)[order]
            return np.interp(depths, xp, fp, left=np.nan, right=np.nan)

        if key is not None:
            return interp(self[key])

        index = pd.Index(depths, name=self.curves[0].mnemonic)
        curves = {curve.mnemonic: interp(curve.data) for curve in self.curves[1:]}

        return pd.DataFrame(curves, index=index)

    def copy(self, dmin: float | None = None, dmax: float | None = None) -> WellLog:
        """Return an independent copy, optionally cropped to ``[dmin, dmax]``.

        All header sections are kept. When cropping, STRT and STOP in ~Well
        are set to the first and last depth of the window.

        Parameters
        ----------
        dmin, dmax : float, optional
            Inclusive interval bounds. A missing bound leaves that side open.

        Returns
        -------
        WellLog
            The copied (and cropped) log.

        Raises
        ------
        ValueError
            If no depth falls within ``[dmin, dmax]``.
        """
        log = deepcopy(self)

        if dmin is None and dmax is None:
            return log

        mask = self.mask(dmin, dmax)

        if not mask.any():
            raise ValueError(f"No depths between {dmin} and {dmax}.")

        for curve in log.curves:
            curve.data = curve.data[mask]

        log.update_start_stop_step(
            STRT=float(log.index[0]),
            STOP=float(log.index[-1]),
            STEP=log.well["STEP"].value if "STEP" in log.well else None,
        )

        return log

    @staticmethod
    def is_valid(values: npt.ArrayLike) -> bool:
        """Return True if ``values`` contains no NaN."""
        return not np.isnan(values).any()

    @staticmethod
    def is_positive(values: npt.ArrayLike) -> bool:
        """Return True if every value is non-negative (NaN counts as False)."""
        return bool(np.all(np.asarray(values) >= 0))

    @staticmethod
    def is_sorted(values: npt.ArrayLike) -> bool:
        """Return True if ``values`` is strictly increasing."""
        values = np.asarray(values)
        return bool(np.all(values[:-1] < values[1:]))
