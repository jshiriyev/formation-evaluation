"""Command line for pphys.digitize: ``pphys-digitize`` or ``python -m pphys.digitize``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._digitize import DigitizeError, Settings, digitize


def _track(value: str) -> str | int:
    if value in ("left", "right"):
        return value
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "use 'left', 'right' or a track index"
        ) from None


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="pphys-digitize",
        description="Digitize one curve of a scanned log (PDF) into a LAS file, "
        "with QC images.",
    )
    ap.add_argument("scan", type=Path, help="the PDF scan")
    ap.add_argument("--curve", required=True, help="mnemonic of the curve, e.g. GR")
    ap.add_argument(
        "--vmin", type=float, required=True, help="value at the left track edge"
    )
    ap.add_argument(
        "--vmax", type=float, required=True, help="value at the right track edge"
    )
    ap.add_argument("--unit", default="", help="unit of the curve, e.g. gAPI")
    ap.add_argument(
        "--depth",
        type=float,
        nargs=2,
        metavar=("TOP", "BASE"),
        help="depths at the first and last row of the page; skips OCR",
    )
    ap.add_argument("--depth-unit", choices=("m", "ft"), default="m")
    ap.add_argument(
        "--step", type=float, help="output depth step (default 0.1524 m or 0.5 ft)"
    )
    ap.add_argument("--page", type=int, default=0, help="page to digitize, 0-based")
    ap.add_argument(
        "--track",
        type=_track,
        default="left",
        help="track to read: left, right or an index from the left (default left)",
    )
    ap.add_argument(
        "--track-edges",
        type=float,
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        help="page columns of the track edges (see page.png); exact value scale",
    )
    ap.add_argument(
        "--well", help="well name for the LAS header (default: the scan's name)"
    )
    ap.add_argument(
        "--scale", type=float, default=Settings.render_scale, help="PDF render scale"
    )
    ap.add_argument("--tesseract", help="path to the Tesseract executable")
    ap.add_argument(
        "--out",
        type=Path,
        help="output folder (default: <scan name>_digitized next to the scan)",
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    settings = Settings(render_scale=args.scale, tesseract=args.tesseract)
    try:
        result = digitize(
            args.scan,
            curve=args.curve,
            vmin=args.vmin,
            vmax=args.vmax,
            unit=args.unit,
            depth=args.depth,
            depth_unit=args.depth_unit,
            step=args.step,
            page=args.page,
            track=args.track,
            track_edges=args.track_edges,
            well=args.well,
            settings=settings,
        )
    except (DigitizeError, FileNotFoundError, ValueError) as exc:
        print(f"pphys-digitize: {exc}", file=sys.stderr)
        return 1

    out = args.out or args.scan.with_name(f"{args.scan.stem}_digitized")
    las_path = result.save(out)
    print(result.qc.summary())
    print(f"LAS: {las_path}")
    print(f"QC images and qc.json: {out}")
    return 0
