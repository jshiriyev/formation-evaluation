---
name: rerun-notebook
description: Re-execute one or all notebooks in notebooks/ in place with nbconvert (they are stored with their outputs), then report cell errors and which figures changed. Use after changing pphys code that a notebook demonstrates, or when asked to refresh notebook outputs.
argument-hint: "[notebook name | all]"
allowed-tools: Bash(uv run *), Bash(git diff*), Bash(git status*), Read, Glob, Write
---

# /rerun-notebook

Target: `$ARGUMENTS` (a name such as `wellview_onepager`, with or without
`.ipynb`; `all` or empty means every `notebooks/*.ipynb`). Only `.ipynb` files:
the `notebooks/*.py` scripts are stale (pre-rename API) and must not be run.

The notebooks and what they cover:
- `wellview_onepager.ipynb`: 12-track WellView one-pager, then each feature alone
  (`tutorial_3_graph_1` + `tutorial_3_graph_2` merged; tops/survey/casing/perfs are illustrative).
- `fill_styles.ipynb`: Lithology/Mineral/Porespace/motif keys, custom styles, a WellView
  lithology track and a cross-section.
- `lasview_real_field_data.ipynb`: LasView on `real_field_data.las` (cased-hole CBL, well ABD001).

## Steps

1. Snapshot the figures before running. Write a small script to the scratchpad that
   prints, per code cell, a short hash of every `image/png` output
   (`json.load` the notebook, `hashlib.sha1(base64-string)`), and run it with
   `uv run python <script> <notebook>`. Keep the output.
2. Execute in place, one notebook at a time:
   `uv run --with nbconvert jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 notebooks/<name>.ipynb`
   If a cell raises, nbconvert stops and leaves the file unchanged: report the
   cell number, its source (first lines) and the traceback tail, then go on with the
   next notebook. Don't patch the notebook to hide the error; find the cause in pphys
   or in the notebook code and say which it is.
3. Snapshot again and compare per cell: figures added, removed, changed.
   `git diff --stat notebooks/` shows the overall size of the change.
4. For each changed figure, decode the new PNG to the scratchpad and the old one
   (from `git show HEAD:notebooks/<name>.ipynb`), Read both and describe the visible
   difference in one line (e.g. "track 3 now on log scale", "motif tiling denser").
   Only pixel noise (same picture)? Say so.

## Report

Per notebook: ran OK / failed at cell N (reason); figures changed (cell: what changed);
execution counts and timing-only changes can be ignored. End with whether the new
outputs look right and should be committed.
