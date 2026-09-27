# LasView: exploring and checking a LAS file

`pphys.LasView` summarizes a single LAS file: what is in it, where each curve has data, whether the file and its curves pass basic quality checks, and what the logs look like. Tables come back as `pandas.DataFrame` objects and plots as `matplotlib` figures, so you can display, filter, save or restyle them.

A worked example on a real cased-hole run is in [`notebooks/lasview_real_field_data.ipynb`](../notebooks/lasview_real_field_data.ipynb).

## Quick start

```python
from pphys import LasView

tops = {"Top A": 1520.0, "Top B": 1604.5}
view = LasView("well.las", tops=tops)

view.summary()              # well identity, header vs data depths
view.inventory()            # one row per curve: unit, family, top, bottom, coverage
view.validate()             # file-level checks: header, depth index, null values
view.quality()              # curve-level checks: limits, spikes, flat lines, gaps

fig = view.plot_coverage()  # where each curve has data
fig = view.plot_logs(["GR", ["RHOB", "NPHI"], "RT"])
view.save_report("well_report.pdf")
```

In Jupyter, assign plots to a variable (`fig = ...`). Otherwise the figure is shown twice: once by the plotting backend and once as the cell's return value.

## Loading a file

```python
LasView(source, tops=None, *, cache_path=None, **read_kwargs)
```

- **`source`**: a path to a LAS file, or a log that is already loaded (`pphys.WellLog` or any `lasio.LASFile`).
  - Paths are read with `pphys.read`, so `cache_path=` and lasio options such as `null_policy="none"` work as usual.
  - A loaded log is used as it is, without copying.
- **`tops`** (optional): formation tops, in the unit of the depth index, given in any of these forms:
  - a dict `{"name": depth}`;
  - a `pandas.Series` of depths indexed by name;
  - a `DataFrame` with `formation` and `depth` columns, the same format `WellView.add_tops` uses.

  Tops are sorted by depth. They label the coverage and log plots and define the zones.

Useful attributes:

| Attribute | Meaning |
|---|---|
| `view.log` | The underlying `pphys.WellLog`, for anything `LasView` does not cover |
| `view.depth`, `view.depth_mnemonic`, `view.depth_unit` | The depth index and its name and unit |
| `view.curves` | Curve mnemonics, excluding the depth index |
| `view.well_name` | `WELL` from the `~Well` section |
| `view.other` | Free text of the `~Other` section (remarks, processing notes) |
| `view.tops` | Tops as a DataFrame sorted by depth |
| `view.family("GR")` | The curve family `LasView` recognized (see [Curve families](#curve-families)) |

## Tables

| Method | Returns |
|---|---|
| `summary()` | Series: well, field, company, service company, date, location, country, LAS version, depth curve and unit, header STRT/STOP/STEP, data top and bottom, median step, samples, number of curves, NULL value |
| `header(section)` | The `"well"`, `"curves"`, `"parameters"` or `"version"` section with `mnemonic`, `unit`, `value` and `description` |
| `inventory()` | One row per curve, depth index first (see below) |
| `statistics(curves=None)` | `unit`, `count`, `mean`, `std`, `min`, `p10`, `p50`, `p90`, `max` per curve, ignoring missing values |
| `intervals(curves=None, min_gap=0)` | Continuous runs of data per curve: `curve`, `top`, `bottom`, `thickness` |
| `gaps(curves=None, min_gap=0)` | Missing intervals inside each curve: `curve`, `top`, `bottom`, `thickness` |
| `zones()` | Formation intervals from the tops: `formation`, `top`, `base`, `thickness` |
| `zone_statistics(curves=None, stat="mean")` | One value per zone and curve. `stat` is any pandas aggregation: `"median"`, `"min"`, `"max"`, `"std"`, `"count"` or a function |

`inventory()` columns:

| Column | Meaning |
|---|---|
| `unit`, `description` | From the `~Curve` section |
| `family` | Recognized curve family, `depth` for the index, empty if unknown |
| `top`, `bottom` | First and last depth with a value |
| `samples` | Number of values (non-null) |
| `coverage` | Fraction of all depths in the file that have a value |
| `gaps` | Number of missing intervals between `top` and `bottom` |

In `intervals()` and `gaps()`, `top` and `bottom` of a gap are the last value above it and the first value below it. `min_gap` is a thickness in depth units:
- `intervals(min_gap=...)` joins runs separated by gaps up to that thickness;
- `gaps(min_gap=...)` reports only thicker gaps.

This replaces the `ignorenansteps` option of the earlier `LasView`, which counted samples instead of depth.

`p10`, `p50` and `p90` are the 10th, 50th and 90th percentiles (low to high), not exceedance probabilities.

## Quality control

### File checks: `validate()`

Returns one row per check with `status` `pass`, `warn` or `fail` and a `detail`.

| Check | Fails or warns when |
|---|---|
| required `~Well` items | STRT, STOP, STEP or NULL is missing (fail) |
| well identification | COMP, WELL, FLD, LOC, SRVC or DATE is empty, or both UWI and API are |
| depth unit | The index unit is not a depth unit (M, FT, F, .1IN, ...) |
| depth values | The depth index has missing values (fail) |
| depth order | Depths repeat or change direction (fail) |
| regular sampling | Depth steps differ from the median step |
| header STEP | STEP differs from the data step. STEP = 0 (irregular sampling) is accepted only if the data are irregular |
| header STRT, STOP | Differ from the first or last depth by more than half a step |
| unique mnemonics | A mnemonic appears more than once |
| curve units | A curve has no unit |
| undeclared null values | The data contain -999.25, -999, -9999, -9999.25 or -99999 while NULL declares something else, so these values were not treated as missing |
| empty curves | A curve has no values at all |
| tops within logged interval | A top lies outside the logged depths (only with tops) |

### Curve checks: `quality()`

```python
view.quality(curves=None, *, spike_threshold=8.0, flat_samples=20)
```

| Column | Meaning |
|---|---|
| `family`, `unit` | Recognized family and curve unit |
| `samples` | Number of values |
| `missing` | Fraction missing between the curve's first and last value |
| `limits` | Physically plausible range for the family and unit, e.g. `[0, 500]` for gamma ray in GAPI. Empty if unknown |
| `below_min`, `above_max` | Number of values outside the limits |
| `spikes` | Number of single-sample spikes |
| `longest_flat` | Longest run of identical consecutive values, in depth units |
| `flags` | Readable summary, or `ok` |

- **Limits** are plausibility bounds, not interpretation cut-offs. A value outside them is physically impossible for that measurement (e.g. negative attenuation, density above 3.3 g/cc), which points to a tool, processing or unit problem.
- **Spikes:** a sample is a spike if it jumps away from both neighbours, in the same direction, by more than `spike_threshold` times the curve's typical sample-to-sample change (the robust standard deviation of the first differences). Smooth peaks spanning several samples are not spikes, so filtered or processed curves are not over-flagged. Lower the threshold to be stricter.
- **Flat lines:** runs of at least `flat_samples` identical values are flagged. They typically mean a stuck sensor, a clipped value or an interpolated gap.
- **Skipped families:** spike and flat-line checks are skipped (`<NA>`) for curves that are spiky or wrap around by design (casing collar locator, azimuths and bearings).

### Curve families

`LasView` recognizes a curve from its mnemonic, compared upper-case with spaces removed (so `Bit Size` matches as `BITSIZE`). If the mnemonic is unknown, it falls back to a unit that identifies the measurement: OHMM means resistivity, GAPI gamma ray, G/CC bulk density, US/F sonic, and DB/F attenuation.

Unit spellings are normalized. For example, `gm/cc`, `g/cm3` and `gram/cc` are all read as G/CC, and `ls-pu` as PU. Limits apply only when the unit is recognized.

| Family | Example mnemonics | Limits | Display |
|---|---|---|---|
| gamma ray | GR, SGR, CGR, HSGR, ECGR, GAMMA* | 0 to 500 GAPI | |
| potassium, thorium, uranium | POTA/K, THOR/TH, URAN/U | 0 to 10 %; 0 to 100 ppm | |
| spontaneous potential | SP, SSP, SPBL | -500 to 500 mV | |
| resistivity | RT, RD, RXO, LLD, LLS, MSFL, ILD, ILM, SFL, AT10 to AT90, AHT*, P*H, RES* | 0.01 to 100 000 ohm.m | log axis |
| bulk density | RHOB, RHOZ, DEN, ZDEN | 1.0 to 3.3 g/cc | |
| density correction | DRHO, HDRA, ZCOR | -0.5 to 0.5 g/cc | |
| neutron porosity | NPHI, TNPH, NPOR, CNC, NEU | -0.15 to 1.0 v/v; -15 to 100 pu | |
| photoelectric factor | PEF, PE | 0 to 10 b/e | |
| sonic | DT, DTC, DTCO, AC, DT* | 40 to 250 us/ft; 130 to 820 us/m | |
| shear sonic | DTS, DTSM, DT4S | 60 to 800 us/ft | |
| caliper, bit size | CALI, HCAL, C1; BS, BIT | 3 to 40 in; 75 to 1000 mm | |
| attenuation (cement bond) | ATAV, ATC1 to ATCn, ATMN, ATMX | 0 to 50 dB/ft | |
| casing collar locator | CCL | none | no spike/flat checks |
| deviation | DEV, DEVI, INCL | 0 to 180 deg | |
| azimuth / bearing | AZIM, HAZI, RB* | 0 to 360 deg | no spike/flat checks |
| tension | TENS, TTEN, CHT | at least 0 | |
| logging speed | SPD, SPEED, CS | at least 0 | |
| temperature | TEMP, MTEM, BHT | -40 to 400 degC; -40 to 750 degF | |
| volume fraction | PHIT, PHIE, SW, VSH, VCL, BVW | 0 to 1 v/v; 0 to 100 % | |

Where patterns overlap, the more specific family wins. For example, DTS is shear sonic rather than sonic, AT90 is resistivity rather than attenuation, and SPD is logging speed rather than SP.

## Zones and windows

```python
view.zones()
view.zone_statistics(["GR", "RHOB"], stat="median")
part = view.window(1500.0, 1650.0)   # a new LasView on that interval, tops kept
part.quality()
```

Each zone runs from its top to the next top; the last one ends at the bottom of the log. In `zone_statistics`, a sample exactly on a top belongs to the zone below it.

## Plots

Every plot method returns a `matplotlib.figure.Figure`. Methods that draw on a single set of axes also accept `ax=`, so the plot can go into a figure of your own.

| Method | What it shows |
|---|---|
| `plot_coverage(scale="events", min_gap=0, depth_format="{:.1f}")` | One vertical bar per curve from first to last value, broken at gaps. Tops are labelled on the right |
| `plot_table(frame=None, title=None, float_format="{:.1f}")` | Any table drawn as a figure; by default the inventory as Curves / Top / Bottom / Description |
| `plot_logs(tracks=None, top=None, base=None, figsize=None)` | Curves against depth, one track per curve or per group, with dashed lines at the tops |
| `plot_histograms(curves=None, bins=50, ncols=4)` | One histogram per curve, P10 and P90 dotted and P50 dashed |
| `plot_crossplot(x, y, color=None, top=None, base=None, cmap="viridis")` | Scatter plot of two curves, optionally coloured by a third (the depth curve works too) |
| `plot_correlation(curves=None, method="pearson")` | Correlation matrix as a heat map. `"spearman"` suits curves related non-linearly |

Notes on the individual plots:
- **`plot_coverage` scales:**
  - `"events"` (the default) gives every depth where a curve starts or stops, and every top, its own evenly spaced row. Small offsets between tools stay readable next to kilometres of log.
  - `"depth"` uses a true depth axis.
- **`plot_logs` tracks:** each item is a mnemonic or a list of mnemonics sharing a track, e.g. `["GR", ["ATMN", "ATAV", "ATMX"], "RT"]`. Resistivity-type curves use a logarithmic axis. `top` and `base` limit the depth range.
- **`plot_table`:** accepts the output of any table method, e.g. `view.plot_table(view.quality(), title="Curve quality")`. A named index, such as `curve`, becomes the first column.
- **Log scales:** resistivity-type curves are shown on logarithmic axes in histograms and crossplots too.

Save any figure with `fig.savefig("name.png", dpi=200, bbox_inches="tight")`.

## Report

```python
view.save_report("well_report.pdf")
```

Writes a multi-page PDF with these pages, in order:
1. summary;
2. file checks;
3. curve inventory;
4. coverage;
5. statistics;
6. curve quality;
7. zones and zone averages (only if tops are given);
8. the log display;
9. histograms;
10. correlation matrix.

## Limitations

- One file at a time. To compare wells, use `pphys.onepage.CrossView`.
- Statistics of angles (azimuths, bearings) are arithmetic, which is misleading for values that wrap from 360 to 0.
- The spike check finds single-sample spikes. Excursions spanning several samples show up in the log and histogram plots instead.
- The LAS format ends a unit at the first space, so a malformed header such as `DEN .gram per cc` gives the unit `gram`. Such curves are recognized by mnemonic but get no limits.
