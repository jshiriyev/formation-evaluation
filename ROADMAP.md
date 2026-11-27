# Roadmap

**Objective.** Formation Evaluation gives practicing petrophysicists an end-to-end, open workflow: take a well from a raw LAS file or a paper scan, through quality control and interpretation, to report-ready one-page plots. It has two interfaces:

- **Python:** the `pphys` package, the engine of every step.
- **Browser:** no-code apps on [GitHub Pages](https://jshiriyev.github.io/formation-evaluation/) for the same workflow, computed by a hosted `pphys` service.

Today, loading, QC and single-well plots work. The milestones below close the remaining gaps, in this order.

| # | Milestone | Workflow step | State today |
|---|---|---|---|
| 1 | [Working interpretation](#1-working-interpretation) | Interpret | Models written, but most modules do not import |
| 2 | [Multi-well CrossView](#2-multi-well-crossview) | Plot several wells | Drawing code exists; no class holds a well's tops |
| 3 | [Robust digitizing](#3-robust-digitizing) | Digitize paper logs | Prototype: one red curve per run |
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

**Today.** `pphys.digitize.digitize()` and the `pphys-digitize` command digitize one red curve from one PDF page into a `WellLog`, with QC images and a `qc.json`. Depth comes from manual depths, or from the depth labels read by OCR (Tesseract) and fitted with a straight line. Values are mapped linearly across the track edges when given; otherwise they are approximate, scaled across the curve's own columns plus a margin. Tests cover the pipeline on simple synthetic pages.

**Done when:**
- [ ] Several curves can be digitized per track and per page, picked by any colour, not only red.
- [ ] Linear and logarithmic tracks (e.g. resistivity on a 0.2–2000 scale) are both supported.
- [ ] Image scans (PNG, JPG, TIFF) and multi-page PDFs are accepted directly.
- [x] A Python API returns a `pphys.WellLog` (`digitize(...).las`); the command line is a thin wrapper around it.
- [x] LAS files are written through lasio / `WellLog`, not by hand.
- [ ] QC output shows the trace overlay and the depth-fit residuals, and warns when the fit uses too few labels.
- [ ] Tests run on synthetic scans and need no Tesseract.

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
