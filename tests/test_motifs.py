"""Tests for MotifPattern, Motifs and how Pigment draws them."""

import dataclasses
import math
import warnings

import numpy as np
import pytest
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.path import Path

from pphys import read
from pphys.onepage import CrossView, Lithology, MotifPattern, Motifs, Pigment, WellView

# MotifPattern: construction


def test_defaults():
    motif = MotifPattern("quadrilateral")

    assert (motif.length, motif.height) == (12.0, 6.0)
    assert motif.pitch == (12.0, 6.0)
    assert (motif.length_ratio, motif.height_ratio) == (1.0, 1.0)
    assert (motif.tilted_ratio, motif.tilted_length) == (0.0, 0.0)
    assert motif.radius == pytest.approx(math.sqrt(72.0) / 2)


def test_cell_size_from_ratio():
    motif = MotifPattern(
        "triangle", length=5.0, height=4.0, length_ratio=3.0, height_ratio=2.0
    )

    assert motif.pitch == (15.0, 8.0)


def test_ratio_from_cell_size():
    motif = MotifPattern(
        "line", length=8.0, height=0.0, length_extern=16.0, height_extern=5.0
    )

    assert motif.length_ratio == 2.0
    assert motif.pitch == (16.0, 5.0)


def test_tilt_from_ratio_or_length():
    by_ratio = MotifPattern("quadrilateral", length=12.0, tilted_ratio=0.25)
    by_length = MotifPattern("quadrilateral", length=12.0, tilted_length=3.0)

    assert by_ratio.tilted_length == 3.0
    assert by_length.tilted_ratio == 0.25


def test_consistent_pair_is_accepted():
    motif = MotifPattern(
        "line",
        length=8.0,
        height=0.0,
        length_ratio=2.0,
        length_extern=16.0,
        height_extern=5.0,
    )

    assert motif.length_extern == 16.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"length_ratio": 2.0, "length_extern": 10.0},
        {"height_ratio": 2.0, "height_extern": 5.0},
        {"tilted_ratio": 0.5, "tilted_length": 1.0},
    ],
)
def test_inconsistent_pair_raises(kwargs):
    with pytest.raises(ValueError, match="disagree"):
        MotifPattern("quadrilateral", **kwargs)


def test_unknown_element_raises():
    with pytest.raises(ValueError, match="element must be one of"):
        MotifPattern("hexagon")


def test_former_element_name_is_accepted():
    assert MotifPattern("quadrupe").element == "quadrilateral"


@pytest.mark.parametrize(
    ("element", "kwargs", "message"),
    [
        ("quadrilateral", {"length": 0.0}, "length must be positive"),
        ("circle", {"height": 0.0}, "height of a circle"),
        ("line", {"height": -1.0}, "non-negative"),
        ("line", {"length": 0.0, "height": 0.0}, "not both 0"),
        (
            "line",
            {"height": 0.0},
            "height_extern must be positive",
        ),  # needs a row height
        ("quadrilateral", {"length_extern": -1.0}, "length_extern must be positive"),
        ("circle", {"radius": 0.0}, "radius must be positive"),
        ("quadrilateral", {"offset_ratio": math.nan}, "offset_ratio"),
        ("quadrilateral", {"shift_ratio": math.inf}, "shift_ratio"),
        ("ellipse", {"height": 0.0}, "height of a ellipse"),
    ],
)
def test_invalid_sizes_raise(element, kwargs, message):
    with pytest.raises(ValueError, match=message):
        MotifPattern(element, **kwargs)


def test_is_immutable():
    motif = MotifPattern("circle", params={"facecolor": "red"})

    with pytest.raises(dataclasses.FrozenInstanceError):
        motif.length = 1.0
    with pytest.raises(TypeError):
        motif.params["facecolor"] = "blue"


def test_params_are_copied():
    params = {"facecolor": "red"}
    motif = MotifPattern("circle", params=params)
    params["facecolor"] = "blue"

    assert motif.params["facecolor"] == "red"


# MotifPattern: geometry


def symbol_origins(motif, path):
    """Return the lower-left corner of each symbol (polygons and lines)."""
    per_symbol = len(motif._shape()[1])
    return path.vertices[::per_symbol]


def test_path_staggers_every_other_row():
    motif = MotifPattern("quadrilateral", length=12.0, height=6.0, offset_ratio=0.5)
    origins = symbol_origins(motif, motif.path(0.0, 48.0, 0.0, 24.0))

    even = origins[np.isclose(origins[:, 1] % 12.0, 0.0)]
    odd = origins[np.isclose(origins[:, 1] % 12.0, 6.0)]

    np.testing.assert_allclose(even[:, 0] % 12.0, 0.0, atol=1e-9)
    np.testing.assert_allclose(odd[:, 0] % 12.0, 6.0, atol=1e-9)


def test_path_follows_the_anchor():
    motif = MotifPattern("quadrilateral", offset_ratio=0.0)
    origins = symbol_origins(motif, motif.path(0.0, 48.0, 0.0, 24.0, anchor=(3.0, 1.0)))

    np.testing.assert_allclose(origins[:, 0] % 12.0, 3.0, atol=1e-9)
    np.testing.assert_allclose(origins[:, 1] % 6.0, 1.0, atol=1e-9)


def test_path_symbols_overlap_the_box():
    motif = Motifs.chert
    path = motif.path(10.0, 50.0, 20.0, 60.0)
    vertices = path.vertices.reshape(-1, len(motif._shape()[1]), 2)

    assert len(vertices) > 0
    assert np.all(vertices[:, :, 0].max(axis=1) >= 10.0)
    assert np.all(vertices[:, :, 0].min(axis=1) <= 50.0)
    assert np.all(vertices[:, :, 1].max(axis=1) >= 20.0)
    assert np.all(vertices[:, :, 1].min(axis=1) <= 60.0)


@pytest.mark.parametrize(
    ("element", "n_vertices", "closed"),
    [("line", 2, False), ("triangle", 4, True), ("quadrilateral", 5, True)],
)
def test_symbol_shapes(element, n_vertices, closed):
    motif = MotifPattern(element, length=10.0, height=4.0)
    vertices, codes = motif._shape()

    assert len(vertices) == n_vertices
    assert bool(codes[-1] == Path.CLOSEPOLY) is closed


def test_circle_shape():
    motif = MotifPattern("circle", length=4.0, height=4.0, radius=1.5)
    vertices, _ = motif._shape()
    distance = np.hypot(vertices[:, 0] - 2.0, vertices[:, 1] - 2.0)

    assert distance.max() == pytest.approx(1.5, rel=0.05)  # Bezier control points


def test_rhomb_leans_right():
    vertices, _ = Motifs.rhomb._shape()

    assert vertices[2, 0] == pytest.approx(12.0 + 3.0)  # top right shifted by tilt


def test_ellipse_fills_its_box():
    vertices, _ = MotifPattern("ellipse", length=9.0, height=6.0)._shape()

    assert vertices[:, 0].min() == pytest.approx(0.0, abs=1e-9)
    assert vertices[:, 0].max() == pytest.approx(9.0)
    assert vertices[:, 1].max() == pytest.approx(6.0)


def test_cross_is_two_strokes():
    vertices, codes = MotifPattern("cross", length=4.0, height=4.0)._shape()

    assert codes.tolist() == [Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO]
    assert vertices.tolist() == [[0.0, 2.0], [4.0, 2.0], [2.0, 0.0], [2.0, 4.0]]


def test_vertical_line():
    motif = MotifPattern("line", length=0.0, height=5.0, length_extern=16.0)
    vertices, _ = motif._shape()

    assert motif.pitch == (16.0, 5.0)
    assert vertices.tolist() == [[0.0, 0.0], [0.0, 5.0]]


def test_shift_moves_the_whole_grid():
    plain = MotifPattern("quadrilateral", offset_ratio=0.0)
    shifted = MotifPattern("quadrilateral", offset_ratio=0.0, shift_ratio=0.25)
    box = (0.0, 48.0, 0.0, 24.0)

    plain_x = symbol_origins(plain, plain.path(*box))[:, 0] % 12.0
    shifted_x = symbol_origins(shifted, shifted.path(*box))[:, 0] % 12.0

    np.testing.assert_allclose(plain_x, 0.0, atol=1e-9)
    np.testing.assert_allclose(shifted_x, 3.0, atol=1e-9)


def test_ticks_sit_in_the_gaps_of_shale_dashes():
    dashes = symbol_origins(Motifs.shale, Motifs.shale.path(0.0, 64.0, 0.0, 20.0))
    ticks = symbol_origins(Motifs.tick, Motifs.tick.path(0.0, 64.0, 0.0, 20.0))

    # Dashes are 8 points long every 16 points, odd rows staggered by 8, so
    # dashes start 4 past a multiple of 8 and gaps are centred on multiples
    # of 8, where the ticks stand.
    np.testing.assert_allclose(dashes[:, 0] % 8.0, 4.0, atol=1e-9)
    np.testing.assert_allclose(ticks[:, 0] % 8.0, 0.0, atol=1e-9)


# Motifs


def test_motif_names():
    assert Motifs.names() == (
        "brick",
        "rhomb",
        "shale",
        "chert",
        "irons",
        "tick",
        "slant",
        "plus",
        "ooid",
    )
    assert Motifs.get("brick") is Motifs.brick
    assert all(isinstance(motif, MotifPattern) for _, motif in Motifs.items())


def test_unknown_motif_raises():
    with pytest.raises(KeyError, match="available: brick"):
        Motifs.get("nope")


def test_lithologies_use_motif_patterns():
    used = [motif for _, style in Lithology.items() for motif in style.motifs]

    assert used
    assert all(isinstance(motif, MotifPattern) for motif in used)


# Drawing with Pigment


def track(depth_range=50.0, xlim=(0.0, 1.0), size=(2.0, 8.0)):
    """Return an axes shaped like a log track with depth increasing downwards."""
    figure = plt.figure(figsize=size, dpi=72)  # 1 point = 1 pixel
    axis = figure.add_axes((0.0, 0.0, 1.0, 1.0))
    axis.set_xlim(*xlim)
    axis.set_ylim(depth_range, 0.0)
    return axis


def n_symbols(axis):
    return sum(
        int(np.sum(patch.get_path().codes == Path.MOVETO)) for patch in axis.patches
    )


def fill(axis, lithology="limestone", x1=1.0, x2=0.0, depth_range=None):
    top, base = sorted(axis.get_ylim())
    y = np.linspace(top, base if depth_range is None else depth_range, 200)
    x1 = np.broadcast_to(x1, y.shape).astype(float)
    Pigment.fill_solid(axis, y, x1, x2, **Lithology.get(lithology).__dict__)
    return axis


def test_right_to_left_fill_draws_motifs():
    axis = fill(track(), x1=1.0, x2=0.0)  # add_module's default direction

    assert len(axis.patches) == 1
    assert n_symbols(axis) > 0


def test_one_patch_per_motif():
    axis = fill(track(), "cherty_dolomite")

    assert len(axis.patches) == 2  # rhombs and chert triangles


def test_pattern_does_not_depend_on_depth_range():
    short, long = fill(track(depth_range=50.0)), fill(track(depth_range=1235.0))

    assert n_symbols(short) == n_symbols(long)


@pytest.mark.parametrize("xlim", [(0.0, 1.0), (0.0, 150.0)])
def test_symbols_are_sized_in_points(xlim):
    axis = fill(track(xlim=xlim), x1=xlim[1])
    patch = axis.patches[0]
    corners = patch.get_transform().transform(patch.get_path().vertices[:5])

    width = corners[:, 0].max() - corners[:, 0].min()
    height = corners[:, 1].max() - corners[:, 1].min()

    assert (width, height) == pytest.approx((12.0, 6.0))  # 72 dpi: pixels = points


def test_nan_gap_clips_to_both_parts():
    axis = track()
    y = np.linspace(0.0, 50.0, 200)
    x = np.ones_like(y)
    x[80:120] = np.nan
    Pigment.fill_solid(axis, y, x, 0.0, **Lithology.get("limestone").__dict__)

    clip = axis.patches[0].get_clip_path().get_fully_transformed_path()
    assert int(np.sum(clip.codes == Path.MOVETO)) == 2


def test_log_scale_track():
    axis = track(xlim=(0.2, 2000.0))
    axis.set_xscale("log")

    assert n_symbols(fill(axis, x1=2000.0, x2=0.2)) > 0


def test_fill_without_motifs_adds_no_patch():
    assert len(fill(track(), "sandstone").patches) == 0


@pytest.mark.parametrize("name", [name for name, _ in Lithology.items()])
def test_every_lithology_fills_without_warnings(name):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fill(track(), name)


def test_add_motifs_inside_a_patch():
    axis = track()
    box = Rectangle((0.0, 10.0), 1.0, 5.0)
    axis.add_patch(box)

    added = Pigment.add_motifs(axis, box, Lithology.get("limestone").motifs)

    assert len(added) == 1
    assert Pigment.add_motifs(axis, box, None) == []


# Use in the one-page views


@pytest.fixture
def well_view():
    log = read("notebooks/tutorial_6_graph_B.LAS")
    view = WellView(log, ntrail=2, depth={"limit": (2028.0, 2082.0)}, widths=(1, 3))
    view.set(1, limit=(0.0, 1.0))
    view(plt.figure(figsize=(4, 8)))
    view.add_curve(1, "NPHI", multp=0.02)
    return view


def test_well_view_module_shows_motifs_in_track_and_header(well_view):
    well_view.add_module(
        1, left=0, right=None, title="Dolomite", **Lithology.get("dolomite").__dict__
    )

    assert n_symbols(well_view.stage(1)) > 0
    assert n_symbols(well_view.label(1)) > 0


def test_well_view_module_without_colour_or_hatch(well_view):
    well_view.add_module(
        1, left=0, right=None, motifs=Lithology.get("limestone").motifs
    )

    assert n_symbols(well_view.stage(1)) > 0


class Tops(dict):
    """Stand-in for the per-well tops object CrossView expects."""

    def limit(self, key):
        names = sorted(self, key=self.get)
        return self[key], self[names[names.index(key) + 1]]


class Well:
    def __init__(self, tops):
        self.tops = Tops(tops)


def test_cross_view_formation_with_motifs():
    wells = [Well({"A": 1200.0, "B": 1350.0}), Well({"A": 1150.0, "B": 1320.0})]
    view = CrossView(*wells, figsize=(6, 5))
    view.set(width_ratios=[2, 30, 4], height_ratios=[3, 30])
    view(2)
    for index in range(2):
        depth = np.linspace(1000.0, 1600.0, 50)
        view.add_curve(index, np.full_like(depth, 50.0), depth, 0.97, key="GR")

    view.add_formation("A", motifs=Lithology.get("limestone").motifs, color="cyan")

    assert n_symbols(view.scene.axis) > 0
    assert n_symbols(view.litho) > 0
