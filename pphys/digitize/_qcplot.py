"""The QC figure of a digitized page (:meth:`DigitizeResult.plot_qc`).

Three panels share the depth axis: the scan with the tracks, the traces and
the depth labels; the depth-fit residual of each label; and the digitized
curves. The page's warnings are listed below. Plain matplotlib ``Figure``,
no pyplot, so nothing is shown or kept open.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.transforms import blended_transform_factory

# One trace colour per curve, cyan first as in the curve_overlay images.
TRACES = ("#00b8e6", "#ff8c00", "#2ca02c", "#9467bd", "#8c564b")
BRIDGED = "#e600e6"  # magenta
INLIER = "#1a9e3a"
MISREAD = "#d62728"
EDGE = "#1f5fbf"
WARN = "#a04000"
SCAN_CONTRAST = 0.45  # of the scan's own, under the overlays

# Sizes in inches.
PANEL_HEIGHT = 9.0
RESIDUAL_WIDTH = 1.7
CURVE_WIDTH = 1.4
GAP = 0.12
LEFT, RIGHT, TOP = 0.75, 0.2, 1.25
AXIS_BOTTOM = 0.55  # tick labels and the x label below the panels
LINE = 0.15  # one line of warnings


def qc_figure(result, page: int = 0) -> Figure:
    """The QC figure of ``result.qc.pages[page]``; see :meth:`DigitizeResult.plot_qc`."""
    qc = result.qc
    count = len(qc.pages)
    if not -count <= page < count:
        raise IndexError(f"page {page} does not exist: the result has {count} page(s).")
    page %= count
    pq = qc.pages[page]
    width, height = pq.page_size
    a, b = pq.depth_fit

    def depth(row):
        return a * np.asarray(row, dtype=float) + b

    prefix = f"p{page + 1}_" if count > 1 else ""
    image = result.images.get(prefix + "page")
    traces = result.traces[page] if page < len(result.traces) else {}

    scan_width = float(np.clip(PANEL_HEIGHT * width / height, 2.5, 9.0))
    widths = [scan_width, RESIDUAL_WIDTH] + [CURVE_WIDTH] * len(pq.curves)
    fig_width = LEFT + sum(widths) + GAP * (len(widths) - 1) + RIGHT
    warnings = _page_warnings(qc.warnings, page, count)
    lines = []
    for w in warnings or ["No warnings."]:
        lines += textwrap.wrap(w, int(fig_width * 15), subsequent_indent="    ")
    bottom = AXIS_BOTTOM + LINE * (len(lines) + 1)
    fig_height = TOP + PANEL_HEIGHT + bottom

    fig = Figure(figsize=(fig_width, fig_height), dpi=100, facecolor="white")
    axes, x = [], LEFT
    for w in widths:
        rect = [
            x / fig_width,
            bottom / fig_height,
            w / fig_width,
            PANEL_HEIGHT / fig_height,
        ]
        axes.append(fig.add_axes(rect, sharey=axes[0] if axes else None))
        x += w + GAP
    scan, resid, curve_axes = axes[0], axes[1], axes[2:]
    unit = str(result.las.curves[0].unit).lower() or "m"

    # The scan, its tracks, the traces and the labels
    top_edge, base_edge = float(depth(-0.5)), float(depth(height - 0.5))
    if image is not None:
        # The scan is faded toward white so the trace and the boxes stand out.
        faded = (255 - SCAN_CONTRAST * (255 - image[..., ::-1].astype(float))).astype(
            np.uint8
        )
        scan.imshow(
            faded,
            extent=(-0.5, width - 0.5, base_edge, top_edge),
            origin="upper",
            aspect="auto",
            interpolation="antialiased",
        )
    for x0, x1 in pq.tracks:
        for edge in (x0, x1):
            scan.axvline(edge, color=EDGE, lw=0.6, ls=(0, (3, 3)), alpha=0.8)
    names_at: dict[tuple[float, float], list[str]] = {}
    for c in pq.curves:
        names_at.setdefault(tuple(c.track), []).append(c.name)
    across = blended_transform_factory(scan.transData, scan.transAxes)
    for (x0, x1), names in names_at.items():
        for edge in (x0, x1):
            scan.axvline(edge, color=EDGE, lw=0.9)
        scan.text(
            (x0 + x1) / 2,
            1.005,
            ", ".join(names),
            transform=across,
            ha="center",
            va="bottom",
            fontsize=7,
            color=EDGE,
        )
    rows = np.arange(height)
    trace_colour = {c.name: TRACES[i % len(TRACES)] for i, c in enumerate(pq.curves)}
    for name, trace in traces.items():
        column = np.full(height, np.nan)
        column[trace.row] = trace.column
        bridged = np.zeros(height, dtype=bool)
        bridged[trace.row] = trace.bridged
        scan.plot(
            np.where(bridged, np.nan, column),
            depth(rows),
            color=trace_colour.get(name, TRACES[0]),
            lw=0.7,
        )
        if bridged.any():
            near = bridged | np.r_[bridged[1:], False] | np.r_[False, bridged[:-1]]
            scan.plot(
                np.where(near, column, np.nan), depth(rows), color=BRIDGED, lw=1.1
            )
    for i, (row, _) in enumerate(pq.depth_labels):
        colour = INLIER if pq.depth_inliers[i] else MISREAD
        if i < len(pq.depth_label_boxes):
            x0, y0, x1, y1 = pq.depth_label_boxes[i]
            top, base = float(depth(y0 - 1.5)), float(depth(y1 + 1.5))
            scan.add_patch(
                Rectangle(
                    (x0 - 1.5, top),
                    x1 - x0 + 3,
                    base - top,
                    fill=False,
                    ec=colour,
                    lw=0.8,
                )
            )
            if not pq.depth_inliers[i] and i < len(pq.depth_label_text):
                scan.text(
                    x1 + 4,
                    float(depth(row)),
                    pq.depth_label_text[i],
                    color=MISREAD,
                    fontsize=6,
                    va="center",
                )
    scan.set_xlim(-0.5, width - 0.5)
    scan.set_ylim(base_edge, top_edge)
    scan.set_ylabel(f"depth ({unit})", fontsize=8)
    scan.set_xlabel("page column (working pixels)", fontsize=7)
    scan.tick_params(labelsize=7)

    # The depth-fit residuals
    if pq.depth_source == "ocr" and pq.depth_labels:
        label_rows = np.array([row for row, _ in pq.depth_labels], dtype=float)
        residual = np.array(pq.depth_residuals, dtype=float)
        keep = np.array(pq.depth_inliers, dtype=bool)
        tol = result.settings.label_tolerance
        reach = max(2.0 * tol, 1.0)
        if keep.any():
            reach = max(reach, 1.25 * float(np.abs(residual[keep]).max()))
        resid.axvspan(-tol, tol, color="0.9", zorder=0)
        resid.axvline(0, color="0.5", lw=0.6)
        y = depth(label_rows)
        resid.scatter(residual[keep], y[keep], s=14, color=INLIER, zorder=3)
        for r, d, text in zip(
            residual[~keep],
            y[~keep],
            np.array(pq.depth_label_text, dtype=object)[~keep],
        ):
            at = float(np.clip(r, -reach, reach))
            resid.scatter(
                [at], [d], s=22, color=MISREAD, marker=">" if r > 0 else "<", zorder=3
            )
            resid.annotate(
                text,
                (at, d),
                xytext=(-4 if r > 0 else 4, 0),
                textcoords="offset points",
                ha="right" if r > 0 else "left",
                va="center",
                fontsize=6,
                color=MISREAD,
            )
        resid.set_xlim(-1.15 * reach, 1.15 * reach)
        rms = "" if pq.depth_rms is None else f"\nRMS {pq.depth_rms:.2f} rows"
        resid.set_title(
            f"depth fit\n{int(keep.sum())} of {keep.size} labels{rms}", fontsize=8
        )
        resid.set_xlabel(f"residual (rows; ±{tol:g} band)", fontsize=7)
    else:
        resid.text(
            0.5,
            0.5,
            "depth given by hand:\nno labels to check",
            transform=resid.transAxes,
            ha="center",
            va="center",
            fontsize=7,
            color="0.4",
        )
        resid.set_title("depth fit\nmanual", fontsize=8)
        resid.set_xticks([])
    resid.grid(True, color="0.88", lw=0.5)
    resid.tick_params(labelleft=False, labelsize=6)

    # The digitized curves, each on its own scale
    las_depth = np.asarray(result.las.index, dtype=float)
    for ax, c in zip(curve_axes, pq.curves):
        ax.plot(
            np.asarray(result.las[c.name], dtype=float),
            las_depth,
            color=_ink(c.color),
            lw=0.8,
        )
        if c.scale == "log10":
            ax.set_xscale("log")
        if c.vmin is not None and c.vmax is not None:
            ax.set_xlim(c.vmin, c.vmax)
        curve_unit = str(result.las.curves[c.name].unit)
        ax.set_title(c.name + (f"\n({curve_unit})" if curve_unit else ""), fontsize=8)
        ax.grid(True, which="both", color="0.88", lw=0.5)
        ax.tick_params(labelleft=False, labelsize=6)

    where = f"{Path(pq.source).name} #{pq.index}"
    if count > 1:
        where += f" (page {page + 1} of {count})"
    how = (
        "depth given by hand"
        if pq.depth_source == "manual"
        else f"depth from {sum(pq.depth_inliers)} of {len(pq.depth_labels)} labels"
    )
    fig.text(
        LEFT / fig_width,
        1 - 0.15 / fig_height,
        f"{where}: {how}, depth = {a:.6g} * row + {b:.6g}",
        fontsize=9,
        weight="bold",
        va="top",
    )
    handles = [
        *(
            Line2D([], [], color=trace_colour[c.name], lw=1.5, label=f"{c.name} trace")
            for c in pq.curves
        ),
        Line2D([], [], color=BRIDGED, lw=1.5, label="bridged"),
        Line2D([], [], color=EDGE, lw=1.0, label="track edges (dashed: other tracks)"),
        Patch(fill=False, ec=INLIER, label="label on the fit"),
        Patch(fill=False, ec=MISREAD, label="label ignored"),
    ]
    fig.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(LEFT / fig_width, 1 - 0.35 / fig_height),
        ncol=min(len(handles), 6),
        fontsize=7,
        frameon=False,
        handlelength=1.5,
    )
    fig.text(
        LEFT / fig_width,
        (bottom - AXIS_BOTTOM) / fig_height,
        "\n".join(lines),
        fontsize=7,
        color=WARN if warnings else "0.4",
        va="top",
    )
    return fig


def _page_warnings(warnings: list[str], page: int, count: int) -> list[str]:
    """The warnings about one page, and those about no page in particular."""
    if count == 1:
        return list(warnings)
    own = (f"page {page + 1} ", f"page {page + 1}:")
    return [
        w for w in warnings if w.startswith(own) or not re.match(r"page \d+[ :]", w)
    ]


def _ink(color: str):
    """The curve's colour, or dark grey when it would vanish on white."""
    try:
        rgb = to_rgb(color)
    except ValueError:
        return "black"
    return "0.3" if 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2] > 0.85 else rgb
