"""Tests for WellView: header rows, curves, fills, tops, perfs, casings and pages."""

import numpy as np
import pandas as pd
import pytest
from matplotlib import colormaps
from matplotlib import pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.image import AxesImage
from matplotlib.patches import Polygon, Rectangle

from pphys import read
from pphys.onepage import Lithology, Motifs, WellView


@pytest.fixture(scope="module")
def log():
    return read("notebooks/tutorial_6_graph_B.LAS")  # 2028-2082 m: GR, NPHI, RHOB


def build(log, top=2033.0, base=2078.0, **kwargs):
    """Return a built view: depth, density (1.95-2.95) and neutron (0.45 to -0.15)."""
    layout = {
        "ntrail": 3,
        "ncycle": 4,
        "depth": {"limit": (top, base)},
        "widths": (1, 3),
        **kwargs,
    }
    view = WellView(log, **layout)
    view.set(1, limit=(1.95, 2.95))
    view.set(2, limit=(0.45, -0.15))
    return view(plt.figure(figsize=(5.0, 8.0), dpi=72))


def texts(axis):
    return {text.get_text(): text for text in axis.texts}


def row_of(view, text):
    """Return the header row a text sits in."""
    return int(text.get_position()[1] // view._label.major)


# Header rows


def test_entries_take_separate_rows(log):
    view = build(log)

    view.add_curve(1, "RHOB")
    view.add_module(1, left=0, title="sand", facecolor="gold")
    view.add_curve(1, "DRHO", shift=2.5)

    head = texts(view.label(1))
    assert [row_of(view, head[name]) for name in ("RHOB", "sand", "DRHO")] == [0, 1, 2]


def test_explicit_rows_are_skipped_by_the_next_free_row(log):
    view = build(log)

    view.add_curve(1, "RHOB", cycle=1)
    view.add_curve(1, "DRHO", shift=2.5)

    head = texts(view.label(1))
    assert (row_of(view, head["RHOB"]), row_of(view, head["DRHO"])) == (1, 0)


def test_rows_beyond_the_header_warn(log):
    view = build(log, ncycle=1)
    view.add_curve(1, "RHOB")

    with pytest.warns(UserWarning, match="not shown"):
        view.add_curve(1, "DRHO", shift=2.5)


def test_no_header_entry(log):
    view = build(log)

    view.add_curve(1, "RHOB", cycle=False)

    assert len(view.label(1).texts) == 0


def test_layout_without_header_draws_curves(log):
    view = build(log, label={"spot": None})

    view.add_curve(1, "RHOB")

    assert len(view.stage(1).lines) == 1


def test_bottom_header_puts_the_name_above_the_line(log):
    view = build(log, label={"spot": "bottom"})
    view.add_curve(1, "RHOB")
    head = view.label(1)
    name = texts(head)["RHOB"].get_window_extent()
    line = head.lines[0].get_window_extent()

    assert name.y0 >= line.y0 - 1  # on screen, as in a top header


# Curves


def test_edge_values_on_a_flipped_track(log):
    view = build(log)

    view.add_curve(2, "NPHI", multp=0.01, title="NPHI")
    head = texts(view.label(2))

    assert head["45"].get_position()[0] == pytest.approx(0.02)  # left edge value
    assert head["-15"].get_position()[0] == pytest.approx(0.98)


def test_header_follows_the_curve_colour(log):
    view = build(log)

    line = view.add_curve(1, "RHOB", lw=0.8)

    legend = view.label(1).lines[0]
    assert legend.get_color() == line.get_color()
    assert legend.get_linewidth() == pytest.approx(1.6)
    assert texts(view.label(1))["RHOB"].get_color() == line.get_color()


def test_missing_curve(log):
    with pytest.raises(KeyError, match="it has DEPT"):
        build(log).add_curve(1, "RT")


def test_zero_multiplier(log):
    with pytest.raises(ValueError, match="multp"):
        build(log).add_curve(1, "RHOB", multp=0)


def test_use_before_building(log):
    with pytest.raises(RuntimeError, match="figure"):
        WellView(log).add_curve(1, "GR")


# Fills


def test_module_edges_are_the_track_edges(log):
    view = build(log)
    view.add_curve(1, "RHOB")

    left = view.add_module(1, right=0)
    right = view.add_module(1, left=0)

    assert left.get_paths()[0].get_extents().x0 == pytest.approx(1.95)
    assert right.get_paths()[0].get_extents().x1 == pytest.approx(2.95)


def test_module_header_shows_the_fill(log):
    view = build(log)
    view.add_curve(1, "RHOB")

    fill = view.add_module(1, left=0, **Lithology.limestone)

    box = next(p for p in view.label(1).patches if isinstance(p, Rectangle))
    assert box.get_facecolor() == pytest.approx(fill.get_facecolor()[0])
    assert "limestone" in texts(view.label(1))  # the style's label
    assert len(view.label(1).patches) == 2  # the box and its bricks


def test_module_needs_the_curves_first(log):
    with pytest.raises(IndexError, match="plot the curves"):
        build(log).add_module(1, left=0)


def test_cut_fills_the_sides_seen_on_screen(log):
    view = build(log)
    nphi = log["NPHI"] * 0.01

    view.add_cut(
        2,
        "NPHI",
        20,
        multp=0.01,
        left={"facecolor": "red"},
        right={"facecolor": "blue"},
    )
    left, right = view.stage(2).collections

    # on this flipped track, values above the cut lie on the left
    assert left.get_facecolor()[0] == pytest.approx(to_rgba("red"))
    assert left.get_paths()[0].get_extents().x0 >= 0.2 - 1e-9
    assert right.get_paths()[0].get_extents().x1 <= 0.2 + 1e-9
    assert nphi.max() > 0.2 > nphi.min()


def test_cut_header_is_split_at_the_cut(log):
    view = build(log)

    view.add_cut(
        2,
        "NPHI",
        20,
        multp=0.01,
        left={"facecolor": "red"},
        right={"facecolor": "blue"},
    )

    boxes = [p for p in view.label(2).patches if isinstance(p, Rectangle)]
    assert sorted(round(b.get_x() + b.get_width(), 6) for b in boxes) == [-0.15, 0.2]


def test_cut_takes_fill_styles(log):
    view = build(log)

    view.add_cut(1, "RHOB", 2.5, left=Lithology.sandstone, right=Lithology.limestone)

    assert len(view.stage(1).patches) == 1  # limestone bricks
    assert view.stage(1).collections[0].get_hatch() == "..."


def test_shade_colour_limits_are_in_curve_units(log):
    view = build(log)
    view.set(1, limit=(0.0, 150.0))
    view = view(plt.figure(figsize=(5.0, 8.0), dpi=72))

    image = view.add_shade(1, "GR", multp=0.5, vmin=0, vmax=300, colormap="viridis")
    colours = image.get_array()[:, 0]
    gr = log["GR"][(log.index >= 2033) & (log.index <= 2078)]

    expected = colormaps["viridis"](np.nanmax(gr) / 300)
    assert np.abs(colours - expected).sum(axis=1).min() < 0.02


def test_shade_header_shows_the_colours(log):
    view = build(log)

    view.add_shade(1, "RHOB", x2=1.95, colormap="Greens", title="density")

    (bar,) = view.label(1).images
    assert isinstance(bar, AxesImage)
    assert bar.get_array().shape[:2] == (1, 256)
    assert "density" in texts(view.label(1))


# Depths


def test_depth_values_inside_the_window(log):
    view = build(log)

    view.add_depths(0)

    labels = sorted(t.get_text() for t in view.stage(0).texts)
    assert labels == ["2040", "2050", "2060", "2070"]


def test_depth_title_and_print_scale(log):
    view = build(log)

    view.add_depths(0)

    (title,) = view.label(0).texts
    name, scale = title.get_text().split("\n")
    assert name == "MD (m)"
    assert scale.startswith("1:")


def test_tvd_from_a_survey(log):
    view = build(log)
    survey = pd.DataFrame({"MD": [0.0, 3000.0], "TVD": [0.0, 1500.0]})  # 60 degrees

    view.add_depths(0, survey=survey, scale=False)

    values = {t.get_text(): t.get_position()[1] for t in view.stage(0).texts}
    assert values["1020"] == pytest.approx(2040.0)
    assert texts(view.label(0)).keys() == {"TVD (m)"}


# Tops, perforations and casings


def test_tops_span_the_track_whatever_its_scale(log):
    view = build(log)

    view.add_tops(1, {"A": 2040.0, "B": 2060.0})

    spans = view.stage(1).patches
    assert len(spans) == 2
    for span in spans:
        corners = span.get_path().transformed(span.get_patch_transform()).vertices
        assert (corners[:, 0].min(), corners[:, 0].max()) == (0.0, 1.0)  # axes fraction


def test_nothing_above_the_first_top(log):
    view = build(log)

    view.add_tops(1, pd.Series({"A": 2050.0}))

    (span,) = view.stage(1).patches
    assert span.get_window_extent().y1 < view.stage(1).get_window_extent().y1
    assert "Unknown" not in texts(view.stage(1))


def test_tops_colours_and_names(log):
    view = build(log)
    tops = pd.DataFrame(
        {
            "formation": ["A", "B"],
            "depth": [2040.0, 2050.0],
            "facecolor": ["black", None],
        }
    )

    view.add_tops(1, tops, title="Tops")

    black, other = view.stage(1).patches
    assert black.get_facecolor() == to_rgba("black")
    assert other.get_facecolor() == pytest.approx(colormaps["tab20"](1))
    assert texts(view.stage(1))["A"].get_color() == "white"  # readable on black
    assert "Tops" in texts(view.label(1))


def test_tops_need_formation_and_depth(log):
    with pytest.raises(ValueError, match="formation"):
        build(log).add_tops(1, pd.DataFrame({"depth": [2040.0]}))


def test_perforations_by_year(log):
    view = build(log, ntrail=4, widths=(1, 3, 3, 1))
    perfs = pd.DataFrame(
        {
            "top": [2040.0, 2060.0],
            "base": [2050.0, 2062.0],
            "date": ["2023-03-14", "2024-06-02"],
        }
    )

    view.add_perfs(3, perfs, year_axis={2024: 2}, title="Perfs")

    assert len(view.stage(3).patches) == 1  # 2023 stays in the given track
    assert len(view.stage(2).patches) == 1
    assert view.stage(3).patches[0].get_facecolor() == to_rgba("black")
    assert "Perfs" in texts(view.label(3))
    assert "Perfs 2024" in texts(view.label(2))


def test_perforation_dates_shorten_to_fit(log):
    view = build(log)
    perfs = pd.DataFrame(
        {"top": [2040.0, 2060.0], "base": [2050.0, 2063.0], "date": ["2023-03-14"] * 2}
    )

    view.add_perfs(1, perfs)

    written = {t.get_position()[1]: t.get_text() for t in view.stage(1).texts}
    assert written[2045.0] == "2023-03-14"  # 10 m of room
    assert written[2061.5] in {"2023-03", "2023", "23"}  # 3 m of room
    assert all(t.get_color() == "white" for t in view.stage(1).texts)


def test_casings(log):
    view = build(log)
    casings = [
        {"od": 7, "base": 2070.0, "top": 2030.0},  # a liner
        {"od": "9 5/8", "base": 2045.0},
        {"od": 13.375, "base": 2036.0},
        {"od": 20, "base": 1500.0},  # ends above the window
    ]

    view.add_casings(1, casings, title="Casing")
    axis = view.stage(1)

    shoes = [p for p in axis.patches if isinstance(p, Polygon)]
    assert len(axis.lines) == 6  # two walls for each string in the window
    assert len(shoes) == 6
    assert sorted(t.get_text() for t in axis.texts) == ['13 3/8"', '7"', '9 5/8"']
    outer = max(abs(line.get_xdata()[0] - 0.5) for line in axis.lines)
    assert outer == pytest.approx(0.4 * 13.375 / 20)  # sized against the 20 in
    assert "Casing" in texts(view.label(1))


def test_casings_need_od_and_base(log):
    with pytest.raises(ValueError, match="od"):
        build(log).add_casings(1, [{"base": 2045.0}])


# Pages and saving


def test_page_draws_the_same_things_for_another_window(log):
    view = build(log)
    view.add_depths(0)
    view.add_curve(1, "RHOB")
    view.add_cut(2, "NPHI", 20, multp=0.01, left={"facecolor": "red"})

    page = view.page(2050.0, 2060.0)

    assert page.stage(1).get_ylim() == (2060.0, 2050.0)
    assert len(page.stage(2).lines) == len(view.stage(2).lines) == 1
    assert page._calls == view._calls  # add_cut's inner add_curve is not repeated
    assert view.stage(1).get_ylim() == (2078.0, 2033.0)  # the original is untouched


def test_page_sizes_motifs_for_its_window(log):
    view = build(log)
    view.add_curve(1, "RHOB")
    view.add_module(1, left=0, **Lithology.limestone)

    page = view.page(2050.0, 2055.0)
    brick = next(p for p in page.stage(1).patches if not isinstance(p, Rectangle))
    corners = brick.get_transform().transform(brick.get_path().vertices[:5])

    assert np.ptp(corners, axis=0) * 72 / page.figure.dpi == pytest.approx(
        (Motifs.brick.length, Motifs.brick.height)
    )


def test_save_one_figure(log, tmp_path):
    view = build(log)

    view.save(tmp_path / "view.png", dpi=50)

    assert (tmp_path / "view.png").stat().st_size > 0


def test_save_pages(log, tmp_path):
    view = build(log)
    view.add_curve(1, "RHOB")

    view.save(tmp_path / "pages.pdf", step=10)

    content = (tmp_path / "pages.pdf").read_bytes()
    pages = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
    assert pages == 5  # 2033-2078 in 10 m pages


def test_save_before_building(log, tmp_path):
    with pytest.raises(RuntimeError, match="figure"):
        WellView(log).save(tmp_path / "x.png")
