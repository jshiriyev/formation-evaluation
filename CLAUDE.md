# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Objective and priorities

Formation Evaluation (package `pphys`) gives **practicing petrophysicists** an end-to-end, open workflow: take a well from raw LAS or a paper scan, through QC and interpretation, to report-ready one-page plots.
- **Two interfaces with equal goals:** the Python package (the engine) and no-code browser apps on GitHub Pages. The apps will be computed by a hosted `pphys` service, so uploaded files leave the browser.
- **Milestones, in order** (`ROADMAP.md` has the done-when lists):
  1. working interpretation (`pphys.insight` imports, is tested and reproduces the shaly-sand workflow);
  2. multi-well CrossView (a class for each well's tops; reproduces `img/onepage_cross_view.png`);
  3. robust digitizing (multi-curve, any colour, image input, Python API);
  4. a backend for the apps.

  Prefer work that advances the current milestone, and tick its items in `ROADMAP.md` when they are done.
- **Out of scope:** a Bokeh streaming viewer (the former `pphys.stream`), induction-tool modelling (the former `pphys.maxwres`), and PyPI. Install is from GitHub only.
- **License:** MIT (`LICENSE`). The README leads with the "Formation Evaluation" name; `pphys` is the import name. Keep the README's status column honest.

## What this is

`pphys` is a petrophysics package with three features:

1. **onepage**: one-page matplotlib log plots from LAS files. `WellView` draws a single well and `CrossView` a multi-well correlation. Target output: `img/onepage_well_view.png`, `img/onepage_cross_view.png`.
2. **digitize**: scanned log (PDF) → `WellLog`/LAS. `pphys.digitize.digitize()` reads several curves of any colour in one call; `pphys-digitize` reads one. Milestone 3 has image input and the QC plots left.
3. **insight**: log interpretation models, covering water analysis, lithology/porosity/shale volume, saturation (Archie + shaly-sand) and permeability. Target workflow: `img/insight_shaly_sand_results.png`. The resistivity models it should support are listed in `img/insight_shaly_sand_resistivity_models.png`.

`img/` holds the reference figures the package is expected to reproduce. `index.html` and `pages/` are browser apps published on GitHub Pages (see "Web apps" below).

`notebooks/` holds demo exercises:
- `real_field_data.las` is a real cased-hole cement-bond run (well ABD001), used by `lasview_real_field_data.ipynb`.
- `fill_styles.ipynb` demonstrates the fill styles: the lithology, mineral, pore-space and motif keys, custom styles, a WellView lithology/volume display and a cross-section.
- `wellview_onepager.ipynb` builds a 12-track WellView one-pager and then shows each feature on its own. It uses `tutorial_3_graph_1` and `tutorial_3_graph_2` merged (same depths); its tops, survey, casing and perforations are illustrative. `doc/wellview.md` is the WellView reference.
- `tutorial_*.LAS` are digitized textbook logs.
- The `.py` scripts there are **stale**. They import the pre-rename API (`pphys.visualization`, `Formation`, `Correlation`, `Weaver`, `lasview`).

## Setup & commands

The project is managed with **uv**. Always run tools through `uv run`, never a system Python: the machine's global Pythons differ (3.12 holds a stale non-editable `pphys`, and 3.14 has no lasio).

```bash
uv sync                                              # create/update .venv from uv.lock (prompt "pphys")
uv run pytest                                        # all tests
uv run pytest tests/test_welllog.py::test_copy_window  # one test
uv run ruff check pphys --no-cache --select F821     # quickest way to find broken code (undefined names)
uv run pphys-digitize scan.pdf --curve GR --vmin 0 --vmax 150 [--color black] [--scale log10] [--depth TOP BASE | --label-columns L R] [--track auto] [--out DIR]
uv add <pkg>        # runtime dependency (use --optional digitize or --dev for the others)
uv build            # wheel + sdist into dist/
```

- **Python version:** `.python-version` pins Python 3.12 for the environment. `requires-python` stays `>=3.10` because the code uses `X | None` syntax.
- **Dependencies:** runtime dependencies are in `[project] dependencies`.
  - The `digitize` extra holds opencv-python-headless, pypdfium2 and pytesseract; the Tesseract program must be installed separately.
  - The `dev` dependency group holds pytest and ruff, plus `pphys[digitize]`, so a bare `uv sync` installs every feature.
  - Don't edit `uv.lock` by hand; commit it.
- **Build backend:** `uv_build`, with `module-root = ""` because this is a flat layout (`./pphys`, not `./src/pphys`). It packages every file under `pphys/`, including `_lithology.json` and subfolders without an `__init__.py`.

Tests use pytest, and uv installs `pphys` in editable mode, so tests import the working tree. Tests cover the top-level modules (`WellLog`, `read`, `load`, `Temperature`, `LasView`, the curve families), the onepage fills (`test_motifs`, `test_templix`, `test_pigment`), the wellview layout chain (`test_layout`), its rounding helpers (`test_unary`), WellView itself (`test_wellview`) the digitizer on synthetic PDF pages with OCR stubbed (`test_digitize`), and the synthetic-page generator, the score and every scorecard scenario (`test_digitize_synthetic`; known gaps are strict xfails); insight has none yet. `tests/conftest.py` does the following:
- switches matplotlib to the Agg backend and closes figures after each test;
- provides the fixtures `write_las`, `age` (moves a file's modification time back so cache tests don't depend on timestamp resolution), `parses` (counts LAS parses to prove cache hits) and `cache`.

The `.ipynb` notebooks are stored with their outputs. They are re-run with `uv run --with nbconvert jupyter nbconvert --to notebook --execute --inplace <notebook>`.

## Architecture

### LAS I/O (top level)

- `pphys.read(path, cache_path)` and `pphys.load(dir, cache_dir)` return `pphys.WellLog` (defined in `_lasio.py`).
  - It is a `lasio.LASFile` subclass that adds `mask`, `crop`, `resample` (NaN outside the logged range) and `copy(dmin, dmax)` (a cropped deep copy).
  - `read` caches only when `cache_path` is given. A cache file is named `<stem>-<hash of absolute path + read kwargs>.pkl` and is reused only while it is newer than the LAS file. Unreadable or outdated pickles, e.g. from a renamed class, are rebuilt automatically.
  - `load` calls `read` for every `*.las` file (any letter case, not recursive), so both share one cache. It returns `{stem: WellLog}` in case-insensitive name order.
- `pphys.LasView` (`_view.py`) summarizes and checks one LAS file. `doc/lasview.md` is the user reference and `notebooks/lasview_real_field_data.ipynb` the worked example.
  - It is built from a path, which goes through `pphys.read`, or from a loaded `WellLog`/`LASFile`, plus optional `tops`.
  - Table methods return DataFrames: `summary`, `header`, `inventory`, `statistics`, `intervals`/`gaps`, `quality`, `validate`, `zones`, `zone_statistics`.
  - Plot methods return Figures and never call `plt.show()`: `plot_coverage`, `plot_table`, `plot_logs`, `plot_histograms`, `plot_crossplot`, `plot_correlation`. `save_report` writes them all to a PDF, and `window(top, base)` returns a cropped `LasView`.
  - The `quality` checks rely on the curve families in `_families.py`.
- `_families.py` recognizes a curve type from its mnemonic (regex, first match wins) or, failing that, from an identifying unit.
  - Each family carries plausible ranges per unit (after `normalize_unit`), whether it plots on a log axis, a colour, and `smooth`: False skips the spike and flat-line checks, e.g. for CCL and azimuths.
  - Order matters where patterns overlap, e.g. DTS must come before DT and density correction before density.
- `pphys.Temperature` (`_temp.py`) is a frozen dataclass for a linear geothermal model: `T = surface + gradient * (depth - surface_depth)`.
  - `unit_system` is `"field"` (ft, degF) or `"metric"` (m, degC), and every other value is in that system. Field defaults are exact conversions of the metric ones.
  - `Temperature.from_points(d1, t1, d2, t2, unit_system=)` builds the model from two measurements.
  - Calling the model evaluates it; `depth_unit="m"`/`"ft"` converts incoming depths.
  - Static helpers: `f_to_c`/`c_to_f`, `resistivity` (Arps), `horner` (BHT extrapolation).

### onepage / WellView

The chain is `XAxisDict`/`DepthDict`/`LabelDict` → `wellview.Layout` → `wellview.Builder` → `WellView`. Only `WellView` knows about the LAS file; `Builder` only builds axes. `wellview/_unary.py` holds rounding helpers (`decimals`, `ceil`, `floor` at the first significant digit) used by `XAxisDict`.

**`Layout`** holds three kinds of validated frozen-dataclass config, accepting either the dataclass or its keywords:
- `XAxisDict`: one per track, set with `wv.set(i, limit=, scale='linear'|'log10', major=, minor=, grid=)`.
  - A left limit larger than the right flips the track.
  - On linear tracks, `minor` defaults to a tenth of the range floored at its first significant digit, and `major` to 5 × minor (10/50 for 0–150).
  - On log10 tracks, majors fall on decades and `minor` is the tuple of decade multiples (default 1–9).
- `DepthDict`: `limit` in either order, stored as (base, top) y-limits; `major`/`minor` tick spacing; `spot`, the depth-track indices, which get inward ticks instead of grid lines; and `grid` (bool), depth grid lines in the other tracks, if the track's own `grid` is on.
- `LabelDict`: the header. `spot` is `'top'`, `'bottom'` or `None`; `major` is the row height per curve; `limit` defaults to `(0, ncycle*major)`, set by `Layout`.

Its sizing rules:
- `widths` accepts length 1, length 2 (depth-track width, other width; default `(2, 4)`) or length `ntrail`.
- `heights` is (header row height, height per depth unit). `height_ratios` turns it into the GridSpec row ratios (header × `ncycle`, depth span) in figure order for the label spot.
- `ntrail`/`ncycle` are read-only.

**`Builder.__call__(figure)`** adds a GridSpec with one body axis per track and, unless `label.spot` is None, one head axis. It keeps them in `heads`/`bodies` and returns them head-then-body.
- A bottom header has its y axis flipped, so row 0 sits next to the track.
- Tick labels are hidden; `WellView.add_depths` writes the depth numbers.

**`WellView(las, **layout_kwargs)`** (`_wellview.py`, 4-space indentation; user reference in `doc/wellview.md`): call `wv(figure)` (it returns the view) before any `add_*`. `label(i)` is `heads[i]` and `stage(i)` is `bodies[i]`.
- **Header rows:** each `add_*` takes a header row through `_row(index, cycle)`, which records the rows used per track (`_rows`).
  - `cycle=True` takes the next free row, an int takes that row (0 = next to the track), and `False` takes none.
  - A row ≥ `ncycle` warns. Header entries are skipped when `label.spot` is None.
  - `_row_y(row, fraction)` gives screen-upward positions for both top and bottom headers.
- **Positioning:** header text and track-wide items (tops, perfs, casings, depth labels) use `_across(axis)`, a blended transform with x in axes fraction and y in data. That keeps them right on log and flipped tracks. Track-edge values come from `self[i].limit` (left, right).
- **Curves:** `multp`/`shift` plot `value*multp + shift`. Cut-offs (`add_cut`), shade `x2` and `vmin`/`vmax` are in curve units. `add_cut`'s `left`/`right` follow the screen, so they swap on flipped tracks.
- **`add_module(left, right)`:** takes line indices on the track, and `None` means that side's track edge. Plot the curves first.
- **Tops and perforations:** `add_tops` takes a dict, Series or DataFrame (`formation, depth[, facecolor]`) and draws nothing above the first top. `add_perfs` takes `top, base[, date]`, with `year_axis={year: track}`. Both fill full-width with `axhspan`.
- **Casings and depths:** `add_casings` takes `od, base[, top]`. `add_depths(i, survey=)` labels MD or TVD and writes the print scale.
- **Pages:** drawing methods are wrapped by `@_drawing`, which records the outermost call in `_calls`. `page(top, base)` copies the view with a new `DepthDict` window and replays the calls on a new figure, so motifs are re-tiled. `save(path, step=)` writes such pages to a PdfPages PDF. Anything drawn directly on `stage(i)` is not replayed.

**Fills** are in `_pigment.Pigment`, static methods that draw in data coordinates with depth on y:
- `fill_solid(axis, y, x1, x2, motifs=, **kwargs)` passes every other keyword to `fill_betweenx`, so `where=`/`interpolate=` shade crossovers and `label=` reaches the legend. It then calls `add_motifs` and returns the fill.
- `add_motifs(axis, fill, motifs)` tiles one motif or several inside any fill: the result of `fill_between`/`fill_betweenx`, or a patch in any coordinates of the axis. It is used by `WellView.add_module`, which also draws motifs in the header box, and by `CrossView.add_formation(..., motifs=)`.
- `motif_patch` first applies pending autoscaling and aspect, then tiles only the part of the region **inside the axes**, and clips to the region and the axes box. Each motif becomes **one** compound `PathPatch`, clipped to every polygon of the fill (NaN gaps split a fill into several). It is added with `add_artist`, so it doesn't widen the data limits, at the fill's zorder.
- `fill_colormap` colours each depth by the curve value, on a log colour scale on a log track. It is used by `WellView.add_shade` and `CrossView.add_gradient`.
  - It resamples the curve onto a regular depth grid at the finest sample spacing, so descending or uneven depths are fine.
  - It builds an `AxesImage` directly; `imshow` would reset the limits (un-inverting depth axes) and the aspect.
  - It clips the image to the `fill_betweenx` outline, so NaN gaps stay empty.

**Fill styles** (`_templix.py`):
- `FillStyle` is a frozen, validated dataclass (`facecolor`, `hatch`, `motifs`, `label`) that unpacks with `**`, so `**Lithology.limestone` goes straight into `Pigment.fill_solid`, `WellView.add_module` (the header title defaults to the label) or `CrossView.add_formation`.
- `StyleTable` instances hold the styles. Names are looked up regardless of case, spaces, hyphens or underscores (`Lithology["cherty dolomite"]`, `Lithology.cherty_dolomite`), with close-match suggestions on a `KeyError`. `plot_key(names or rows)` draws a labelled key.
- The tables:
  - `Lithology` follows the standard graphic lithology key (20 rock types), plus `matrix`, `shale free` and `salt`. Mixed rocks combine motifs; dolomitic limestone uses a private pink "dolomite bricks" motif aligned with `Motifs.brick`.
  - `Mineral` is for multimineral volume tracks.
  - `Porespace` is for porosity and saturation tracks.

**Motifs** (`_motifs.py`):
- `MotifPattern` is a frozen dataclass.
  - Sizes are in **points**, not data units, so a pattern looks the same on any track and depth range. Data-unit sizes rendered solid black over long intervals.
  - Of each pair (`length_ratio`/`length_extern`, `height_ratio`/`height_extern`, `tilted_ratio`/`tilted_length`), give at most one; the other is derived.
  - Elements: `circle`, `ellipse`, `line` (may be vertical, with `length=0`), `cross`, `triangle` and `quadrilateral`.
  - `path(x0, x1, y0, y1, anchor)` tiles a box with every other row staggered by `offset_ratio` of a cell. `shift_ratio` moves the whole grid, e.g. to put ticks in the gaps of the shale dashes. Grids are anchored to the axes origin, so separate fills line up.
- `Motifs` holds the shared, immutable instances (`brick`, `rhomb`, `shale`, `chert`, `irons`, `tick`, `slant`, `plus`, `ooid`). Look them up with `get` / `names` / `items`.
- Motifs are converted with the axes' current limits and size, so set the limits before filling. WellView's `Builder` does this.

### onepage / CrossView

Setup takes three steps:
1. `CrossView(*wells, figsize=)`.
2. `.set(**gridspec_kwargs)` builds a 2×3 frame: west/head/east above depth/scene/litho.
3. `cv(nwells, xpad=, ypad=)` creates a `crossview.Booter` with one inset axis per well inside the scene axis.

Plotting:
- Per-well data goes on `cv.scene[i]`.
- `add_curve(i, x, depth, ylabel, key=)` also draws a legend line on the scene axis at y fraction `ylabel`.
- `add_top/add_formation` map depths to scene coordinates through `Booter.ylocs`.
- Those two methods expect each well object to expose `.tops[key]` and `.tops.limit(key)`, but no such class exists in the package. The old `Formation` class (removed in commit 07046bd) stored tops per formation *across* wells, not per well.

### insight

Standalone model classes with lowercase names (`archie`, `gammaray`, `simandoux`, …) that operate on numpy arrays.

- Shaly-sand models take an `archie` instance for a/m/n, e.g. `simandoux(archie(m=2)).sw(phi, vsh, rw, rsh, rt)`.
- Implicit models (simandoux, totalshale, dualwater, dispersed/Bateman) solve each depth sample with `scipy.optimize.root_scalar` (Newton, `x0=1`).
- Every shaly-sand model must reduce to Archie at Vsh=0 (or Swb=0). This is a useful correctness check.
- `@trim` (`insight/_trim.py`) clips the result to `[lower, upper]` (default 0–1) and adds those kwargs to the call.
- Matrix constants (DTma, rhoma, and phima for each neutron tool) live in `lithology/_lithology.json`. They are not yet wired into the crossplot classes (`neuden`, `mnplot`, `sonneu`).
- Many insight modules still import `trim` from `borepy.utils._wrappers`, an old package name. They need `insight/_trim.py` instead.
- `insight/__init__.py` is empty and several subfolders have no `__init__.py` (namespace packages). Import by full module path.

### digitize

`digitize(scan, curves=[Curve(name, vmin, vmax, unit=, scale=, color=, track=, track_edges=), ...], ...)` (`_digitize.py`) digitizes several curves in one call; `curve=, vmin=, vmax=, color=, ...` is the one-curve shorthand (`_curve_list`). It returns a `DigitizeResult`:
- `.las`: a `WellLog` with DEPT and one column per curve. Each curve's description records its colour and scale.
- `.qc` (`QC`), page-level fields:
  - detected `tracks`, depth source and fit;
  - `depth_labels` with `depth_inliers`/`depth_residuals`/`depth_rms`, `label_columns`;
  - `warnings`, per-curve ones prefixed `NAME:`.
- `.qc.curves`: one `CurveQC` per curve (track edges and source, scale, grid, rows found/bridged/ambiguous, coverage). `qc.track`/`track_source`/`scale`/`grid`/`coverage` are shortcuts to the first curve.
- `.images`: "page", "depth_labels", and per curve `mask_`/`track_`/`track_mask_`/`curve_overlay_<NAME>`.
- `.raw`: `{name: Reading(depth, value, bridged)}` before resampling. `.depth`/`.value` are the first curve's.

`.save(dir)` writes `<name>.las`, `<name>.csv` (long format: curve, depth, value, bridged), one PNG per image and `qc.json`. The pipeline:
1. Render the PDF page with pypdfium2 at `Settings.render_scale`. All pixel positions (`track_edges`, `(row, depth)` pairs, `QC`) are on this rendered page.
2. Mask each curve's colour (`curve_mask(bgr, color)`):
   - **Coloured curves** match by hue (`hue_tolerance`, with `min_saturation`/`min_value`), so faded ink still counts.
   - **Black and grey** (saturation below `GRAY_SATURATION`, `Curve.dark`) match by darkness (`gray_saturation`, `gray_tolerance`).
   - **Specks** under `min_blob` pixels are dropped by connected-component area. There is no morphological opening: it erased thin vertical strokes.
   - **Mistakable colours:** a light red grid matches red too, and is removed later by its shape. Colours too light to tell from the paper are rejected.
3. Find the tracks (`find_tracks(page, curve=all masks, exclude=coloured masks)`):
   - **Lines:** long vertical lines are runs of columns whose line ink covers `min_line_fraction` of the page height. Line ink is pixels `ink_contrast` darker than the paper, minus `exclude`. Only coloured curves are excluded, because black ones share the frames' colour.
   - **Frames vs grid:** the darkest lines are frames, lighter ones grid (`frame_tolerance`).
   - **Tracks:** a span between neighbouring frames is a track if it holds grid lines, horizontal grid lines running across it (`_crossed`), or curve pixels in ≥ 30 % of its rows. Without that 30 % rule, the black depth labels of a black-curve page made the depth column a track. This skips the depth column and margins, and separates tracks sharing a frame.
   - **Uniform darkness:** when every line is as dark as the frames, a track is a run of lines whose gaps are all crossed by horizontal lines. With a shared frame and uniform darkness, contiguous tracks merge.
   - **Edges** are the frame centres, to sub-pixel accuracy.
   - **Choosing:** each curve's `track` picks one: "auto" (default; most pixels of its colour between the frames, with a warning when two tracks are close), "left", "right" or an index. Its `track_edges` override all of this.
   - **No tracks found** raises `DigitizeError`; there is no fallback.
   - **Grid check:** `grid_kind` reads the grid as linear (even spacing) or log10 (spacing shrinking within each decade). A mismatch with `scale` adds a warning; the grid never changes the values.
4. Calibrate depth, either manually or by OCR:
   - **Manual:** `depth=(top, base)` (the first and last page rows) or two or more `(row, depth)` pairs.
   - **OCR, where:** `find_depth_labels` reads every `label_bands` band (gaps between tracks and the margins, or `label_columns`) and keeps the band whose numbers best agree.
   - **OCR, how:** `read_labels` finds text blobs: ink with full-width lines removed, characters merged sideways, height within `min_label_height`–`max_label_height`. It enlarges each to about 32 px and reads them all in **one** Tesseract call on a stacked sheet (psm 6, whitelist `0-9.-`), parsed by `_parse_number`.
   - **Snapping:** each label's row is snapped onto the horizontal grid line it marks (`_grid_rows`, half the ink contrast, ≥ 80 % of a track's width), when one is within half its text height. Text centres sit about 2 px off their line, and snapping removed a 0.14 % depth error.
   - **Fit:** `fit_depth` is a robust fit. Every pair of labels proposes a line with `a > 0`; the line with the most labels within `label_tolerance` rows wins and is refitted by least squares. At least `min_labels` (3) must agree.
   - **Warnings:** misreads are listed; also fewer than 4 labels, or label RMS above 1.5 rows (a stretched scan).

   A failed calibration raises `DepthCalibrationError`, whose `.images` holds the QC images made so far, including `depth_labels` (boxes green or red, with each label's fitted depth). It never falls back to pixel depths. `find_tesseract` checks `Settings.tesseract`, `TESSERACT_CMD`, the PATH, then the Windows install folders.
5. For each curve, in its track crop:
   - **Clean** (`clean_track_mask`): drop rows ≥ 70 % covered (lines across the track); drop full-height lines when there are three or more (a grid in the curve's colour, while a lone one may be a constant curve); drop the frame columns for dark curves; drop specks.
   - **Follow** (`trace_curve`): in each row, join runs closer than 3 px. One run is taken as is; with several, the run nearest the neighbouring rows' column wins (forward then backward pass). Rows with several runs are counted, and more than 10 % warns that a same-colour curve may be mixed in. That is out of scope.
   - **Bridge** (`bridge_gaps`): gaps up to `max_gap` rows (dashes, another curve drawn on top) are interpolated and marked `bridged`; longer gaps stay empty.
   - **Map** (`map_x_to_value`): columns to values across the exact edges, linear or log10; vmin > vmax flips the track.
6. Resample all curves onto one regular depth grid (`resample`, step 0.1524 m / 0.5 ft), leaving NaN where neighbouring readings are more than `max_gap + 1.5` rows apart, and build the `WellLog` through lasio.

`_cli.py` is the thin `pphys-digitize` / `python -m pphys.digitize` wrapper. `utils.resample` is a separate, unused smoothing-spline resampler.

**Measuring accuracy** (`_synthetic.py`, `scorecard.py`):
- `synthetic_scan(path, tracks=, depth=, defects=, ...)` draws a page with matplotlib (Agg, no pyplot): `SyntheticTrack`s holding `SyntheticCurve`s (linear or log10, any colour, values as an array, a function of depth, or random smooth), a depth column with labels, a grid, and optional `Defects` (fade, tint, rotation, blur, noise, JPEG). It returns a `SyntheticScan` with the truth:
  - `values`, `track_columns`, `depth_fit`;
  - helpers `track_edges(curve, render_scale)` and `depth_pairs(render_scale)` that feed `digitize`.
- Pages are drawn at 144 dpi and saved as a **lossless** PDF through pypdfium2 (Pillow would JPEG-compress them), so `render_scale=2.0` reproduces the drawn pixels exactly. Truth positions are pixel indices (pixel i covers [i, i+1)).
- `score(result, scan)` returns RMS/max value error in percent of the track width (in log space on log10 tracks), coverage, and the largest depth error in percent of the span. Coverage is the percent of page rows where the curve was found (bridged rows included), from `result.raw[name]`, before resampling. `TARGET` is the agreed threshold: 1 / 3 / 98 / 0.5.
- `scorecard.SCENARIOS` lists the pages. `gap` names the roadmap step expected to fix a failing one; the tests mark those as `xfail(strict=True)`, so a fix fails until its `gap` is removed. Run `uv run python -m pphys.digitize.scorecard [--keep DIR] [NAME ...]`.

Known prototype weaknesses (roadmap milestone 3), each shown by a scenario:
- Tracks can't be found on a rotated page (`rotated`; deskewing isn't planned).
- On noisy or faded pages the grid lines fall below `ink_contrast`, so the grid check stays silent; the frames are still found.
- OCR assumes one straight depth line per page; real scans with paper stretch show up only as label scatter (a warning), not as corrected depths. Tesseract 5.4 is installed in `C:\Program Files\Tesseract-OCR`.
- Curves of one colour in one track are not told apart (`same_colour_track`, not planned); the trace follows whichever run it started on, and a warning flags it.
- The command line digitizes one curve per run; several curves need the Python `curves=` list.

### Web apps (GitHub Pages)

`index.html` (the app hub) and `pages/*.html` (the apps) are standalone vanilla-JS pages, styled like jshiriyev.github.io. They live outside `pphys/`, so they are not packaged.
- **Publishing:** `.github/workflows/pages.yml` publishes them to https://jshiriyev.github.io/formation-evaluation/ on pushes to main that touch them.
  - The site mirrors the repository paths, so relative links work the same on Pages and from `python -m http.server` at the repo root.
  - Only `index.html`, `pages/*.html` and `notebooks/tutorial_3_graph_2.LAS` are published. Any other linked file must be added to the "Assemble the site" step.
  - The workflow fails if a relative `href`/`src` or a `*_URL = '...'` constant in any published page points to a missing file.
- **Adding an app:** put the page in `pages/` and copy an `app-card` in `index.html`; `tone-onepage`/`tone-digitize`/`tone-insight` name the pphys feature.

**WellView configurator** (`pages/onepage-wellview.html`): a wizard that walks through a WellView set-up and draws nothing.
- It reads the LAS header, curves and statistics in the browser. Its sample is `../notebooks/tutorial_3_graph_2.LAS`. Curve families are a JS port of `_families.py`, so keep the two in step.
- It builds a JSON payload that mirrors the WellView API (`layout` including `xaxes`, then `calls` of `{method, args, kwargs}`, then `output`). The contract is documented in the comment at the top of its script.
- With `API_BASE = ''` it only `console.log`s the payload; setting `API_BASE` POSTs it together with the LAS file.
- A payload from it has been replayed through WellView successfully, so a backend only needs to resolve `{"style": "Table.name"}`, turn table records into DataFrames and convert `year_axis` keys to int.

## Conventions

- Indentation varies by file:
  - Tabs: `digitize/utils.py`, `insight/permeability/_resistivity.py`, `insight/saturation/shalyform/*`, `onepage/_crossview.py`, `onepage/crossview/*`, `onepage/wellview/*`.
  - 4 spaces: everything else.

  Match the surrounding block. Inconsistent mixing raises `TabError`.
- Formatting is `ruff format` with quotes preserved, run through `uv run python .claude/hooks/fmt.py [paths]` (`--check` to verify). It keeps each file's indentation; bare `ruff format` would turn the tab files into spaces.
- `import numpy` and `import numpy as np` both appear; follow the file.
- Implementation lives in `_private.py` modules and is re-exported from the package `__init__.py`.
- Frozen dataclasses set derived fields only through `object.__setattr__` in `__post_init__`.

## Claude Code setup (`.claude/`)

- `settings.json` (committed) holds the deny rules and the hooks; `settings.local.json` (git-ignored) holds a personal allow list.
  - Denied: force pushes, `reset --hard`, `clean -f`, `branch -D` and similar; pushes to `main` (they deploy Pages); bare `python`/`pip`/`pytest` (use `uv run`).
- Hooks (`.claude/hooks/`, stdlib Python run through `uv run --no-sync`, so run `uv sync` once after cloning):
  - `pre_tool.py`: denies any `git push` that would update `main` or force; asks before running or editing the stale `notebooks/*.py`.
  - `post_edit.py`, after a Write/Edit of a `pphys/` or `tests/` `.py` file: syntax and mixed-indentation check, new undefined names (F821, compared with HEAD) block, `fmt.py` formats, the related tests run (map in `TESTS`). Editing `_families.py` or the families block of `pages/onepage-wellview.html` reports the differences from the other side (`families_sync.py`). Editing `index.html`, `pages/*.html` or `pages.yml` runs the published-link check (`check_links.py`, same rule as the workflow).
  - `stop_tests.py`: at the end of a turn, runs the full `pytest` if `pphys/` or `tests/` changed since the last run; a failure sends Claude back to fix it (at most three rounds).
- Skills: `/check` (pre-push gate), `/rerun-notebook`, `/reproduce-figure`, `/new-app`, `/digitize`, `/update-docs`, `/fix-insight-imports`.
- Agents: `petrophysics-reviewer` (insight equations, read-only), `plot-qa` (renders and inspects figures), `web-app-reviewer` (pages, read-only), `test-writer` (tests only).
