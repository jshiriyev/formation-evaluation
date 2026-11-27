---
name: digitize
description: Digitize a scanned log (PDF or image) into LAS with pphys.digitize, then review the QC images and the resulting curve. Use when the user hands over a scanned log to convert.
argument-hint: "<scan.pdf|scan.png> [--curve NAME --vmin V --vmax V --depth TOP BASE --track-edges L R]"
allowed-tools: Bash(uv run *), Bash(tesseract *), Read, Write, Glob
---

# /digitize

Input: `$ARGUMENTS`.

`pphys.digitize` (still a prototype algorithm, roadmap milestone 3) reads **one red
curve** per run:
1. It renders the PDF page and finds the tracks from the red pixels.
2. It calibrates depth from manual depths, or by OCR of the labels between the first
   and last track (Tesseract), fitting `depth = a*row + b`.
3. It maps the per-row median column of the curve linearly onto `[vmin, vmax]`.

Python: `digitize(scan, curve=, vmin=, vmax=, ...)` returns a result with `.las`
(a WellLog), `.qc` and `.images`; `.save(dir)` writes them all.

Command line: `uv run pphys-digitize SCAN --curve GR --vmin 0 --vmax 150 [options]`.
- **Required:** `--curve`, `--vmin`, `--vmax`.
- **Options:**
  - `--unit`, `--depth TOP BASE` (depths at the first and last page row; skips OCR), `--depth-unit m|ft`;
  - `--step` (0.1524 m / 0.5 ft by default), `--page` (0-based);
  - `--track left|right|N`, `--track-edges L R` (page columns of the track edges, giving an exact value scale);
  - `--well`, `--scale` (render scale, 2.0), `--tesseract PATH`, `--out DIR` (default `<scan>_digitized`).

## Steps

1. **Inputs.** Ask for the curve mnemonic and the track's left/right scale values
   unless given. Read the scan first: the scale is often legible in the header, so
   propose it and confirm.
2. **Image input.** Only PDFs are read for now. For a PNG/JPG, convert it in the
   scratchpad: `uv run python -c "from PIL import Image; Image.open('in.png').convert('RGB').save('in.pdf', resolution=72)"`.
3. **Track edges.** Without `--track-edges`, values are only approximate (scaled
   across the curve's own columns) and the QC warns about it. Do a first run, Read
   `page.png` (pixels of the rendered page, at `--scale`), find the columns of the track's
   left and right borders, and re-run with `--track-edges L R`.
4. **OCR.** Without `--depth`, Tesseract must be found (`find_tesseract()`, or
   `TESSERACT_CMD`). If it is missing, ask for the top and bottom depths of the page
   instead, or how to install Tesseract. A failed OCR stops with an error; never
   fall back to pixel depths. Today OCR is unreliable (scorecard `ocr_depth`), so
   prefer manual depths when the user can read them off the scan.
   - **Flat beds:** if the log has them (a blocky gamma ray), add `mask_kernel=1` in
     Python (`Settings(mask_kernel=1)`); the default cleaning erases near-vertical
     strokes.
   - **Settings that matter:** when they're unclear, imitate the page with
     `synthetic_scan(...)` (same colours, scales and defects) and compare settings
     with `score(...)` before running on the real scan.
5. **Run.** Use an output folder in the scratchpad unless the user names one.
6. **QC.** Read the outputs:
   - `curve_overlay.png`: the cyan trace on the track. It should follow the curve, with no jumps to grid lines or other curves.
   - `track_mask.png`.
   - For OCR, `depth_labels.png`: the labels read and the fit. Several labels should be read, and the fitted top and base depths should be plausible.
   - The summary's warnings, and `qc.json`.
7. **Result.** Load the LAS with `pphys.read` and run `pphys.LasView(...)` `summary()`
   and `quality()`. Plot the digitized curve next to the scan's track (scratchpad
   PNG) and Read it to compare.

## Report

- The LAS path, depth range and step.
- How depth was calibrated (manual, or OCR with N labels and the fit).
- Each QC warning or problem, its likely cause (approximate scale, red grid lines,
  OCR misses) and the option that would fix it.
