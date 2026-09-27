"""Tests for the WellView chain: XAxis, Depth, Label, Layout, Builder, WellView."""

import dataclasses

import pytest
from matplotlib import pyplot as plt

from pphys import read
from pphys.onepage import WellView
from pphys.onepage.wellview import Builder, DepthDict, LabelDict, Layout, XAxisDict

# XAxisDict


@pytest.mark.parametrize(
    ("scale", "limit"), [("linear", (0.0, 20.0)), ("log10", (1.0, 100.0))]
)
def test_xaxis_default_limits(scale, limit):
    assert XAxisDict(scale=scale).limit == limit


@pytest.mark.parametrize(
    ("limit", "minor", "major"),
    [
        ((0, 150), 10.0, 50.0),  # gamma ray
        ((0, 1), 0.1, 0.5),  # volume fractions
        ((1.95, 2.95), 0.1, 0.5),  # bulk density
        ((0.45, -0.15), 0.06, 0.3),  # neutron porosity, flipped
        ((-22, 7), 2.0, 10.0),  # spontaneous potential
    ],
)
def test_xaxis_default_grid_spacing_follows_the_range(limit, minor, major):
    xaxis = XAxisDict(limit=limit)

    assert (xaxis.minor, xaxis.major) == (minor, major)


def test_xaxis_given_spacing():
    xaxis = XAxisDict(limit=(0, 150), major=30, minor=5)

    assert (xaxis.major, xaxis.minor) == (30.0, 5.0)
    assert XAxisDict(limit=(0, 150), minor=5).major == 25.0  # five minor spacings
    assert XAxisDict(limit=(0, 150), major=30).minor == 10.0


@pytest.mark.parametrize(
    ("minor", "subs"),
    [
        (None, tuple(float(n) for n in range(1, 10))),
        (1, (1.0,)),
        ((1, 2, 5), (1.0, 2.0, 5.0)),
    ],
)
def test_xaxis_log_minor_multiples(minor, subs):
    assert XAxisDict(limit=(0.2, 2000), scale="log10", minor=minor).minor == subs


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"scale": "log"}, "scale must be one of"),
        ({"limit": (5, 5)}, "two different values"),
        ({"limit": (0, 100), "scale": "log10"}, "positive limits"),
        ({"limit": (0, 1), "minor": -0.1}, "positive"),
    ],
)
def test_xaxis_validation(kwargs, message):
    with pytest.raises(ValueError, match=message):
        XAxisDict(**kwargs)


def test_xaxis_geometry():
    neutron = XAxisDict(limit=(0.45, -0.15))
    resistivity = XAxisDict(limit=(0.2, 2000), scale="log10")

    assert neutron.flipped
    assert not resistivity.flipped
    assert (neutron.lower, neutron.upper) == (-0.15, 0.45)
    assert neutron.middle == pytest.approx(0.15)
    assert resistivity.middle == pytest.approx(20.0)
    assert resistivity.lower_off(25) == pytest.approx(2.0)  # a quarter of 4 decades
    assert resistivity.upper_off(25) == pytest.approx(200.0)


# DepthDict and LabelDict


@pytest.mark.parametrize("limit", [(3200, 3310), (3310, 3200)])
def test_depth_increases_downwards_whatever_the_order(limit):
    depth = DepthDict(limit=limit)

    assert depth.limit == (3310.0, 3200.0)  # (base, top) as y limits
    assert (depth.upper, depth.lower, depth.length) == (3200.0, 3310.0, 110.0)


def test_depth_survives_replace():
    depth = dataclasses.replace(DepthDict(limit=(3200, 3310)), major=5.0)

    assert depth.limit == (3310.0, 3200.0)


def test_depth_spot_accepts_an_integer():
    assert DepthDict(spot=1).spot == (1,)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"limit": (10, 10)}, "two different depths"),
        ({"major": 0}, "positive"),
        ({"minor": -1}, "positive"),
    ],
)
def test_depth_validation(kwargs, message):
    with pytest.raises(ValueError, match=message):
        DepthDict(**kwargs)


def test_label_spot_validation():
    with pytest.raises(ValueError, match="spot must be one of"):
        LabelDict(spot="left")


# Layout


def test_layout_matches_the_one_pager_example():
    layout = Layout(
        ntrail=12,
        ncycle=4,
        label={"limit": (0, 40), "major": 10, "spot": "top"},
        depth={"limit": (3200, 3310), "major": 10, "minor": 2, "spot": (0, 1)},
        widths=(4, 4, 2, 8, 8, 8, 8, 8, 1, 1, 1, 1),
        heights=(8, 1),
    )

    assert len(layout) == 12
    assert layout.shape == (12, 4)
    assert layout.height_ratios == (32.0, 110.0)
    assert layout.size == (54.0, 142.0)


def test_label_limit_defaults_to_one_row_per_cycle():
    assert Layout(ncycle=4)._label.limit == (0.0, 40.0)
    assert Layout(ncycle=4, label={"major": 5})._label.limit == (0.0, 20.0)
    assert Layout(ncycle=4, label={"limit": (0, 70)})._label.limit == (0.0, 70.0)


@pytest.mark.parametrize(
    ("widths", "expected"),
    [
        (None, (2.0, 4.0, 4.0)),  # (depth trails, other trails)
        ((3,), (3.0, 3.0, 3.0)),
        ((1, 2), (1.0, 2.0, 2.0)),
        ((1, 2, 3), (1.0, 2.0, 3.0)),
    ],
)
def test_widths(widths, expected):
    assert Layout(ntrail=3, widths=widths).widths == expected


def test_widths_for_several_depth_trails():
    layout = Layout(ntrail=4, depth={"spot": (0, 2)}, widths=(1, 3))

    assert layout.widths == (1.0, 3.0, 1.0, 3.0)


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"ntrail": 3, "widths": (1, 2, 3, 4)}, ValueError),
        ({"ntrail": 3, "widths": (1, 0)}, ValueError),
        ({"ntrail": 2, "depth": {"spot": (3,)}}, ValueError),
        ({"ntrail": 0}, ValueError),
        ({"heights": (8,)}, ValueError),
    ],
)
def test_layout_validation(kwargs, error):
    with pytest.raises(error):
        Layout(**kwargs)


@pytest.mark.parametrize(
    ("spot", "ratios"),
    [("top", (150.0, 10.0)), ("bottom", (10.0, 150.0)), (None, (10.0,))],
)
def test_height_ratios_follow_the_header_spot(spot, ratios):
    layout = Layout(ncycle=3, label={"spot": spot}, depth={"limit": (0, 0.5)})

    assert layout.height_ratios == ratios  # a 0.5 m window keeps a height


def test_set_and_get_trail_axes():
    layout = Layout(ntrail=2)
    layout.set(1, limit=(0, 150))

    assert layout[1].limit == (0.0, 150.0)
    with pytest.raises(TypeError, match="XAxisDict"):
        layout[1] = {"limit": (0, 1)}


def test_trail_count_is_read_only():
    with pytest.raises(AttributeError):
        Layout().ntrail = 5


# Builder


def figure():
    return plt.figure(figsize=(6.0, 8.0))


def test_builder_needs_no_well_data():
    builder = Builder(ntrail=3, depth={"limit": (1000, 1100)})

    axes = builder(figure())

    assert len(axes) == 6
    assert axes == [
        axis
        for pair in zip(builder.heads, builder.bodies, strict=True)
        for axis in pair
    ]


def test_builder_axes_follow_the_layout():
    builder = Builder(ntrail=2, ncycle=4, depth={"limit": (1000, 1100)})
    builder.set(1, limit=(0.2, 2000), scale="log10")
    builder(figure())

    head, body = builder.heads[1], builder.bodies[1]

    assert body.get_ylim() == (1100.0, 1000.0)  # depth increases downwards
    assert head.get_ylim() == (0.0, 40.0)
    assert body.get_xscale() == head.get_xscale() == "log"
    assert body.get_xlim() == head.get_xlim() == pytest.approx((0.2, 2000.0))


@pytest.mark.parametrize(
    ("spot", "ylim"), [("top", (0.0, 30.0)), ("bottom", (30.0, 0.0))]
)
def test_header_sits_at_its_spot(spot, ylim):
    builder = Builder(ntrail=2, label={"spot": spot}, depth={"limit": (0, 100)})
    builder(figure())
    head, body = builder.heads[0].get_position(), builder.bodies[0].get_position()

    assert body.height > head.height
    assert (head.y0 >= body.y1) == (spot == "top")
    assert builder.heads[0].get_ylim() == ylim  # row 0 next to the track


def test_builder_without_header():
    builder = Builder(ntrail=2, label={"spot": None})

    axes = builder(figure())

    assert builder.heads == []
    assert axes == builder.bodies


def test_builder_ignores_other_axes_on_the_figure():
    canvas = figure()
    other = canvas.add_axes((0.0, 0.9, 1.0, 0.1))
    builder = Builder(ntrail=2)

    axes = builder(canvas)

    assert other not in axes
    assert len(axes) == 4


def test_grid_lines():
    builder = Builder(ntrail=3, depth={"limit": (0, 100)})
    builder.set(2, limit=(0, 1), grid=False)
    canvas = figure()
    builder(canvas)
    canvas.canvas.draw()

    def gridded(axis):
        return (
            any(line.get_visible() for line in axis.xaxis.get_gridlines()),
            any(line.get_visible() for line in axis.yaxis.get_gridlines()),
        )

    depth_trail, curve_trail, lithology_trail = builder.bodies
    assert gridded(curve_trail) == (True, True)
    assert gridded(lithology_trail) == (False, False)
    assert gridded(depth_trail)[1] is False  # depth trails carry ticks instead


def test_depth_grid_can_be_turned_off():
    builder = Builder(ntrail=2, depth={"limit": (0, 100), "grid": False})
    canvas = figure()
    builder(canvas)
    canvas.canvas.draw()

    assert not any(
        line.get_visible() for line in builder.bodies[1].yaxis.get_gridlines()
    )


def test_tick_labels_are_hidden():
    builder = Builder(ntrail=2, depth={"limit": (0, 100)})
    canvas = figure()
    builder(canvas)
    canvas.canvas.draw()

    labels = [
        label
        for axis in builder.heads + builder.bodies
        for label in axis.get_xticklabels() + axis.get_yticklabels()
    ]
    assert not any(label.get_visible() and label.get_text() for label in labels)


# WellView on top of the Builder


@pytest.fixture
def log():
    return read("notebooks/tutorial_1_graph_B.LAS")


def test_well_view_with_default_layout(log):
    view = WellView(log)

    assert view(figure()) is view
    assert len(view.axes) == 6


def test_well_view_label_and_stage(log):
    view = WellView(log, ntrail=2, depth={"limit": (1330, 1380)})
    view(figure())

    assert view.label(1) is view.heads[1]
    assert view.stage(1) is view.bodies[1]


def test_well_view_before_it_is_built(log):
    with pytest.raises(RuntimeError, match="figure"):
        WellView(log).stage(0)


def test_well_view_without_header(log):
    view = WellView(log, ntrail=2, label={"spot": None}, depth={"limit": (1330, 1380)})
    view.set(1, limit=(0, 150))
    view(figure())

    view.add_curve(1, "GAMMATOTAL", cycle=False)

    assert len(view.stage(1).lines) == 1
    with pytest.raises(ValueError, match="no header"):
        view.label(1)
