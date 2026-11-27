"""Scorecard: digitize synthetic pages of known values and score each one.

Every scenario draws a page with :func:`~pphys.digitize.synthetic_scan`,
digitizes one or more curves with :func:`~pphys.digitize.digitize` (in one
call) and compares each with the truth (:func:`~pphys.digitize.score`).
``gap`` names the roadmap step expected to make a failing scenario pass;
scenarios without one should pass today. The tests run the same list.

    uv run python -m pphys.digitize.scorecard [--keep DIR] [NAME ...]
"""

from __future__ import annotations

import argparse
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ._digitize import Curve, DigitizeError, Settings, digitize, find_tesseract
from ._synthetic import (
    Defects,
    Score,
    SyntheticCurve,
    SyntheticTrack,
    score,
    synthetic_scan,
    write_pages,
)


@dataclass(frozen=True)
class Scenario:
    """A synthetic page and how to digitize it.

    Parameters
    ----------
    name, description : str
        Identifier and one line on what is tested.
    page : dict
        Keyword arguments of :func:`~pphys.digitize.synthetic_scan`.
    curve : str or tuple of str
        The curve(s) to digitize, in one call. Each is passed with its true
        scale, colour and unit, as a user reading the log header would.
    track : "auto", "left", "right", int, or dict of curve to those
        The ``track`` of each curve.
    edges : bool
        Pass the true track edges (``track_edges``) instead of letting the
        digitizer find them.
    manual_depth : bool
        Pass the true depths; otherwise depth comes from OCR of the labels.
    settings : dict
        Keyword arguments of :class:`~pphys.digitize.Settings`.
    more_pages : tuple of dict
        Pages after the first, each as keyword arguments of
        :func:`~pphys.digitize.synthetic_scan`; they are stitched by depth.
    fmt : str
        File type the pages are written as: "pdf", "png", "jpg", "tif".
    files : bool
        Write each page to its own file and pass the list of files.
    dpi_tag : bool
        Whether image files store their DPI.
    gap : str or None
        Why the scenario fails today and which roadmap step should fix it;
        None when it should pass.
    """

    name: str
    description: str
    page: dict = field(default_factory=dict)
    curve: str | tuple[str, ...] = "GR"
    track: str | int | dict = "left"
    edges: bool = False
    manual_depth: bool = True
    settings: dict = field(default_factory=dict)
    more_pages: tuple[dict, ...] = ()
    fmt: str = "pdf"
    files: bool = False
    dpi_tag: bool = True
    gap: str | None = None

    @property
    def curves(self) -> tuple[str, ...]:
        return (self.curve,) if isinstance(self.curve, str) else tuple(self.curve)

    @property
    def needs_ocr(self) -> bool:
        return not self.manual_depth

    def track_of(self, name: str):
        return (
            self.track.get(name, "auto") if isinstance(self.track, dict) else self.track
        )


def _gr_track(*curves: SyntheticCurve) -> SyntheticTrack:
    return SyntheticTrack(curves or (SyntheticCurve("GR", unit="gAPI"),), 0.0, 150.0)


def _rt_track(color: str = "red") -> SyntheticTrack:
    return SyntheticTrack(
        (SyntheticCurve("RT", color=color, unit="ohm.m"),), 0.2, 2000.0, scale="log10"
    )


def blocky_gr(depth):
    """Gamma ray of flat beds with soft boundaries, for pages from 1000 to 1100."""
    beds = np.array([1000, 1012, 1020, 1035, 1041, 1060, 1072, 1085])
    levels = np.array([30.0, 110.0, 45.0, 125.0, 25.0, 95.0, 40.0, 120.0])
    raw = levels[
        np.clip(np.searchsorted(beds, depth, side="right") - 1, 0, len(levels) - 1)
    ]
    kernel = np.exp(-0.5 * (np.arange(-15, 16) / 5.0) ** 2)
    return np.convolve(
        np.pad(raw, 15, mode="edge"), kernel / kernel.sum(), mode="valid"
    )


def _three_tracks() -> tuple[SyntheticTrack, ...]:
    """GR | depth | RT (log10) | NPHI (flipped, 0.45 to -0.15), the last two sharing a frame."""
    nphi = SyntheticTrack((SyntheticCurve("NPHI", unit="v/v"),), 0.45, -0.15)
    return (_gr_track(SyntheticCurve("GR", color="blue")), _rt_track("blue"), nphi)


def _gr_and_sp() -> SyntheticTrack:
    return _gr_track(
        SyntheticCurve("GR", unit="gAPI"),
        SyntheticCurve("SP", color="blue", unit="mV", vmin=-160.0, vmax=40.0),
    )


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("clean", "red GR on a linear track; edges found, true depths"),
    Scenario("manual_edges", "the true track edges given as track_edges", edges=True),
    Scenario(
        "auto_track",
        "track='auto' picks the track of the only red curve",
        page={"tracks": (_gr_track(), _rt_track("blue"))},
        track="auto",
    ),
    Scenario(
        "three_tracks",
        "a flipped neutron track (0.45 to -0.15) sharing its frame with a log10 track",
        page={"tracks": _three_tracks()},
        curve="NPHI",
        track="right",
    ),
    Scenario(
        "uniform_grid",
        "grid lines as dark as the track frames",
        page={"grid_color": "black"},
    ),
    Scenario(
        "ocr_depth",
        "depth from OCR of the printed labels instead of given depths",
        manual_depth=False,
    ),
    Scenario(
        "ocr_feet",
        "OCR depth with labels in feet every 50 ft",
        page={
            "depth": (3300.0, 3600.0),
            "depth_unit": "ft",
            "step": 0.5,
            "label_every": 50.0,
            "grid_every": 10.0,
        },
        manual_depth=False,
    ),
    Scenario(
        "ocr_decimal",
        "OCR depth with decimal labels (every 2.5 m)",
        page={"depth": (1000.0, 1025.0), "label_every": 2.5, "grid_every": 0.5},
        manual_depth=False,
    ),
    Scenario(
        "ocr_left_column",
        "OCR depth with the depth column left of all tracks",
        page={"depth_column": 0},
        manual_depth=False,
    ),
    Scenario(
        "ocr_poor_scan",
        "OCR depth on a noisy, blurred, JPEG'd scan of faded, yellowed paper",
        page={
            "defects": Defects(tint="#f1e4c4", fade=0.4, noise=10.0, blur=0.8, jpeg=50)
        },
        manual_depth=False,
    ),
    Scenario(
        "feet",
        "depths and labels in feet",
        page={
            "depth": (3300.0, 3600.0),
            "depth_unit": "ft",
            "step": 0.5,
            "label_every": 50.0,
            "grid_every": 10.0,
        },
    ),
    Scenario(
        "blue_curve",
        "a blue curve, picked with color='blue'",
        page={"tracks": (_gr_track(SyntheticCurve("GR", color="blue")), _rt_track())},
    ),
    Scenario(
        "two_colours_one_track",
        "red GR crossing a blue SP curve drawn over it, in the same track",
        page={"tracks": (_gr_and_sp(), _rt_track())},
    ),
    Scenario(
        "several_curves",
        "GR (red) and SP (blue) in one track and RT (black, log10) in another, in one call",
        page={"tracks": (_gr_and_sp(), _rt_track("black"))},
        curve=("GR", "SP", "RT"),
        track={"GR": "left", "SP": "left", "RT": "right"},
    ),
    Scenario(
        "blocky_beds",
        "a blocky GR with flat beds and soft boundaries, like a real log",
        page={
            "tracks": (
                _gr_track(SyntheticCurve("GR", values=blocky_gr, unit="gAPI")),
                _rt_track(),
            )
        },
    ),
    Scenario(
        "dashed_curve",
        "a dashed GR, whose gaps between dashes are bridged",
        page={"tracks": (_gr_track(SyntheticCurve("GR", linestyle="--")), _rt_track())},
    ),
    Scenario(
        "log_track",
        "resistivity on a log10 track (0.2-2000)",
        curve="RT",
        track="right",
    ),
    Scenario(
        "black_curve",
        "a black curve on a grey grid",
        page={"tracks": (_gr_track(SyntheticCurve("GR", color="black")), _rt_track())},
    ),
    Scenario(
        "ocr_black_curve",
        "a black curve with OCR depth: the black depth labels must not be taken for curve",
        page={"tracks": (_gr_track(SyntheticCurve("GR", color="black")), _rt_track())},
        manual_depth=False,
    ),
    Scenario(
        "black_on_black_grid",
        "a black curve on a grid as dark as itself",
        page={
            "tracks": (_gr_track(SyntheticCurve("GR", color="black")), _rt_track()),
            "grid_color": "black",
        },
    ),
    Scenario(
        "coloured_grid",
        "grid lines in light red, close to the curve colour",
        page={"grid_color": "#e57373"},
    ),
    Scenario(
        "noisy_scan",
        "speckle noise, slight blur and JPEG artefacts",
        page={"defects": Defects(noise=12.0, blur=0.8, jpeg=40)},
    ),
    Scenario(
        "faded_tinted",
        "yellowed paper and ink faded halfway",
        page={"defects": Defects(tint="#f1e4c4", fade=0.5)},
    ),
    Scenario(
        "png_300dpi",
        "a PNG scan at 300 dpi, resampled to the working 144 dpi",
        page={"dpi": 300},
        fmt="png",
    ),
    Scenario(
        "jpg_200dpi_ocr",
        "a JPEG scan at 200 dpi, depth from OCR",
        page={"dpi": 200},
        fmt="jpg",
        manual_depth=False,
    ),
    Scenario(
        "png_without_dpi",
        "a PNG that stores no DPI, used as is (with a warning)",
        fmt="png",
        dpi_tag=False,
    ),
    Scenario(
        "pdf_two_pages_ocr",
        "a two-page PDF stitched into one log, depth from OCR on each page",
        page={"depth": (1000.0, 1100.0)},
        more_pages=({"depth": (1100.0, 1200.0), "seed": 1},),
        manual_depth=False,
    ),
    Scenario(
        "tiff_pages_overlap",
        "a three-frame 300 dpi TIFF whose pages overlap by 10 m",
        page={"depth": (1000.0, 1100.0), "dpi": 300},
        more_pages=(
            {"depth": (1090.0, 1190.0), "dpi": 300, "seed": 1},
            {"depth": (1180.0, 1280.0), "dpi": 300, "seed": 2},
        ),
        fmt="tif",
    ),
    Scenario(
        "png_page_files",
        "two pages as separate PNG files, stitched",
        page={"depth": (1000.0, 1100.0)},
        more_pages=({"depth": (1100.0, 1200.0), "seed": 1},),
        fmt="png",
        files=True,
    ),
    Scenario(
        "same_colour_track",
        "two red curves in one track; only one can be read by colour",
        page={
            "tracks": (
                _gr_track(
                    SyntheticCurve("GR"), SyntheticCurve("CGR", vmin=-150.0, vmax=150.0)
                ),
                _rt_track("blue"),
            )
        },
        gap="not planned: curves of one colour in one track are not told apart (a QC warning flags them)",
    ),
    Scenario(
        "rotated",
        "the page rotated by 1 degree",
        page={"defects": Defects(rotation=1.0)},
        gap="not planned: deskewing rotated scans is outside milestone 3",
    ),
)


@dataclass
class Row:
    """One scenario's outcome: a score per curve, or the error that stopped it."""

    scenario: Scenario
    scores: list[Score] = field(default_factory=list)
    error: str | None = None
    skipped: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def score(self) -> Score | None:
        return self.scores[0] if self.scores else None

    @property
    def passed(self) -> bool:
        return bool(self.scores) and all(s.passed for s in self.scores)


def run_scenario(scenario: Scenario, folder: str | Path) -> Row:
    """Draw, digitize and score one scenario; the pages are written to ``folder``."""
    if scenario.needs_ocr:
        try:
            find_tesseract(scenario.settings.get("tesseract"))
        except DigitizeError:
            return Row(scenario, skipped="Tesseract not found")
    scans = [synthetic_scan(**kw) for kw in (scenario.page, *scenario.more_pages)]
    folder = Path(folder)
    if scenario.files:
        paths = [
            folder / f"{scenario.name}_{k}.{scenario.fmt}" for k in range(len(scans))
        ]
        for path, scan in zip(paths, scans):
            write_pages(path, [scan], dpi_tag=scenario.dpi_tag)
        source = paths
    else:
        source = write_pages(
            folder / f"{scenario.name}.{scenario.fmt}", scans, dpi_tag=scenario.dpi_tag
        )
    multi = len(scans) > 1
    settings = Settings(**scenario.settings)
    first = scans[0]
    curves = []
    for name in scenario.curves:
        track, spec = first.curve(name)
        vmin, vmax = track.range_of(spec)
        curves.append(
            Curve(
                name,
                vmin,
                vmax,
                unit=spec.unit,
                scale=track.scale,
                color=spec.color,
                track=scenario.track_of(name),
                track_edges=first.track_edges(name, settings.render_scale)
                if scenario.edges
                else None,
            )
        )
    depth = None
    if scenario.manual_depth:
        pairs = [s.depth_pairs(settings.render_scale) for s in scans]
        depth = pairs if multi else pairs[0]
    try:
        result = digitize(
            source,
            curves=curves,
            depth=depth,
            depth_unit=first.depth_unit,
            pages="all" if multi else None,
            settings=settings,
        )
    except DigitizeError as exc:
        return Row(scenario, error=str(exc))
    return Row(
        scenario,
        scores=[score(result, scans, name) for name in scenario.curves],
        warnings=list(result.qc.warnings),
    )


def run(names=None, folder: str | Path | None = None) -> list[Row]:
    """Run the scenarios called ``names`` (all by default); pages go to ``folder`` or a temp folder."""
    chosen = [s for s in SCENARIOS if names is None or s.name in names]
    unknown = set(names or ()) - {s.name for s in SCENARIOS}
    if unknown:
        raise ValueError(f"Unknown scenario(s) {sorted(unknown)}; see SCENARIOS.")
    if folder is not None:
        Path(folder).mkdir(parents=True, exist_ok=True)
        return [run_scenario(s, folder) for s in chosen]
    with tempfile.TemporaryDirectory() as tmp:
        return [run_scenario(s, tmp) for s in chosen]


def table(rows: list[Row]) -> str:
    """The scorecard as text, one line per curve."""
    head = f"{'scenario':28} {'rms %':>7} {'max %':>7} {'cover %':>8} {'depth %':>8}  result  expected"
    lines = [head, "-" * len(head)]
    for row in rows:
        s = row.scenario
        expected = "pass" if s.gap is None else s.gap.split(":")[0]
        entries = row.scores or [None]
        for sc in entries:
            label = (
                s.name if len(s.curves) == 1 else f"{s.name}[{sc.curve if sc else '?'}]"
            )
            if sc is not None:
                nums = f"{sc.rms:7.2f} {sc.max:7.2f} {sc.coverage:8.1f} {sc.depth:8.3f}"
                result = "pass" if sc.passed else "FAIL"
            else:
                nums = f"{'-':>7} {'-':>7} {'-':>8} {'-':>8}"
                result = "skip" if row.skipped else "error"
            ok = row.passed if sc is not None else False
            flag = (
                "" if ok == (s.gap is None) or result == "skip" else "  <- unexpected"
            )
            lines.append(f"{label:28} {nums}  {result:6}  {expected}{flag}")
    for row in rows:
        if row.error:
            lines.append(f"{row.scenario.name}: {row.error}")
        if row.skipped:
            lines.append(f"{row.scenario.name}: skipped, {row.skipped}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m pphys.digitize.scorecard",
        description="Digitize synthetic pages of known values and score them.",
    )
    ap.add_argument("names", nargs="*", help="scenarios to run (default: all)")
    ap.add_argument("--keep", type=Path, help="write the pages to this folder")
    args = ap.parse_args(argv)
    print(table(run(args.names or None, args.keep)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
