"""Summaries, quality checks and quick-look plots for one LAS file."""

from __future__ import annotations

import math
import os
from collections.abc import Callable, Iterator, Mapping, Sequence
from itertools import pairwise
from pathlib import Path
from typing import Any

import lasio
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from ._families import CurveFamily, classify
from ._lasio import WellLog
from ._read import read

# ~Well items that LAS 2.0 requires, and those that identify the well.
_REQUIRED_ITEMS = ("STRT", "STOP", "STEP", "NULL")
_IDENTIFICATION_ITEMS = ("COMP", "WELL", "FLD", "LOC", "SRVC", "DATE")

# Values often used for missing data. Found in the data, they show that the
# declared NULL value does not match the one the data actually use.
_NULL_SENTINELS = (-999.25, -999.0, -9999.0, -9999.25, -99999.0)

_DEPTH_UNITS = {"M", "FT", "F", "METER", "METERS", "METRE", "METRES", "FEET", ".1IN"}

# Scales a median absolute deviation to a standard deviation (normal data).
_MAD_TO_SIGMA = 1.4826

TopsLike = Mapping[str, float] | pd.Series | pd.DataFrame


class LasView:
    """Summaries, quality checks and quick-look plots for one LAS file.

    Tables are returned as :class:`pandas.DataFrame` and plots as
    :class:`matplotlib.figure.Figure`, so both display in notebooks and can
    be saved or edited further.

    Parameters
    ----------
    source : str, path-like or lasio.LASFile
        Path of a LAS file, read with :func:`pphys.read`, or a loaded log.
    tops : mapping, Series or DataFrame, optional
        Formation tops as ``{name: depth}``, a Series of depths indexed by
        name, or a DataFrame with ``formation`` and ``depth`` columns. Depths
        are in the unit of the depth index.
    cache_path : str or path-like, optional
        Cache directory passed to :func:`pphys.read`.
    **read_kwargs
        Passed to :func:`pphys.read`, e.g. ``null_policy="none"``.

    Examples
    --------
    >>> view = LasView("well.las", tops={"Top A": 1520.0})
    >>> view.inventory()
    >>> fig = view.plot_coverage()
    """

    def __init__(
        self,
        source: str | os.PathLike[str] | lasio.LASFile,
        tops: TopsLike | None = None,
        *,
        cache_path: str | os.PathLike[str] | None = None,
        **read_kwargs: Any,
    ) -> None:
        if isinstance(source, lasio.LASFile):
            self.log = _as_welllog(source)
        else:
            self.log = read(source, cache_path, **read_kwargs)

        self.tops = _tops_frame(tops)

    def __repr__(self) -> str:
        return (
            f"LasView(well={self.well_name!r}, curves={len(self.curves)}, "
            f"depth={np.nanmin(self.depth):g}-{np.nanmax(self.depth):g} "
            f"{self.depth_unit})"
        )

    # ------------------------------------------------------------------
    # Basic properties

    @property
    def depth(self) -> np.ndarray:
        """Depth index (first curve) as a float array."""
        return _numeric(self.log.index)

    @property
    def depth_mnemonic(self) -> str:
        """Mnemonic of the depth index, e.g. "DEPT"."""
        return self.log.curves[0].mnemonic

    @property
    def depth_unit(self) -> str:
        """Unit of the depth index, e.g. "M" or "FT"."""
        return self.log.index_unit or self.log.curves[0].unit

    @property
    def curves(self) -> list[str]:
        """Mnemonics of all curves except the depth index."""
        return [curve.mnemonic for curve in self.log.curves[1:]]

    @property
    def well_name(self) -> str:
        """Well name from the ~Well section ("" if missing)."""
        return str(_item(self.log.well, "WELL") or "")

    @property
    def other(self) -> str:
        """Free text of the ~Other section (remarks, processing notes)."""
        return self.log.other

    def family(self, mnemonic: str) -> CurveFamily | None:
        """Return the curve family of ``mnemonic``, or None if unknown."""
        curve = self._curve(mnemonic)
        return classify(curve.mnemonic, curve.unit)

    # ------------------------------------------------------------------
    # Summary tables

    def summary(self) -> pd.Series:
        """Return an overview of the file: well, header depths and data extent."""
        well = self.log.well
        depth = self.depth
        items = {
            "well": _item(well, "WELL"),
            "field": _item(well, "FLD"),
            "company": _item(well, "COMP"),
            "service company": _item(well, "SRVC"),
            "date": _item(well, "DATE"),
            "location": _item(well, "LOC"),
            "country": _item(well, "CTRY"),
            "LAS version": _item(self.log.version, "VERS"),
            "depth curve": self.depth_mnemonic,
            "depth unit": self.depth_unit,
            "header start": _item(well, "STRT"),
            "header stop": _item(well, "STOP"),
            "header step": _item(well, "STEP"),
            "data top": float(np.nanmin(depth)),
            "data bottom": float(np.nanmax(depth)),
            "median step": self._step(),
            "samples": depth.size,
            "curves": len(self.curves),
            "null value": _item(well, "NULL"),
        }
        return pd.Series(items, name=self.well_name or "LAS file", dtype=object)

    def header(self, section: str = "well") -> pd.DataFrame:
        """Return a header section as a table.

        Parameters
        ----------
        section : {"well", "curves", "parameters", "version"}
            The LAS section to return.

        Returns
        -------
        pandas.DataFrame
            Columns ``mnemonic``, ``unit``, ``value`` and ``description``.
        """
        sections = {
            "well": self.log.well,
            "curves": self.log.curves,
            "parameters": self.log.params,
            "version": self.log.version,
        }
        try:
            items = sections[section.lower()]
        except KeyError:
            raise ValueError(
                f"section must be one of {', '.join(sections)}, not {section!r}."
            ) from None

        return pd.DataFrame(
            [
                {
                    "mnemonic": item.mnemonic,
                    "unit": item.unit,
                    "value": item.value,
                    "description": item.descr,
                }
                for item in items
            ],
            columns=["mnemonic", "unit", "value", "description"],
        )

    def inventory(self) -> pd.DataFrame:
        """Return one row per curve: what it is and where it has data.

        Returns
        -------
        pandas.DataFrame
            Indexed by curve, with ``unit``, ``description``, ``family``,
            ``top`` and ``bottom`` (first and last depth with data),
            ``samples`` (number of values), ``coverage`` (fraction of all
            depths with a value) and ``gaps`` (missing intervals between top
            and bottom). The depth index is the first row.
        """
        depth = self.depth
        rows = []

        for position, curve in enumerate(self.log.curves):
            valid = ~np.isnan(_numeric(curve.data))
            family = classify(curve.mnemonic, curve.unit)
            rows.append(
                {
                    "curve": curve.mnemonic,
                    "unit": curve.unit,
                    "description": curve.descr,
                    "family": "depth" if position == 0 else _family_name(family),
                    "top": depth[valid].min() if valid.any() else np.nan,
                    "bottom": depth[valid].max() if valid.any() else np.nan,
                    "samples": int(valid.sum()),
                    "coverage": valid.mean() if valid.size else np.nan,
                    "gaps": max(len(_runs(valid)) - 1, 0),
                }
            )

        return pd.DataFrame(rows).set_index("curve")

    def statistics(self, curves: str | Sequence[str] | None = None) -> pd.DataFrame:
        """Return descriptive statistics per curve, ignoring missing values.

        Returns
        -------
        pandas.DataFrame
            Indexed by curve, with ``unit``, ``count``, ``mean``, ``std``,
            ``min``, ``p10``, ``p50``, ``p90`` (10th, 50th and 90th
            percentiles) and ``max``.
        """
        names = self._names(curves)
        stats = (
            self._frame(names)
            .describe(percentiles=[0.1, 0.5, 0.9])
            .T.rename(columns={"10%": "p10", "50%": "p50", "90%": "p90"})
        )
        stats["count"] = stats["count"].astype(int)
        stats.insert(0, "unit", [self._curve(name).unit for name in names])
        stats.index.name = "curve"
        return stats

    def intervals(
        self, curves: str | Sequence[str] | None = None, min_gap: float = 0.0
    ) -> pd.DataFrame:
        """Return the depth intervals where each curve has continuous data.

        Parameters
        ----------
        curves : str or list of str, optional
            Curves to report; all curves by default.
        min_gap : float, default 0
            Gaps up to this thickness (depth units) are ignored, so the
            intervals on either side are reported as one.

        Returns
        -------
        pandas.DataFrame
            Columns ``curve``, ``top``, ``bottom`` and ``thickness``.
        """
        rows = [
            {"curve": name, "top": top, "bottom": bottom, "thickness": bottom - top}
            for name in self._names(curves)
            for top, bottom in self._intervals(name, min_gap)
        ]
        return pd.DataFrame(rows, columns=["curve", "top", "bottom", "thickness"])

    def gaps(
        self, curves: str | Sequence[str] | None = None, min_gap: float = 0.0
    ) -> pd.DataFrame:
        """Return missing intervals between the first and last value of each curve.

        ``top`` and ``bottom`` are the depths of the last value above and the
        first value below the gap.

        Parameters
        ----------
        curves : str or list of str, optional
            Curves to report; all curves by default.
        min_gap : float, default 0
            Only gaps thicker than this (depth units) are reported.

        Returns
        -------
        pandas.DataFrame
            Columns ``curve``, ``top``, ``bottom`` and ``thickness``.
        """
        rows = []

        for name in self._names(curves):
            runs = self._intervals(name, min_gap)
            for (_, above), (below, _) in pairwise(runs):
                rows.append(
                    {
                        "curve": name,
                        "top": above,
                        "bottom": below,
                        "thickness": below - above,
                    }
                )

        return pd.DataFrame(rows, columns=["curve", "top", "bottom", "thickness"])

    # ------------------------------------------------------------------
    # Quality control

    def quality(
        self,
        curves: str | Sequence[str] | None = None,
        *,
        spike_threshold: float = 8.0,
        flat_samples: int = 20,
    ) -> pd.DataFrame:
        """Check each curve for missing data, impossible values, spikes and flat lines.

        Parameters
        ----------
        curves : str or list of str, optional
            Curves to check; all curves by default.
        spike_threshold : float, default 8
            A sample is a spike if it jumps away from both neighbours, in the
            same direction, by more than this many times the curve's typical
            sample-to-sample change (robust standard deviation of the first
            differences). Smooth features spanning several samples are not
            spikes.
        flat_samples : int, default 20
            A run of at least this many identical values is flagged as a flat
            line (e.g. a stuck sensor).

        Returns
        -------
        pandas.DataFrame
            Indexed by curve, with ``family``, ``unit``, ``samples``,
            ``missing`` (fraction missing between the first and last value),
            ``limits`` (plausible range for the family and unit),
            ``below_min``, ``above_max``, ``spikes``, ``longest_flat`` (depth
            units) and ``flags`` summarizing the issues. Spike and flat-line
            checks are skipped (``<NA>``) for spiky or wrapping curves such
            as the casing collar locator and azimuths.
        """
        step = self._step()
        rows = []

        for name in self._names(curves):
            curve = self._curve(name)
            family = classify(curve.mnemonic, curve.unit)
            values = self._values(name)
            valid = ~np.isnan(values)

            row: dict[str, Any] = {
                "curve": name,
                "family": _family_name(family),
                "unit": curve.unit,
                "samples": int(valid.sum()),
                "missing": np.nan,
                "limits": "",
                "below_min": pd.NA,
                "above_max": pd.NA,
                "spikes": pd.NA,
                "longest_flat": np.nan,
                "flags": "",
            }
            rows.append(row)

            if not valid.any():
                row["flags"] = "empty"
                continue

            issues = []
            first, last = np.flatnonzero(valid)[[0, -1]]
            row["missing"] = 1.0 - valid[first : last + 1].mean()
            if row["missing"] > 0:
                issues.append(f"{row['missing']:.1%} missing")

            limits = family.range_for(curve.unit) if family else None
            if limits is not None:
                low, high = limits
                data = values[valid]
                row["limits"] = f"[{low:g}, {high:g}]"
                row["below_min"] = int((data < low).sum())
                row["above_max"] = int((data > high).sum())
                if row["below_min"]:
                    issues.append(f"{row['below_min']} below {low:g}")
                if row["above_max"]:
                    issues.append(f"{row['above_max']} above {high:g}")

            if family is None or family.smooth:
                row["spikes"] = _count_spikes(values, spike_threshold)
                flat = _longest_constant_run(values)
                row["longest_flat"] = max(flat - 1, 0) * step
                if row["spikes"]:
                    issues.append(f"{row['spikes']} spikes")
                if flat >= flat_samples:
                    issues.append(
                        f"constant over {row['longest_flat']:.3g} {self.depth_unit}"
                    )

            row["flags"] = "; ".join(issues) or "ok"

        frame = pd.DataFrame(rows).set_index("curve")
        return frame.astype(
            {"below_min": "Int64", "above_max": "Int64", "spikes": "Int64"}
        )

    def validate(self) -> pd.DataFrame:
        """Check the file as a whole: header, depth index and null values.

        Returns
        -------
        pandas.DataFrame
            One row per check with ``check``, ``status`` ("pass", "warn" or
            "fail") and ``detail``.
        """
        well = self.log.well
        depth = self.depth
        unit = self.depth_unit
        step = self._step()
        checks: list[tuple[str, str, str]] = []

        def check(name: str, passed: bool, detail: str, severity: str = "warn") -> None:
            checks.append((name, "pass" if passed else severity, detail))

        missing = [m for m in _REQUIRED_ITEMS if _item(well, m) is None]
        check(
            "required ~Well items",
            not missing,
            f"missing: {', '.join(missing)}" if missing else "STRT, STOP, STEP, NULL",
            severity="fail",
        )

        empty = [m for m in _IDENTIFICATION_ITEMS if _item(well, m) is None]
        if _item(well, "UWI") is None and _item(well, "API") is None:
            empty.append("UWI/API")
        check(
            "well identification",
            not empty,
            f"empty: {', '.join(empty)}" if empty else "all present",
        )

        check("depth unit", unit.strip().upper() in _DEPTH_UNITS, unit or "missing")

        steps = np.diff(depth)
        n_missing = int(np.isnan(depth).sum())
        check("depth values", n_missing == 0, f"{n_missing} missing", severity="fail")

        bad = int(min((steps <= 0).sum(), (steps >= 0).sum()))
        check(
            "depth order",
            bad == 0,
            ("increasing" if depth[-1] > depth[0] else "decreasing")
            if bad == 0
            else f"{bad} repeated or reversed depths",
            severity="fail",
        )

        irregular = int((~np.isclose(np.abs(steps), step, rtol=1e-3, atol=1e-9)).sum())
        check(
            "regular sampling",
            irregular == 0,
            f"step {step:g} {unit}"
            if irregular == 0
            else f"{irregular} of {steps.size} steps differ from {step:g} {unit}",
        )

        header_step = _as_float(_item(well, "STEP"))
        if header_step == 0:
            check(
                "header STEP",
                irregular > 0,
                "STEP = 0 declares irregular sampling"
                + ("" if irregular else ", but the data are regular"),
            )
        elif header_step is not None:
            check(
                "header STEP",
                math.isclose(abs(header_step), step, rel_tol=1e-3),
                f"header {header_step:g}, data {step:g}",
            )

        for mnemonic, actual in (("STRT", depth[0]), ("STOP", depth[-1])):
            declared = _as_float(_item(well, mnemonic))
            if declared is not None:
                check(
                    f"header {mnemonic}",
                    abs(declared - actual) <= step / 2,
                    f"header {declared:g}, data {actual:g}",
                )

        originals = [curve.original_mnemonic for curve in self.log.curves]
        duplicates = sorted({m for m in originals if originals.count(m) > 1})
        check(
            "unique mnemonics",
            not duplicates,
            f"duplicated: {', '.join(duplicates)}"
            if duplicates
            else f"{len(originals)} curves",
        )

        no_unit = [
            curve.mnemonic for curve in self.log.curves[1:] if not curve.unit.strip()
        ]
        check(
            "curve units",
            not no_unit,
            f"no unit: {', '.join(no_unit)}" if no_unit else "all curves have units",
        )

        null = _as_float(_item(well, "NULL"))
        found = []
        for name in self.curves:
            values = self._values(name)
            for sentinel in _NULL_SENTINELS:
                if null is not None and math.isclose(sentinel, null):
                    continue
                count = int(np.isclose(values, sentinel).sum())
                if count:
                    found.append(f"{name}: {count} x {sentinel:g}")
        check(
            "undeclared null values",
            not found,
            "; ".join(found)
            if found
            else f"none (NULL = {null:g})"
            if null is not None
            else "none",
        )

        empty_curves = [
            name for name in self.curves if np.isnan(self._values(name)).all()
        ]
        check("empty curves", not empty_curves, ", ".join(empty_curves) or "none")

        if not self.tops.empty:
            inside = self.tops["depth"].between(np.nanmin(depth), np.nanmax(depth))
            outside = self.tops.loc[~inside, "formation"]
            check(
                "tops within logged interval",
                outside.empty,
                f"outside: {', '.join(outside)}"
                if not outside.empty
                else f"{len(self.tops)} tops",
            )

        return pd.DataFrame(checks, columns=["check", "status", "detail"])

    # ------------------------------------------------------------------
    # Zones and depth windows

    def zones(self) -> pd.DataFrame:
        """Return the formation intervals defined by the tops.

        Each zone runs from its top to the next top; the last one ends at the
        bottom of the log.

        Returns
        -------
        pandas.DataFrame
            Columns ``formation``, ``top``, ``base`` and ``thickness``.
        """
        columns = ["formation", "top", "base", "thickness"]
        if self.tops.empty:
            return pd.DataFrame(columns=columns)

        tops = self.tops
        last_base = max(float(np.nanmax(self.depth)), float(tops["depth"].iloc[-1]))
        base = tops["depth"].shift(-1).fillna(last_base)

        return pd.DataFrame(
            {
                "formation": tops["formation"],
                "top": tops["depth"],
                "base": base,
                "thickness": base - tops["depth"],
            },
            columns=columns,
        )

    def zone_statistics(
        self,
        curves: str | Sequence[str] | None = None,
        stat: str | Callable[..., Any] = "mean",
    ) -> pd.DataFrame:
        """Return one statistic per zone and curve, e.g. zone averages.

        Parameters
        ----------
        curves : str or list of str, optional
            Curves to summarize; all curves by default.
        stat : str or callable, default "mean"
            Any pandas aggregation, e.g. "median", "min", "max", "std" or
            "count".

        Returns
        -------
        pandas.DataFrame
            Indexed by formation, one column per curve.
        """
        names = self._names(curves)
        frame = self._frame(names)
        zones = self.zones()
        rows = []

        for position, zone in enumerate(zones.itertuples(index=False)):
            is_last = position == len(zones) - 1
            above_base = (
                frame.index <= zone.base if is_last else frame.index < zone.base
            )
            inside = (frame.index >= zone.top) & above_base
            rows.append(frame[inside].agg(stat).rename(zone.formation))

        result = pd.DataFrame(rows, columns=names)
        result.index.name = "formation"
        return result

    def window(self, top: float | None = None, base: float | None = None) -> LasView:
        """Return a LasView of the log cropped to ``[top, base]``.

        The tops are kept, so zones and plots still show them.
        """
        return LasView(self.log.copy(top, base), tops=self.tops)

    # ------------------------------------------------------------------
    # Plots

    def plot_coverage(
        self,
        *,
        scale: str = "events",
        min_gap: float = 0.0,
        depth_format: str = "{:.1f}",
        ax: Axes | None = None,
    ) -> Figure:
        """Plot where each curve has data, one vertical bar per curve.

        Parameters
        ----------
        scale : {"events", "depth"}, default "events"
            "events" spaces the depths where any curve starts or stops (and
            the tops) evenly, so short offsets between tools stay readable.
            "depth" uses a true depth axis.
        min_gap : float, default 0
            Gaps up to this thickness are not drawn (see :meth:`intervals`).
        depth_format : str, default "{:.1f}"
            Format of the depth labels on the "events" axis.
        ax : matplotlib.axes.Axes, optional
            Axes to draw on; a new figure is created by default.

        Returns
        -------
        matplotlib.figure.Figure
        """
        names = [self.depth_mnemonic, *self.curves]
        runs = {name: self._intervals(name, min_gap) for name in names}
        low, high = float(np.nanmin(self.depth)), float(np.nanmax(self.depth))
        tops = self.tops[self.tops["depth"].between(low, high)]

        if scale == "events":
            boundaries = [
                depth for pairs in runs.values() for pair in pairs for depth in pair
            ]
            events = np.unique(np.round([*boundaries, *tops["depth"]], 6))

            def position(depth: float) -> float:
                return float(np.searchsorted(events, round(depth, 6)))

        elif scale == "depth":
            events = None

            def position(depth: float) -> float:
                return depth

        else:
            raise ValueError(f"scale must be 'events' or 'depth', not {scale!r}.")

        created = ax is None
        if ax is None:
            rows = len(events) if events is not None else 25
            _, ax = plt.subplots(
                figsize=(max(4.0, 0.35 * len(names) + 2.5), max(4.0, 0.3 * rows + 1.5))
            )

        for column, name in enumerate(names):
            for top, bottom in runs[name]:
                ax.vlines(
                    column,
                    position(top),
                    position(bottom),
                    color=f"C{column % 10}",
                    linewidth=1.5,
                )

        ax.set_xlim(-1, len(names))
        ax.set_xticks(range(len(names)), names, rotation=90)
        ax.xaxis.tick_top()

        if events is not None:
            ax.set_yticks(range(len(events)), [depth_format.format(d) for d in events])
            ax.set_ylim(len(events), -1)
        else:
            margin = 0.02 * (high - low)
            ax.set_ylim(high + margin, low - margin)
            ax.set_ylabel(f"Depth ({self.depth_unit})")
        ax.grid(True, axis="y", alpha=0.6)

        if not tops.empty:
            right = ax.twinx()
            right.set_ylim(ax.get_ylim())
            right.set_yticks([position(d) for d in tops["depth"]], tops["formation"])
            if events is None:
                for depth in tops["depth"]:
                    ax.axhline(depth, color="gray", linestyle="--", linewidth=0.8)

        if created:
            ax.figure.tight_layout()
        return ax.figure

    def plot_table(
        self,
        frame: pd.DataFrame | pd.Series | None = None,
        *,
        title: str | None = None,
        float_format: str = "{:.1f}",
        ax: Axes | None = None,
    ) -> Figure:
        """Draw a table as a figure, e.g. for reports.

        Parameters
        ----------
        frame : DataFrame or Series, optional
            Table to draw. By default the curve inventory with the columns
            Curves, Top, Bottom and Description. A named index is included
            as the first column.
        title : str, optional
            Title above the table.
        float_format : str, default "{:.1f}"
            Format for floating-point values.
        ax : matplotlib.axes.Axes, optional
            Axes to draw on; a new figure is created by default.

        Returns
        -------
        matplotlib.figure.Figure
        """
        if frame is None:
            frame = self.inventory().reset_index()[
                ["curve", "top", "bottom", "description"]
            ]
            frame.columns = ["Curves", "Top", "Bottom", "Description"]
        elif isinstance(frame, pd.Series):
            frame = frame.rename_axis("item").to_frame("value").reset_index()
        elif frame.index.name is not None:
            frame = frame.reset_index()

        def text(value: Any) -> str:
            if value is None or value is pd.NA:
                return ""
            if isinstance(value, float | np.floating):
                return "" if np.isnan(value) else float_format.format(value)
            return str(value)

        header = [str(column) for column in frame.columns]
        cells = [
            [text(value) for value in row] for row in frame.itertuples(index=False)
        ]
        numeric = [pd.api.types.is_numeric_dtype(dtype) for dtype in frame.dtypes]

        widths = [
            max([len(name), *(len(row[j]) for row in cells)]) + 3
            for j, name in enumerate(header)
        ]
        edges = np.concatenate([[0], np.cumsum(widths)])
        total, n_rows = float(edges[-1]), len(cells)

        created = ax is None
        if ax is None:
            _, ax = plt.subplots(
                figsize=(
                    max(4.0, 0.085 * total),
                    0.36 * (n_rows + 1) + (0.5 if title else 0.2),
                )
            )

        ax.set_axis_off()
        ax.set_xlim(0, total)
        ax.set_ylim(n_rows + 1.05, -0.05)

        for row_index, row in enumerate([header, *cells]):
            for j, value in enumerate(row):
                if numeric[j]:
                    x, align = edges[j + 1] - 1.5, "right"
                else:
                    x, align = edges[j] + 1.5, "left"
                ax.text(
                    x,
                    row_index + 0.5,
                    value,
                    ha=align,
                    va="center",
                    fontsize=9,
                    fontweight="bold" if row_index == 0 else "normal",
                )

        ax.hlines([0, n_rows + 1], 0, total, color="black", linewidth=0.8)
        ax.hlines(
            range(1, n_rows + 1), 0, total, color="gray", linewidth=0.8, linestyles=":"
        )

        if title:
            ax.set_title(title, loc="left", fontweight="bold")
        if created:
            ax.figure.tight_layout()
        return ax.figure

    def plot_logs(
        self,
        tracks: Sequence[str | Sequence[str]] | None = None,
        *,
        top: float | None = None,
        base: float | None = None,
        figsize: tuple[float, float] | None = None,
    ) -> Figure:
        """Plot curves against depth, one track per curve or group of curves.

        Resistivity-type curves use a logarithmic axis, and tops are drawn
        as dashed lines across all tracks.

        Parameters
        ----------
        tracks : list, optional
            Each item is a curve name or a list of names sharing one track,
            e.g. ``["GR", ["ATMN", "ATMX"]]``. By default every curve gets
            its own track.
        top, base : float, optional
            Depth window to plot; the whole log by default.
        figsize : (float, float), optional
            Figure size in inches.

        Returns
        -------
        matplotlib.figure.Figure
        """
        groups = self._tracks(tracks)
        mask = self.log.mask(top, base)
        depth = self.depth[mask]

        figure, axes = plt.subplots(
            1,
            len(groups),
            sharey=True,
            squeeze=False,
            figsize=figsize or (max(4.0, 1.8 * len(groups)), 10.0),
        )
        axes = axes[0]

        for ax, group in zip(axes, groups, strict=True):
            for position, name in enumerate(group):
                family = self.family(name)
                if len(group) == 1:
                    color = family.color if family is not None else "black"
                else:
                    color = f"C{position % 10}"
                ax.plot(
                    self._values(name)[mask],
                    depth,
                    color=color,
                    linewidth=0.8,
                    label=name,
                )
                if family is not None and family.log_scale:
                    ax.set_xscale("log")

            units = sorted({self._curve(name).unit for name in group})
            names = group[0] if len(group) == 1 else f"{len(group)} curves"
            ax.set_xlabel(f"{names}\n[{', '.join(units)}]", fontsize=8)
            ax.xaxis.set_label_position("top")
            ax.xaxis.tick_top()
            ax.tick_params(labelsize=7)
            ax.grid(True, alpha=0.3)
            if len(group) > 1:
                ax.legend(fontsize=6, loc="upper right", framealpha=0.8)

        if depth.size:
            axes[0].set_ylim(depth.max(), depth.min())
        axes[0].set_ylabel(f"Depth ({self.depth_unit})")

        if depth.size:
            shown = self.tops[self.tops["depth"].between(depth.min(), depth.max())]
            for formation, level in zip(
                shown["formation"], shown["depth"], strict=True
            ):
                for ax in axes:
                    ax.axhline(level, color="gray", linestyle="--", linewidth=0.8)
                axes[-1].annotate(
                    formation,
                    xy=(1.03, level),
                    xycoords=("axes fraction", "data"),
                    va="center",
                    fontsize=8,
                )

        if self.well_name:
            figure.suptitle(self.well_name)
        figure.tight_layout()
        return figure

    def plot_histograms(
        self,
        curves: str | Sequence[str] | None = None,
        *,
        bins: int = 50,
        ncols: int = 4,
    ) -> Figure:
        """Plot a histogram per curve with its P10, P50 and P90 marked.

        Resistivity-type curves use logarithmic bins. Dotted lines mark the
        10th and 90th percentiles and the dashed line the median.

        Returns
        -------
        matplotlib.figure.Figure
        """
        names = self._names(curves)
        nrows = max(1, math.ceil(len(names) / ncols))
        figure, axes = plt.subplots(
            nrows, ncols, figsize=(3.0 * ncols, 2.4 * nrows), squeeze=False
        )

        for ax, name in zip(axes.flat, names, strict=False):
            family = self.family(name)
            values = self._values(name)
            values = values[~np.isnan(values)]
            ax.set_title(self._label(name), fontsize=9)
            ax.tick_params(labelsize=7)

            edges: int | np.ndarray = bins
            if family is not None and family.log_scale:
                values = values[values > 0]
                if values.size and values.min() < values.max():
                    edges = np.geomspace(values.min(), values.max(), bins + 1)
                    ax.set_xscale("log")

            if values.size == 0:
                ax.text(
                    0.5,
                    0.5,
                    "no data",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                continue

            ax.hist(
                values, bins=edges, color=family.color if family else "C0", alpha=0.7
            )
            for value, style in zip(
                np.percentile(values, [10, 50, 90]), (":", "--", ":"), strict=True
            ):
                ax.axvline(value, color="black", linestyle=style, linewidth=0.9)

        for ax in axes.flat[len(names) :]:
            ax.set_visible(False)

        figure.tight_layout()
        return figure

    def plot_crossplot(
        self,
        x: str,
        y: str,
        color: str | None = None,
        *,
        top: float | None = None,
        base: float | None = None,
        cmap: str = "viridis",
        ax: Axes | None = None,
        **scatter_kwargs: Any,
    ) -> Figure:
        """Plot one curve against another, optionally coloured by a third.

        Parameters
        ----------
        x, y : str
            Curves on the horizontal and vertical axes.
        color : str, optional
            Curve used to colour the points.
        top, base : float, optional
            Depth window; the whole log by default.
        cmap : str, default "viridis"
            Colour map when ``color`` is given.
        ax : matplotlib.axes.Axes, optional
            Axes to draw on; a new figure is created by default.
        **scatter_kwargs
            Passed to :meth:`matplotlib.axes.Axes.scatter`.

        Returns
        -------
        matplotlib.figure.Figure
        """
        keep = self.log.mask(top, base)
        xs, ys = self._values(x), self._values(y)
        keep &= ~np.isnan(xs) & ~np.isnan(ys)

        cs = None
        if color is not None:
            cs = self._values(color)
            keep &= ~np.isnan(cs)

        if ax is None:
            _, ax = plt.subplots(figsize=(6.0, 5.0))

        options = {"s": 4, **scatter_kwargs}
        if cs is None:
            ax.scatter(xs[keep], ys[keep], color=options.pop("color", "C0"), **options)
        else:
            points = ax.scatter(xs[keep], ys[keep], c=cs[keep], cmap=cmap, **options)
            ax.figure.colorbar(points, ax=ax, label=self._label(color))

        for name, set_scale in ((x, ax.set_xscale), (y, ax.set_yscale)):
            family = self.family(name)
            if family is not None and family.log_scale:
                set_scale("log")

        ax.set_xlabel(self._label(x))
        ax.set_ylabel(self._label(y))
        ax.set_title(f"{self.well_name} {y} vs {x}".strip())
        ax.grid(True, alpha=0.3)
        return ax.figure

    def plot_correlation(
        self,
        curves: str | Sequence[str] | None = None,
        *,
        method: str = "pearson",
        ax: Axes | None = None,
    ) -> Figure:
        """Plot the correlation matrix of the curves as a heat map.

        Parameters
        ----------
        curves : str or list of str, optional
            Curves to correlate; all curves by default.
        method : {"pearson", "spearman", "kendall"}, default "pearson"
            Correlation coefficient. "spearman" suits curves related
            non-linearly, such as resistivity.
        ax : matplotlib.axes.Axes, optional
            Axes to draw on; a new figure is created by default.

        Returns
        -------
        matplotlib.figure.Figure
        """
        names = self._names(curves)
        matrix = self._frame(names).corr(method=method).to_numpy()

        if ax is None:
            size = 0.45 * len(names) + 2.5
            _, ax = plt.subplots(figsize=(size + 1.0, size))

        image = ax.imshow(matrix, vmin=-1, vmax=1, cmap="RdBu_r")
        ax.set_xticks(range(len(names)), names, rotation=90)
        ax.set_yticks(range(len(names)), names)

        if len(names) <= 25:
            for (i, j), value in np.ndenumerate(matrix):
                if not np.isnan(value):
                    ax.text(
                        j,
                        i,
                        f"{value:.2f}",
                        ha="center",
                        va="center",
                        fontsize=6,
                        color="white" if abs(value) > 0.6 else "black",
                    )

        ax.figure.colorbar(image, ax=ax, label=f"{method.title()} correlation")
        ax.set_title(f"{self.well_name} curve correlation".strip())
        return ax.figure

    def save_report(self, path: str | os.PathLike[str]) -> Path:
        """Write every summary table and plot to a multi-page PDF.

        Pages: summary, file checks, curve inventory, coverage, statistics,
        curve quality, zones and zone averages (if tops are given), logs,
        histograms and correlation.

        Returns
        -------
        pathlib.Path
            The written file.
        """
        path = Path(path)
        metadata = {"Title": f"LasView report {self.well_name}".strip()}

        with PdfPages(path, metadata=metadata) as pdf:
            for figure in self._report_figures():
                pdf.savefig(figure, bbox_inches="tight")
                plt.close(figure)

        return path

    def _report_figures(self) -> Iterator[Figure]:
        """Yield the report pages one at a time."""
        yield self.plot_table(self.summary(), title="Summary", float_format="{:g}")
        yield self.plot_table(self.validate(), title="File checks")
        yield self.plot_table(title="Curve inventory")
        yield self.plot_coverage()
        yield self.plot_table(
            self.statistics(), title="Statistics", float_format="{:.4g}"
        )
        yield self.plot_table(
            self.quality(), title="Curve quality", float_format="{:.3g}"
        )
        if not self.tops.empty:
            yield self.plot_table(self.zones(), title="Zones")
            yield self.plot_table(
                self.zone_statistics(), title="Zone averages", float_format="{:.4g}"
            )
        yield self.plot_logs()
        yield self.plot_histograms()
        yield self.plot_correlation()

    # ------------------------------------------------------------------
    # Helpers

    def _curve(self, name: str) -> lasio.CurveItem:
        """Return the curve item ``name`` or raise a KeyError listing the curves."""
        try:
            return self.log.curves[name]
        except KeyError:
            available = ", ".join(self.log.keys())
            raise KeyError(f"No curve {name!r}; available: {available}.") from None

    def _values(self, name: str) -> np.ndarray:
        """Return the data of curve ``name`` as floats (non-numbers as NaN)."""
        return _numeric(self._curve(name).data)

    def _label(self, name: str) -> str:
        """Return "NAME [unit]" for axis labels."""
        unit = self._curve(name).unit
        return f"{name} [{unit}]" if unit else name

    def _names(self, curves: str | Sequence[str] | None) -> list[str]:
        """Return the requested curve names, checking that they exist."""
        if curves is None:
            return self.curves
        names = [curves] if isinstance(curves, str) else list(curves)
        for name in names:
            self._curve(name)
        return names

    def _tracks(self, tracks: Sequence[str | Sequence[str]] | None) -> list[list[str]]:
        """Return tracks as lists of checked curve names."""
        if tracks is None:
            return [[name] for name in self.curves]
        return [self._names(track) for track in tracks]

    def _frame(self, names: Sequence[str]) -> pd.DataFrame:
        """Return the curves as a DataFrame indexed by depth."""
        return pd.DataFrame(
            {name: self._values(name) for name in names},
            index=pd.Index(self.depth, name=self.depth_mnemonic),
        )

    def _step(self) -> float:
        """Return the median depth step (NaN for fewer than two samples)."""
        steps = np.abs(np.diff(self.depth))
        steps = steps[np.isfinite(steps)]
        return float(np.median(steps)) if steps.size else math.nan

    def _intervals(self, name: str, min_gap: float) -> list[tuple[float, float]]:
        """Return (top, bottom) of each run of data, merging gaps <= min_gap."""
        depth = self.depth
        valid = ~np.isnan(self._values(name)) & ~np.isnan(depth)
        runs = sorted(
            (min(depth[start], depth[stop]), max(depth[start], depth[stop]))
            for start, stop in _runs(valid)
        )

        merged: list[tuple[float, float]] = []
        for top, bottom in runs:
            if merged and top - merged[-1][1] <= min_gap:
                merged[-1] = (merged[-1][0], max(bottom, merged[-1][1]))
            else:
                merged.append((top, bottom))

        return [(float(top), float(bottom)) for top, bottom in merged]


def _as_welllog(las: lasio.LASFile) -> WellLog:
    """Return ``las`` as a WellLog, sharing its data (nothing is copied)."""
    if isinstance(las, WellLog):
        return las
    log = WellLog()
    log.__dict__.update(las.__dict__)
    return log


def _tops_frame(tops: TopsLike | None) -> pd.DataFrame:
    """Return formation tops as a DataFrame sorted by depth."""
    if tops is None:
        frame = pd.DataFrame(
            {"formation": pd.Series(dtype=str), "depth": pd.Series(dtype=float)}
        )
    elif isinstance(tops, pd.DataFrame):
        missing = {"formation", "depth"} - set(tops.columns)
        if missing:
            raise ValueError(f"tops DataFrame needs the columns {sorted(missing)}.")
        frame = tops[["formation", "depth"]].copy()
    elif isinstance(tops, pd.Series):
        frame = pd.DataFrame({"formation": tops.index, "depth": tops.to_numpy()})
    elif isinstance(tops, Mapping):
        frame = pd.DataFrame({"formation": list(tops), "depth": list(tops.values())})
    else:
        raise TypeError("tops must be a mapping, Series or DataFrame.")

    frame["formation"] = frame["formation"].astype(str)
    frame["depth"] = frame["depth"].astype(float)
    return frame.sort_values("depth", kind="stable").reset_index(drop=True)


def _item(section: lasio.SectionItems, mnemonic: str) -> Any:
    """Return the value of a header item, or None if missing or blank."""
    if mnemonic not in section:
        return None
    value = section[mnemonic].value
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _as_float(value: Any) -> float | None:
    """Return ``value`` as a float, or None if it is not a number."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _numeric(data: Any) -> np.ndarray:
    """Return ``data`` as a float array, with non-numeric entries as NaN."""
    try:
        return np.asarray(data, dtype=float)
    except (TypeError, ValueError):
        return pd.to_numeric(pd.Series(data), errors="coerce").to_numpy(dtype=float)


def _family_name(family: CurveFamily | None) -> str | None:
    return None if family is None else family.name


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Return (first, last) indices of each run of True values."""
    edges = np.flatnonzero(np.diff(np.concatenate(([0], mask.astype(int), [0]))))
    return [
        (int(start), int(stop) - 1)
        for start, stop in zip(edges[::2], edges[1::2], strict=True)
    ]


def _count_spikes(values: np.ndarray, threshold: float) -> int:
    """Count single-sample spikes.

    A sample is a spike if it jumps away from both neighbours, in the same
    direction, by more than ``threshold`` times the robust standard deviation
    of the curve's sample-to-sample changes. Unlike a running-median test,
    this leaves smooth peaks of processed curves alone.
    """
    if values.size < 3:
        return 0

    rise = values[1:-1] - values[:-2]
    fall = values[1:-1] - values[2:]

    steps = np.diff(values)
    steps = steps[np.isfinite(steps)]
    sigma = _MAD_TO_SIGMA * np.median(np.abs(steps - np.median(steps)))

    jump = np.minimum(np.abs(rise), np.abs(fall))
    return int(np.sum((rise * fall > 0) & (jump > threshold * sigma)))


def _longest_constant_run(values: np.ndarray) -> int:
    """Return the length of the longest run of identical consecutive values."""
    repeats = np.concatenate(([False], values[1:] == values[:-1]))
    runs = _runs(repeats)
    return max((stop - start + 2 for start, stop in runs), default=1)
