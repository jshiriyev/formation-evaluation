---
name: digitize
description: Digitize a scanned log (PDF or image) into LAS with pphys.digitize, then review the QC images and the resulting curve. Use when the user hands over a scanned log to convert.
argument-hint: "<scan.pdf|scan.png> [--curve NAME --vmin V --vmax V --scale linear|log10 --depth TOP BASE]"
allowed-tools: Bash(uv run *), Bash(tesseract *), Read, Write, Glob
---

# /digitize

Input: `$ARGUMENTS`.

`pphys.digitize` (still a prototype algorithm, roadmap milestone 3) reads **one red
curve** per run:
1. It renders the PDF page and finds the tracks from their frame lines.
2. It calibrates depth from manual depths, or by OCR of the depth labels
   (Tesseract), fitting `depth = a*row + b`.
3. It maps the per-row median column of the curve across the track edges, on a
   linear or log10 scale, onto `[vmin, vmax]`.

Python: `digitize(scan, curve=, vmin=, vmax=, ...)` returns a result with `.las`
(a WellLog), `.qc` and `.images`; `.save(dir)` writes them all.

Command line: `uv run pphys-digitize SCAN --curve GR --vmin 0 --vmax 150 [options]`.
- **Required:** `--curve`, `--vmin`, `--vmax`.
- **Options:**
  - `--unit`, `--scale linear|log10` (as printed in the log header);
  - `--depth TOP BASE` (depths at the first and last page row; skips OCR), `--label-columns L R` (where the depth labels are, if not found), `--depth-unit m|ft`;
  - `--step` (0.1524 m / 0.5 ft by default), `--page` (0-based);
  - `--track auto|left|right|N` (default auto: the track holding the curve colour), `--track-edges L R` (page columns of the track edges; overrides detection);
  - `--well`, `--render-scale` (2.0), `--tesseract PATH`, `--out DIR` (default `<scan>_digitized`).

## Steps

1. **Inputs.** Ask for the curve mnemonic, the track's left and right scale values,
   and whether the track is linear or log10, unless given. Read the scan first: the
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
