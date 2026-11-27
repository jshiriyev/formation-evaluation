---
name: digitize
description: Digitize a scanned log (PDF or image) into LAS with pphys.digitize, then review the QC images and the resulting curve. Use when the user hands over a scanned log to convert.
argument-hint: "<scan.pdf|scan.png|scan.tif ...> [--curve NAME --vmin V --vmax V --scale linear|log10 --depth TOP BASE --pages all --dpi D]"
allowed-tools: Bash(uv run *), Bash(tesseract *), Read, Write, Glob
---

# /digitize

Input: `$ARGUMENTS`.

`pphys.digitize` reads the curves of scanned log pages:
1. It loads PDFs and images (PNG, JPG, TIFF, BMP), one page or several. Images are
   resampled to the working 144 dpi from the DPI they store (or `--dpi`).
2. On each page it finds the tracks from their frame lines.
3. It calibrates each page's depth from manual depths, or by OCR of the depth
   labels (Tesseract), fitting `depth = a*row + b`.
4. It picks each curve by its colour: by hue, or by darkness for black and grey.
   It removes grid lines and frames, follows the curve row by row, bridges short
   gaps, and maps its column across the track edges, linear or log10, onto
   `[vmin, vmax]`.
5. With several pages, it stitches each curve by depth: where pages overlap the
   earlier page wins, and a gap between pages stays empty; both are warned about.

Python: `digitize(scan, curves=[Curve("GR", 0, 150, color="red"), Curve("RT", 0.2, 2000,
scale="log10", color="black", track=1)], ...)` reads several curves in one call.
`curve=, vmin=, vmax=, color=` is the shorthand for one. The result has `.las` (one
column per curve), `.qc` (with `.qc.curves`, and `.qc.pages`: one `PageQC` per
page), `.raw`, `.traces` and `.images`; `.plot_qc(page)` returns the QC figure;
`.save(dir)` writes them all, the figure as `qc.png` (`p<k>_qc.png` per page). `pages=` and `dpi=` work
as on the command line. The command line reads one curve per run.

Command line: `uv run pphys-digitize SCAN [SCAN ...] --curve GR --vmin 0 --vmax 150 [options]`.
Several files are read in order and stitched into one log.
- **Required:** `--curve`, `--vmin`, `--vmax`.
- **Options:**
  - `--unit`, `--color` (the curve's colour: name or hex, default red), `--scale linear|log10` (as printed in the log header);
  - `--depth TOP BASE` (depths at the first and last page row; skips OCR; once per page, in order, with several pages), `--label-columns L R` (where the depth labels are, if not found), `--depth-unit m|ft`;
  - `--step` (0.1524 m / 0.5 ft by default), `--pages N [N ...]|all` (0-based, counted over all files; default the first page of one file, every page of several), `--dpi D` (the resolution of image scans that store none or a wrong one);
  - `--track auto|left|right|N` (default auto: the track holding the curve colour), `--track-edges L R` (page columns of the track edges; overrides detection);
  - `--well`, `--render-scale` (2.0), `--tesseract PATH`, `--out DIR` (default `<first scan>_digitized`).

## Steps

1. **Inputs.** For each curve, ask for the mnemonic, its colour on the scan, the
   track's left and right scale values, and whether the track is linear or log10,
   unless given. Read the scan first: the
   scale is often legible in the header, so propose it and confirm.
2. **Pages and images.** PDFs and images are read directly.
   - **No DPI:** if the summary warns that the image "stores no DPI", it was
     used at its own size. Ask for the scan resolution and pass `--dpi`.
     Depth labels and narrow tracks are only found reliably near 144 dpi.
   - **Several pages:** a multi-page PDF or TIFF, or several files given in depth
     order. Pass `--pages all` for every page of one file (the default for
     several files). Either let OCR calibrate each page, or give `--depth TOP
     BASE` once per page.
   - **Overlaps and gaps:** check the warnings. Where pages overlap, the earlier
     page is kept; a gap between pages stays empty.
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
   With several pages, every QC image name starts with `p<k>_` (`p2_page.png`).
6. **QC.** Read `qc.png` first (`p<k>_qc.png` per page), then the details:
   - `qc.png`, left to right: the scan with each curve's trace (its own colour,
     magenta where bridged) and the label boxes; the depth-fit residual of each
     label (inside the grey band, misreads clipped to the edge in red); the
     digitized curves on their scales. The trace should sit on the ink, and the
     curves should look like the scan at the same depth. The page's warnings are
     printed below the panels.
   - `curve_overlay_<NAME>.png`: the trace on the track, cyan where found and magenta where a short gap was bridged. It should follow the curve, with no jumps to grid lines or other curves.
   - `track_mask_<NAME>.png`: what was taken as the curve.
   - The summary's per-curve line: rows found and bridged, and coverage.
   - For OCR, `depth_labels.png`: each label boxed, green when on the line and red when ignored, with the depth the fit gives it. The summary's `depth labels: N of M on the line, RMS r rows` should show most labels on the line and an RMS under about 1 row; a "stretched" warning means the scan's depth scale isn't uniform.
   - The summary's warnings, and `qc.json`. Warnings about a narrow label span
     (depths extrapolated), many misreads, or a curve found over less than 80 %
     of its range each point at a likely wrong band, track or colour.
7. **Result.** Load the LAS with `pphys.read` and run `pphys.LasView(...)` `summary()`
   and `quality()`. Plot the digitized curve next to the scan's track (scratchpad
   PNG) and Read it to compare.

## Report

- The LAS path, depth range and step.
- How depth was calibrated (manual, or OCR with N labels and the fit).
- Each QC warning or problem, its likely cause (wrong track, wrong scale type, red
  grid lines, OCR misses) and the option that would fix it.
