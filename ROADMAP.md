# Roadmap

**Objective.** Formation Evaluation gives practicing petrophysicists an end-to-end, open workflow: take a well from a raw LAS file or a paper scan, through quality control and interpretation, to report-ready one-page plots. It has two interfaces:

- **Python:** the `pphys` package, the engine of every step.
- **Browser:** no-code apps on [GitHub Pages](https://jshiriyev.github.io/formation-evaluation/) for the same workflow, computed by a hosted `pphys` service.

Today, loading, QC and single-well plots work. The milestones below close the remaining gaps, in this order.

| # | Milestone | Workflow step | State today |
|---|---|---|---|
| 1 | [Working interpretation](#1-working-interpretation) | Interpret | Models written, but most modules do not import |
| 2 | [Multi-well CrossView](#2-multi-well-crossview) | Plot several wells | Drawing code exists; no class holds a well's tops |
| 3 | [Robust digitizing](#3-robust-digitizing) | Digitize paper logs | PDF and image scans, several pages, several curves of any colour; edges and depth found; QC plots left |
| 4 | [Backend for the apps](#4-backend-for-the-apps) | Every step, in the browser | Configurator only; nothing is computed |

## 1. Working interpretation

**Goal.** `pphys.insight` covers the interpretation step: water analysis (Rw from SP), lithology and porosity (density, neutron, sonic, crossplots), shale volume (gamma ray, SP), water saturation (Archie, Hingle, Pickett and the shaly-sand models listed in [`img/insight_shaly_sand_resistivity_models.png`](img/insight_shaly_sand_resistivity_models.png)) and permeability.

**Done when:**
- [ ] Every module in `pphys/insight/` imports. None imports the old package name `borepy`, and `ruff check pphys/insight --select F821` reports no undefined names (about 70 today, in 8 modules).
- [ ] `pphys.insight` has a public API exported from its `__init__.py`. Today that file is empty and several subfolders have no `__init__.py`.
- [ ] Every model has tests. Every shaly-sand model reduces to Archie at Vsh = 0 (or Swb = 0), including for a ≠ 1, m ≠ 2 and n ≠ 2.
- [ ] The crossplot classes (`neuden`, `mnplot`, `sonneu`) take their matrix constants from `pphys/insight/lithology/_lithology.json`.
- [ ] A notebook runs the shaly-sand workflow of [`img/insight_shaly_sand_results.png`](img/insight_shaly_sand_results.png) on a log in `notebooks/` and shows it with WellView. The original South Caspian well's data is not in the repository.
- [ ] `doc/insight.md` documents the models, their equations and units.

## 2. Multi-well CrossView

**Goal.** `pphys.onepage.CrossView` reproduces [`img/onepage_cross_view.png`](img/onepage_cross_view.png): several wells side by side, correlated by their formation tops.

**Today.** `CrossView.add_top` and `add_formation` expect each well object to have `.tops[key]` and `.tops.limit(key)`, but no such class exists. The old `Formation` class (removed in commit 07046bd) stored tops per formation across wells, not per well.

**Done when:**
- [ ] A class holds one well's log and formation tops, built from a dict, Series or DataFrame the way `WellView.add_tops` accepts them.
- [ ] CrossView reproduces the reference figure from data in the repository.
- [ ] Tests and a `doc/crossview.md` reference exist.

## 3. Robust digitizing

**Goal.** Paper logs enter the workflow as reliably as LAS files.

**Today.** `pphys.digitize.digitize()` digitizes several curves in one call (`curves=[Curve(...)]`) into a `WellLog`, with QC images and a `qc.json`. It reads PDFs and image scans (PNG, JPG, TIFF, BMP), one page or several. The `pphys-digitize` command does the same for one curve. Depth comes from manual depths, or from OCR of the depth labels.
- **Inputs:** images are resampled from the DPI they store to the working 144 dpi. `dpi=` overrides a missing or wrong DPI; an image with neither is used as is, with a warning.
- **Several pages** (the pages of a PDF, the frames of a TIFF, or a list of files) each get their own tracks and depth calibration and are stitched by depth. Where pages overlap, the earlier page wins and the overlap is reported; a depth gap between pages is left empty and flagged.
- **Curves** are picked by any colour: coloured ones by hue, so faded ink counts, and black or grey ones by darkness. Each is followed row by row to the run nearest its path. Grid lines in its colour, frames and specks are removed. Short gaps (dashes, crossings) are bridged and long ones stay empty. Curves of one colour in one track are not told apart; a warning flags them.
- **Depth labels** are found in the depth column or margins (or given columns) and read by Tesseract, decimals and feet included. Each is snapped onto the grid line it marks.
- **Depth fit:** a robust straight-line fit ignores misreads and needs at least 3 agreeing labels. The QC reports each label's residual and warns on misreads, few labels or scatter.
- **Track edges** are found from the frame lines, to a fraction of a pixel. That works with tracks sharing a frame and with grids as dark as the frames, and `track_edges` can override it.
- **Values** are mapped across the edges on a linear or log10 scale. A QC warning flags a grid that looks like the other kind.

`pphys.digitize.synthetic_scan()` draws pages of known values, with optional scan defects, and `score()` measures a result against them. `python -m pphys.digitize.scorecard` runs 33 scenarios:
- **Pass today (31):** every scenario that is planned, within the target. That includes black curves (on grey and on black grids), coloured grids, crossing curves, flat beds, dashed curves, three curves in one call, PNG and JPG scans at 200–300 dpi or without a DPI, and two- and three-page PDFs, TIFFs and file lists, overlapping pages included. Value errors are 0.1–0.6 % RMS.
- **Not planned (2):** same-colour curves in one track, and rotated pages.

**Done when:**
- [x] Several curves can be digitized per track and per page, picked by any colour, not only red.
- [x] Linear and logarithmic tracks (e.g. resistivity on a 0.2–2000 scale) are both supported.
- [x] Track edges are found from the page, so `track_edges` is only needed when detection fails.
- [x] Image scans (PNG, JPG, TIFF) and multi-page PDFs are accepted directly.
- [x] A Python API returns a `pphys.WellLog` (`digitize(...).las`); the command line is a thin wrapper around it.
- [x] LAS files are written through lasio / `WellLog`, not by hand.
- [ ] QC output shows the trace overlay and the depth-fit residuals, and warns when the fit uses too few labels.
- [x] Tests run on synthetic scans and need no Tesseract.
- [x] Every planned scorecard scenario (all but rotation and same-colour curves) meets the target: value error RMS ≤ 1 % and max ≤ 3 % of the track width, the curve found in ≥ 98 % of the page rows, and depth error ≤ 0.5 % of the depth span.

## 4. Backend for the apps

**Goal.** A petrophysicist with no Python installed can run the whole workflow in the browser. The pages send the LAS file and the settings to a hosted `pphys` service and show the result.

**Today.** [`pages/onepage-wellview.html`](pages/onepage-wellview.html) reads a LAS file in the browser and builds a WellView set-up. That JSON payload is documented at the top of the page's script and has been replayed through WellView successfully. With `API_BASE = ''` the page only logs the payload.

**Done when:**
- [ ] A hosted service accepts the configurator's payload and LAS file and returns the plot (PNG and PDF). It resolves `{"style": "Table.name"}` references, turns table records into DataFrames and converts `year_axis` keys to integers.
- [ ] `API_BASE` is set, and the page shows the plot and any errors.
- [ ] Each app says plainly that the file is sent to the service, and how long it is kept.
- [ ] Apps exist for QC (`LasView`), interpretation (`insight`) and digitizing, each with a card in `index.html`.
- [ ] Where the service runs and how it is deployed are documented in the repository.

**Open decisions:** hosting, file-size limits, and abuse protection (rate limits or sign-in).

## Out of scope

- An interactive Bokeh log viewer (the former `pphys.stream`). The browser apps take its place.
- Induction-tool response modelling and invasion correction (the former `pphys.maxwres`).
- Publishing to PyPI. `pphys` is installed from GitHub (see the [README](README.md#install)).
