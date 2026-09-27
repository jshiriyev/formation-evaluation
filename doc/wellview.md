# WellView: one-page log displays

`pphys.onepage.WellView` draws a well's logs on one page, in the style of a print from a logging company. It uses side-by-side tracks, a header listing every curve with its scale, and a shared depth axis. It covers the usual contents of such a print:
- measured and true vertical depths;
- curves on linear or logarithmic tracks, including flipped ones;
- cut-off shading, colour-map shading, and lithology or volume fills between curves;
- formation tops, perforations and casing.

Everything is drawn with matplotlib, so the figure can be adjusted, combined or saved like any other.

Worked examples:
- [`notebooks/wellview_onepager.ipynb`](../notebooks/wellview_onepager.ipynb): a complete one-pager and every feature on its own;
- [`notebooks/fill_styles.ipynb`](../notebooks/fill_styles.ipynb): the lithology, mineral and pore-space fill styles.

## Quick start

```python
from matplotlib import pyplot as plt
from pphys import read
from pphys.onepage import Lithology, WellView

view = WellView(read("well.las"), ntrail=4, ncycle=3, depth={"limit": (1500, 1600)})
view.set(1, limit=(0, 150))                       # gamma ray
view.set(2, limit=(0.2, 2000), scale="log10")     # resistivity
view.set(3, limit=(1.95, 2.95))                   # density

view(plt.figure(figsize=(8, 10)))                 # build the tracks
view.add_depths(0)
view.add_cut(1, "GR", 60, left=Lithology.sandstone, right=Lithology.shale, color="green")
view.add_curve(2, "RT", color="black")
view.add_curve(3, "RHOB", color="red")
view.add_curve(3, "NPHI", multp=-1 / 0.6, shift=2.7, color="blue")   # neutron on the density scale

view.save("well.png", dpi=200, bbox_inches="tight")
```

In Jupyter, end a drawing cell with `;` or an assignment, so the returned artist is not printed.

## How it is put together

A one-pager is put together in three steps; only the last one knows about the LAS file.

```
XAxisDict (one per track) ─┐
DepthDict (depth window)  ─┼─> Layout ─> Builder ─> WellView <── LAS file
LabelDict (header rows)   ─┘   (sizes)   (axes)     (draws)
```

| Class | Role |
|---|---|
| `XAxisDict` | One track's horizontal axis: range, linear or log10 scale, grid spacing |
| `DepthDict` | The depth window shared by all tracks, its tick spacing and the depth tracks |
| `LabelDict` | The header: row height, position (top, bottom or none) |
| `Layout` | Holds the three and sizes the tracks (`widths`, `height_ratios`) |
| `Builder` | Turns a Layout into matplotlib axes, one header axis and one track axis per track. It has no well data |
| `WellView` | A Builder with a LAS file, and the methods that draw on the tracks |

`Layout` and `Builder` are in `pphys.onepage.wellview`, together with the three settings classes. A Builder can be used alone, e.g. for a blank log form: `Builder(ntrail=5)(plt.figure())`.

## Layout

```python
WellView(las, ntrail=3, ncycle=3, label=None, depth=None, widths=None, heights=None)
```

| Parameter | Meaning |
|---|---|
| `las` | The log, e.g. from `pphys.read`. Curves are plotted against its depth index |
| `ntrail` | Number of tracks, depth tracks included |
| `ncycle` | Number of header rows per track, i.e. the most entries a track lists |
| `label` | The header: a `LabelDict` or its keywords (below) |
| `depth` | The depth window: a `DepthDict` or its keywords (below) |
| `widths` | Track widths: one value for all tracks; two for (depth tracks, other tracks); or one per track. Default `(2, 4)` |
| `heights` | (height of one header row, height per depth unit). They set the proportions of the header and the tracks. Default `(50, 20)` |

The widths and heights are relative; the figure size decides the actual size. For example, 12 tracks with `ncycle=4`, a 110 m window and `heights=(8, 1)` give a header of 4 × 8 = 32 units over 110 units of tracks. `view.widths` and `view.height_ratios` show the result. `ntrail` and `ncycle` cannot be changed after creation.

### Tracks: `view.set(index, ...)`

Each track has an `XAxisDict`, set with `view.set(index, **keywords)` and read with `view[index]`.

| Keyword | Default | Meaning |
|---|---|---|
| `limit` | `(0, 20)` linear, `(1, 100)` log10 | (left, right) values. A left value larger than the right flips the track, e.g. `(0.45, -0.15)` for neutron porosity |
| `scale` | `"linear"` | `"linear"` or `"log10"`. A log10 track needs positive limits |
| `minor` | a tenth of the range, rounded down at its first significant digit | Linear: spacing of the minor grid lines (10 for 0 to 150, 0.1 for 1.95 to 2.95). Log10: the multiples of each decade that get a line, default 1 to 9 |
| `major` | five minor spacings | Linear: spacing of the major grid lines (50 for 0 to 150). Log10: unused, the major lines fall on the decades |
| `grid` | `True` | Draw grid lines along and across the track. Turn it off for tops, lithology, perforation and casing tracks |

### Depth window: `depth={...}`

| Keyword | Default | Meaning |
|---|---|---|
| `limit` | `(0, 100)` | Top and base of the window, in either order. Depth always increases downwards |
| `major`, `minor` | `10`, `1` | Spacing of the depth ticks and depth grid lines |
| `spot` | `(0,)` | Indices of the depth tracks. They get inward depth ticks instead of grid lines, and the first value of `widths=(a, b)` |
| `grid` | `True` | Depth grid lines in the other tracks, where the track's own `grid` is on |

### Header: `label={...}`

| Keyword | Default | Meaning |
|---|---|---|
| `spot` | `"top"` | `"top"`, `"bottom"` or `None` for no header |
| `major` | `10` | Height of one row, in header units |
| `limit` | `(0, ncycle * major)` | Vertical range of the header axes. The default gives exactly `ncycle` rows |

## Building the figure

```python
view(figure)            # returns the view
view.stage(index)       # the track's axes: curves, fills, anything matplotlib draws
view.label(index)       # the track's header axes
view.figure, view.heads, view.bodies
```

Calling the view builds the tracks on a figure, or on a subfigure. Build before drawing: every `add_*` method needs the axes. `stage(i)` shares the track's x range and scale, so extra matplotlib artists can be drawn in track units. `label(i)` also shares the track's x axis, with header units vertically.

### Header rows: `cycle`

Every track has `ncycle` header rows, numbered from the track outwards: row 0 is next to the track, above it with a top header and below it with a bottom one. Each header entry takes one row, chosen with `cycle`:

| `cycle` | Row |
|---|---|
| `True` (default) | The next free row of the track |
| an integer | That row |
| `False` | No header entry |

An entry beyond the last row would be invisible, so it raises a warning. Increase `ncycle` or pass `cycle=False` for it. Without a header (`label={"spot": None}`), header entries are skipped.

## Drawing

| Method | Draws | Returns |
|---|---|---|
| `add_depths(i, survey=None, title=None, cycle=True, scale=True, **text)` | Depth values down a depth track, MD or TVD | |
| `add_curve(i, mnemo, multp=1, shift=0, cycle=True, title=None, **line)` | A curve and its header row | `Line2D` |
| `add_curve_legend(i, mnemo, multp=1, shift=0, cycle=True, title=None, **line)` | A curve's header row only | |
| `add_cut(i, mnemo, cut, multp=1, shift=0, left=None, right=None, cycle=True, title=None, **line)` | A curve, shaded either side of a cut-off | `Line2D` |
| `add_shade(i, mnemo, x2=0, multp=1, shift=0, cycle=True, colormap="Reds", vmin=None, vmax=None, title=None, **image)` | A colour fill that follows the curve | `AxesImage` |
| `add_module(i, left=None, right=None, cycle=True, title=None, **style)` | A fill between two plotted curves, or a curve and a track edge | the fill |
| `add_tops(i, tops, title=None, text_dict=None, **patch)` | Coloured formations with their names | |
| `add_perfs(i, perfs, year_axis=None, date_text_dict=None, date_text_coeff=1, sep_line=False, title=None, **patch)` | Perforated intervals with their dates | |
| `add_casings(i, casings, title=None, **line)` | Casing walls, shoes and diameters | |
| `add_title(i, text, rotation=90, **text)` | A title across a track's whole header | |

### Curves: `add_curve`

The header row shows:
- the curve's line, in the curve's colour and twice as thick;
- its name (the mnemonic, or `title`) and unit;
- the curve values at the left and right edges of the track.

Keyword arguments are matplotlib line properties.

`multp` and `shift` plot `value * multp + shift`, to put a curve on another track's scale, and the header shows the curve's own values at the edges. The standard neutron-density overlay puts neutron porosity (v/v) on a 1.95–2.95 g/cc density track, with 0.45 at the left edge and -0.15 at the right:

```python
view.add_curve(3, "NPHI", multp=-1 / 0.6, shift=2.7)     # header: 0.45 ... -0.15
```

A missing mnemonic raises a `KeyError` listing the curves in the file.

### Cut-offs: `add_cut`

```python
view.add_cut(1, "GR", 60, left=Lithology.sandstone, right=Lithology.shale, color="green")
```

This plots the curve and fills between it and the cut-off:
- `left` where the curve lies left of the cut-off on screen;
- `right` where it lies right of it.

On a flipped track, left means higher values. The cut-off is in curve units. Each side takes a fill style: a dict such as `{"facecolor": "gold", "alpha": 0.6}`, or a `FillStyle` from `Lithology`, `Mineral` or `Porespace`, motifs included. The header row is split at the cut-off into the two styles, under the curve's legend.

### Colour shading: `add_shade`

```python
view.add_shade(2, "RT", x2=0.2, colormap="coolwarm", vmin=1, vmax=1000)
```

This fills between the curve and the baseline `x2`, colouring each depth by the curve's value there.
- **Colour scale:** `vmin` and `vmax` set its ends in curve units; the default is the curve's range. On a log10 track the colour scale is logarithmic too.
- **Header:** its row is a colour bar. Each position has the colour that a curve value there would get, with `title` (default the mnemonic) on top.
- **Curve:** it isn't drawn; add it with `add_curve`, usually after the shade so it sits on top.

The fill is resampled onto a regular depth grid, so uneven sampling is fine, and missing values leave gaps.

### Fills between curves: `add_module`

`left` and `right` are the lines already plotted on the track, by their order of plotting (0 is the first). `None` stands for the track's left or right edge.

```python
view.add_curve(4, "CALI"); view.add_curve(4, "BS")
view.add_module(4, left=0, right=1, facecolor="tan", title="washout")

view.add_curve(5, "VSH", cycle=False)
view.add_module(5, right=0, **Lithology.shale)          # left edge to VSH
view.add_module(5, left=0, **Lithology.sandstone)       # VSH to the right edge
```

Keyword arguments are a fill style or anything `Pigment.fill_solid` and `fill_betweenx` take. For example, `where=` and `interpolate=True` shade a neutron-density crossover only where it occurs. The header row shows the fill, motifs included, with `title` or else the style's label.

Stacked volumes (a mineral or pore-space track) are cumulative curves plotted with `cycle=False` and one module between each pair. See the notebooks.

### Depths: `add_depths`

- **Values:** writes the major depth values down the track, leaving out those on the window's edges, where they would be cut in half.
- **Header:** reads `MD (m)`, using the unit of the LAS depth index.
- **Print scale:** with `scale=True` and a depth unit of M or FT, the header adds the scale, e.g. `1:500`. It is worked out from the track height on the figure, so it holds for a print at the figure's size.

With `survey=` (a DataFrame with `MD` and `TVD` columns, TVD increasing with MD), the track shows TVD values at their measured depths. Its ticks follow TVD, and the header reads `TVD (m)`. The tracks stay in measured depth.

### Formation tops: `add_tops`

`tops` takes the same forms as `LasView`:
- `{name: depth}`;
- a Series of depths indexed by name;
- a DataFrame with `formation` and `depth` columns, and optionally `facecolor`.

Each formation is coloured from its top to the next top, and the last one to the base of the window. Nothing is drawn above the first top. Colours default to the `tab20` palette. Names are written vertically where they fit, in black or white, whichever reads better. Keyword arguments go to the fills (e.g. `alpha`), and `text_dict` to the names.

### Perforations: `add_perfs`

`perfs` is a DataFrame with `top` and `base` columns and optionally `date`.
- **Intervals:** black by default; keyword arguments are patch properties.
- **Dates:** each interval is labelled in the longest form that fits: `2024-05-17`, `2024-05`, `2024` or `24`. `date_text_coeff` above 1 asks for more room.
- **Tracks per year:** `year_axis={2023: 10, 2024: 11}` puts each perforation in the track of its year, as on a completion history. Other years, and intervals without a date, go to the given track.
- **Separators:** `sep_line=True` draws a white line at the top of each interval, to separate adjacent ones.
- **Titles:** `title` labels the header, and with `year_axis`, each year track gets "title year".

### Casings: `add_casings`

`casings` is a DataFrame or a list of dicts with:
- `od`: the outside diameter in inches, a number or text such as `"9 5/8"`;
- `base`: the shoe depth;
- optionally `top`: a liner's hanger depth. Without it, the string runs from above the window.

Strings are nested by diameter, largest outermost, and their spacing is proportional to diameter. Each string is drawn as two walls, with a shoe triangle and the diameter label at its shoe. A string that ends above the window isn't drawn. Keyword arguments are line properties of the walls.

## Drawing straight with matplotlib

`view.stage(i)` and `view.label(i)` are ordinary matplotlib axes, in the track's units, e.g.:

```python
Pigment.fill_solid(view.stage(3), depth, x1, x2, **Lithology.limestone)
view.stage(2).axhline(1712.5, color="red", linestyle="--")
```

These show on the figure, but `page()` and multi-page `save()` do not draw them again (see below).

## Pages and saving

```python
zoom = view.page(1700, 1720)                   # a new WellView of that window
view.save("well.png", dpi=200)                 # the figure as drawn
view.save("well.pdf", step=50)                 # 50 m pages in one PDF
```

`page(top, base, figure=None)` returns a new view of the same layout for another depth window, drawn on a new figure of the same size unless one is given. Everything drawn with WellView methods is drawn again for the new window, so motifs, colour fills, depth labels and text are sized for it. Changing the y limits of the axes instead would stretch the symbols. The original view is not changed.

`save(filepath, step=None, **kwargs)` saves the figure in the format of the file extension; keyword arguments go to `savefig`. With `step`, it writes pages of `step` depth units each to one PDF, from the top of the window down. Every page has the figure's size, so the depth scale is the same on all pages; the last page may run past the base.

## Changes from the earlier WellView

- **`add_module`:** a `None` boundary is now the track edge on that side. It used to be the value 1 for `left` and 0 for `right`, whatever the track range. A fill from the left edge to the first curve is `add_module(i, right=0)`.
- **`cycle`:** numbers header rows from 0 next to the track, the same way for every method. Header entries no longer collide: `True` takes the next free row, not the number of lines on the track.
- **`add_cut`:** takes the cut-off in curve units, and `left`/`right` follow the screen on flipped tracks. The header text is the curve name instead of "Unknown".
- **`add_shade`:** takes `vmin`/`vmax` in curve units, like `x2`.
- **Track-wide fills:** tops and perforations fill the full width of any track. They used to stop at the value equal to the track's span.
- **Draw methods:** they return their main artist. Calling the view returns the view.
- **`show()`:** removed; it did nothing. `save()` and `add_casings()` are now implemented.

## Limitations

- One well per page. To compare wells, use `pphys.onepage.CrossView`.
- Motifs, colour fills and the print scale are laid out for the figure's size and depth window when they are drawn. Set the figure size before drawing, and use `page()` to change the window.
- Header text is sized in points and does not shrink to fit. In narrow tracks or thin rows, widen the track, increase `heights[0]` or use `title=` for shorter names.
- Whether a top name or a perforation date fits is estimated from the font size, not measured.
- The casing sketch is schematic: diameters are relative, and cement, hangers and packers are not drawn.
- A TVD survey must have TVD increasing with MD.
