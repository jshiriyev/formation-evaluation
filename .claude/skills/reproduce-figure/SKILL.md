---
name: reproduce-figure
description: Regenerate one of the reference figures in img/ with pphys (WellView one-pager, CrossView correlation, or the insight shaly-sand results) and compare it side by side with the reference, listing what matches, what differs and what pphys is missing. Use when asked how close the package is to a target figure or to work toward one.
argument-hint: "[well_view | cross_view | shaly_sand]"
allowed-tools: Bash(uv run *), Read, Glob, Grep, Write
---

# /reproduce-figure

Target: `$ARGUMENTS`. If empty, list the three targets and ask which one.

| Target | Reference | Built with | Notes |
|---|---|---|---|
| `well_view` | `img/onepage_well_view.png` | `pphys.onepage.WellView` | `notebooks/wellview_onepager.ipynb` is the closest existing build; `doc/wellview.md` is the API reference. |
| `cross_view` | `img/onepage_cross_view.png` | `pphys.onepage.CrossView` | `add_top`/`add_formation` expect well objects with `.tops[key]` and `.tops.limit(key)`; no such class exists, so write a small adapter in the script and say so in the report. |
| `shaly_sand` | `img/insight_shaly_sand_results.png` (models in `img/insight_shaly_sand_resistivity_models.png`) | `pphys.insight` models + WellView tracks | Many insight modules still import `borepy` and fail; run `/fix-insight-imports` on the ones needed first, or report them as blockers. |

Never modify `img/`; it holds the targets.

## Steps

1. Read the reference image. Write down its layout: figure size and aspect, number
   of tracks and their order, the curves in each track with colours, scales (linear/log,
   limits, flipped?), shading/fills/motifs, header rows, depth track (MD/TVD, print
   scale), tops/perforations/casing.
2. Pick the data: the `notebooks/tutorial_*.LAS` files (digitized textbook logs) or
   `real_field_data.las`. Say which curves stand in for which, when names differ.
3. Write the script to the scratchpad (Agg backend, `fig.savefig(..., dpi=150)`), run
   it with `uv run python`, and fix your script (not pphys) until it renders.
   Match the reference size and track widths as closely as the API allows.
4. Read the rendered PNG next to the reference. For a detailed visual review, hand
   both paths to the **plot-qa** agent.

## Report

- The script path and the PNG path (full absolute paths).
- A checklist per element of the reference: ✅ reproduced, ≈ close (what differs),
  ❌ not possible yet (which pphys feature is missing, with the class/method it
  would belong to).
- The two or three changes to pphys that would close most of the gap.
