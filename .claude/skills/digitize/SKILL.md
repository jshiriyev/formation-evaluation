---
name: digitize
description: Digitize a scanned log (PDF or image) into LAS with pphys.digitize, then review the QC images and the resulting curve. Use when the user hands over a scanned log to convert.
argument-hint: "<scan.pdf|scan.png> [--vmin V --vmax V --curve NAME --depth-top T --depth-bottom B]"
allowed-tools: Bash(uv run *), Bash(tesseract *), Read, Write, Glob
---

# /digitize

Input: `$ARGUMENTS`.

The pipeline (`pphys/digitize/digitize.py`, an MVP) handles **one red curve** per
run: it renders the PDF page, finds the tracks from the red pixels, OCRs the depth
labels between the tracks (Tesseract) and fits `depth = a*y + b`, then maps the
per-row median x of the curve linearly onto `[vmin, vmax]`.

CLI flags: `--pdf` (required), `--outdir` (default `mvp_out`), `--page` (0),
`--scale` (render scale, 2.0), `--curve` (mnemonic, default `QK`), `--vmin`/`--vmax`
(track scale, default 0/8), `--step` (output spacing, 0.1524), and
`--depth-top`/`--depth-bottom` (manual depths in m; override OCR when both are set).

## Steps

1. **Inputs.** The scale defaults are rarely right: ask for the track's left/right
   scale values (`--vmin`/`--vmax`) and the curve mnemonic unless given. Look at the
   scan first (Read it) to read the scale off the header if it is legible, and confirm.
2. **Image input.** The CLI only reads PDFs. For a PNG/JPG, convert it in the
   scratchpad: `uv run python -c "from PIL import Image; Image.open('in.png').convert('RGB').save('in.pdf')"`.
3. **OCR.** Without `--depth-top/--depth-bottom`, Tesseract must be installed:
   `tesseract --version`. If it is missing, ask for the top and bottom depths of the
   page instead (or how to install Tesseract), rather than failing.
4. **Run.** Use an output folder in the scratchpad unless the user names one:
   `uv run python -m pphys.digitize.digitize --pdf <pdf> --outdir <out> --vmin .. --vmax .. --curve ..`
5. **QC.** Read `debug_curve_overlay.jpg` (curve trace on the track),
   `debug_depth_ocr.jpg` (OCR'd depth labels and the fit), and `track_red_mask.jpg`.
   Check: the trace follows the curve (no jumps to grid lines or other curves),
   the depth fit uses several labels and its top/bottom depths are plausible, and
   values stay inside `[vmin, vmax]`.
6. **Result.** Load the LAS with `pphys.read` and run `pphys.LasView(...)` `summary()`
   and `quality()`; plot the digitized curve next to the scan's track (scratchpad
   PNG) and Read it to compare.

## Report

The LAS path, depth range and step, the depth-fit quality (labels used, residuals if
shown), any QC problem with its likely cause (wrong scale, red grid lines, OCR misses)
and the flag that would fix it.
