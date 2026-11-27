"""Command line for pphys.digitize: ``pphys-digitize`` or ``python -m pphys.digitize``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._digitize import DigitizeError, Settings, digitize


def _track(value: str) -> str | int:
    if value in ("auto", "left", "right"):
        return value
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "use 'auto', 'left', 'right' or a track index"
        ) from None


def _page(value: str) -> str | int:
    if value == "all":
        return value
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("use page indices or 'all'") from None


def _pages(values: list | None) -> str | int | list[int] | None:
    """--pages as digitize() takes it: None, 'all', one index or a list."""
    if values is None:
        return None
    if "all" in values:
        if len(values) > 1:
            raise argparse.ArgumentTypeError("--pages all takes no indices")
        return "all"
    return values[0] if len(values) == 1 else values


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="pphys-digitize",
        description="Digitize one curve of a scanned log (PDF or image, one page "
        "or several stitched by depth) into a LAS file, with QC images.",
    )
    ap.add_argument(
        "scan",
        type=Path,
        nargs="+",
        help="the scan: a PDF or a PNG, JPG, TIFF or BMP image; several files are "
        "read in order and stitched into one log",
    )
    ap.add_argument("--curve", required=True, help="mnemonic of the curve, e.g. GR")
    ap.add_argument(
        "--vmin", type=float, required=True, help="value at the left track edge"
    )
    ap.add_argument(
        "--vmax", type=float, required=True, help="value at the right track edge"
    )
    ap.add_argument("--unit", default="", help="unit of the curve, e.g. gAPI")
    ap.add_argument(
        "--color",
        default="red",
        help="the curve's colour: a name or hex, e.g. red, blue, black, '#1f77b4' (default red)",
    )
    ap.add_argument(
        "--scale",
        choices=("linear", "log10"),
        default="linear",
        help="track scale, as printed in the log header (default linear)",
    )
    ap.add_argument(
        "--depth",
        type=float,
        nargs=2,
        action="append",
        metavar=("TOP", "BASE"),
        help="depths at the first and last row of the page; skips OCR. With "
        "several pages, give it once per page, in order",
    )
    ap.add_argument("--depth-unit", choices=("m", "ft"), default="m")
    ap.add_argument(
        "--step", type=float, help="output depth step (default 0.1524 m or 0.5 ft)"
    )
    ap.add_argument(
        "--pages",
        type=_page,
        nargs="+",
        metavar="PAGE",
        help="pages to digitize, 0-based and counted over all files in order, or "
        "'all' (default: the first page of one file, every page of several)",
    )
    ap.add_argument(
        "--dpi",
        type=float,
        help="resolution of image scans, when the file stores none or a wrong one",
    )
    ap.add_argument(
        "--track",
        type=_track,
        default="auto",
        help="track to read: auto (the one holding the curve colour), left, right "
        "or an index from the left (default auto)",
    )
    ap.add_argument(
        "--track-edges",
        type=float,
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        help="page columns of the track edges (see page.png); overrides detection",
    )
    ap.add_argument(
        "--label-columns",
        type=float,
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        help="page columns holding the depth labels (default: searched outside the tracks)",
    )
    ap.add_argument(
        "--well", help="well name for the LAS header (default: the scan's name)"
    )
    ap.add_argument(
        "--render-scale",
        type=float,
        default=Settings.render_scale,
        help="working resolution as a multiple of 72 dpi: the PDF render scale, "
        "and the target images are resampled to (default 2.0, i.e. 144 dpi)",
    )
    ap.add_argument("--tesseract", help="path to the Tesseract executable")
    ap.add_argument(
        "--out",
        type=Path,
        help="output folder (default: <first scan's name>_digitized next to it)",
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = parser()
    args = ap.parse_args(argv)
    try:
        pages = _pages(args.pages)
    except argparse.ArgumentTypeError as exc:
        ap.error(str(exc))
    depth = args.depth
    if depth is not None and len(depth) == 1:
        depth = tuple(depth[0])
    elif depth is not None:
        depth = [tuple(d) for d in depth]
    scan = args.scan[0] if len(args.scan) == 1 else args.scan
    settings = Settings(render_scale=args.render_scale, tesseract=args.tesseract)
    try:
        result = digitize(
            scan,
            curve=args.curve,
            vmin=args.vmin,
            vmax=args.vmax,
            unit=args.unit,
            scale=args.scale,
            color=args.color,
            depth=depth,
            depth_unit=args.depth_unit,
            step=args.step,
            pages=pages,
            dpi=args.dpi,
            track=args.track,
            track_edges=args.track_edges,
            label_columns=args.label_columns,
            well=args.well,
            settings=settings,
        )
    except (DigitizeError, FileNotFoundError, ValueError) as exc:
        print(f"pphys-digitize: {exc}", file=sys.stderr)
        return 1

    first = args.scan[0]
    out = args.out or first.with_name(f"{first.stem}_digitized")
    las_path = result.save(out)
    print(result.qc.summary())
    print(f"LAS: {las_path}")
    print(f"QC figure: {', '.join(str(out / name) for name in result.qc_names())}")
    print(f"QC images and qc.json: {out}")
    return 0
