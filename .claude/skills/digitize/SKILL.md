---
name: digitize
description: Digitize a scanned log (PDF or image) into LAS with pphys.digitize, then review the QC images and the resulting curve. Use when the user hands over a scanned log to convert.
argument-hint: "<scan.pdf|scan.png> [--curve NAME --vmin V --vmax V --scale linear|log10 --depth TOP BASE]"
allowed-tools: Bash(uv run *), Bash(tesseract *), Read, Write, Glob
---

# /digitize

Input: `$ARGUMENTS`.

`pphys.digitize` reads the curves of one PDF page:
1. It finds the tracks from their frame lines.
2. It calibrates depth from manual depths, or by OCR of the depth labels
   (Tesseract), fitting `depth = a*row + b`.
3. It picks each curve by its colour: by hue, or by darkness for black and grey.
   It removes grid lines and frames, follows the curve row by row, bridges short
   gaps, and maps its column across the track edges, linear or log10, onto
   `[vmin, vmax]`.

Python: `digitize(scan, curves=[Curve("GR", 0, 150, color="red"), Curve("RT", 0.2, 2000,
scale="log10", color="black", track=1)], ...)` reads several curves in one call.
`curve=, vmin=, vmax=, color=` is the shorthand for one. The result has `.las` (one
column per curve), `.qc` (with `.qc.curves`), `.raw` and `.images`; `.save(dir)`
writes them all. The command line reads one curve per run.

Command line: `uv run pphys-digitize SCAN --curve GR --vmin 0 --vmax 150 [options]`.
- **Required:** `--curve`, `--vmin`, `--vmax`.
- **Options:**
  - `--unit`, `--color` (the curve's colour: name or hex, default red), `--scale linear|log10` (as printed in the log header);
  - `--depth TOP BASE` (depths at the first and last page row; skips OCR), `--label-columns L R` (where the depth labels are, if not found), `--depth-unit m|ft`;
  - `--step` (0.1524 m / 0.5 ft by default), `--page` (0-based);
  - `--track auto|left|right|N` (default auto: the track holding the curve colour), `--track-edges L R` (page columns of the track edges; overrides detection);
  - `--well`, `--render-scale` (2.0), `--tesseract PATH`, `--out DIR` (default `<scan>_digitized`).

## Steps

1. **Inputs.** For each curve, ask for the mnemonic, its colour on the scan, the
   track's left and right scale values, and whether the track is linear or log10,
   unless given. Read the scan first: the
   scale is often legible in the header, so propose it and confirm.
2. **Image input.** Only PDFs are read for now. For a PNG/JPG, convert it in the
   scratchpad: `uv run python -c "from PIL import Image; Image.open('in.png').convert('RGB').save('in.pdf', resolution=72)"`.
3. **Track edges** are found from the frame lines. Check the summary's `track:` line
   and `tracks` in `qc.json`.
   - **The wrong track was read, or tracks are close:** pass `--track` (an index from
     the left) or `--track-edges L R` (columns of the borders, read off `page.png` at
     `--render-scale`).
   - **No track frames found:** typical of rotated or frameless scans. Pass
     `--track-edges`.
   - **"grid looks log10/linear" warning:** recheck `--scale`.
4. **OCR.** Without `--depth`, the depth labels are found and read with Tesseract
   (`find_tesseract()`, or `TESSERACT_CMD`). If Tesseract is missing, ask for the top
   and bottom depths of the page instead, or how to install it.
   - **Fit:** at least 3 labels must agree on one straight line; misreads are ignored
     and listed in the warnings.
   - **Labels not found:** pass `--label-columns L R` (read the columns off
     `page.png`), or fall back to `--depth`.
   - **Never** fall back to pixel depths.
   - **Same-colour curves:** two curves of the same colour in one track can't be
     told apart. A warning says so ("another curve of that colour"); tell the user
     rather than trusting that curve.
   - **Settings that matter:** when they're unclear, imitate the page with
     `synthetic_scan(...)` (same colours, scales and defects) and compare settings
     with `score(...)` before running on the real scan.
5. **Run.** Use an output folder in the scratchpad unless the user names one.
6. **QC.** Read the outputs:
   - `curve_overlay_<NAME>.png`: the trace on the track, cyan where found and magenta where a short gap was bridged. It should follow the curve, with no jumps to grid lines or other curves.
   - `track_mask_<NAME>.png`: what was taken as the curve.
   - The summary's per-curve line: rows found and bridged, and coverage.
   - For OCR, `depth_labels.png`: each label boxed, green when on the line and red when ignored, with the depth the fit gives it. The summary's `depth labels: N of M on the line, RMS r rows` should show most labels on the line and an RMS under about 1 row; a "stretched" warning means the scan's depth scale isn't uniform.
   - The summary's warnings, and `qc.json`.
7. **Result.** Load the LAS with `pphys.read` and run `pphys.LasView(...)` `summary()`
   and `quality()`. Plot the digitized curve next to the scan's track (scratchpad
   PNG) and Read it to compare.

## Report

- The LAS path, depth range and step.
- How depth was calibrated (manual, or OCR with N labels and the fit).
- Each QC warning or problem, its likely cause (wrong track, wrong scale type, red
  grid lines, OCR misses) and the option that would fix it.
