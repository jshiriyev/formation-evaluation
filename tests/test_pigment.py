"""Tests for Pigment: solid fills, colour-map fills and motifs."""

import numpy as np
import pytest
from matplotlib import colormaps
from matplotlib import pyplot as plt
from matplotlib.image import AxesImage
from matplotlib.patches import Rectangle
from matplotlib.path import Path

from pphys import read
from pphys.onepage import CrossView, Lithology, Motifs, Pigment, WellView


def track(ylim=(1100.0, 1000.0), xlim=(0.0, 1.0)):
    """Return a 72-dpi log track (1 point = 1 pixel), depth increasing downwards."""
    figure = plt.figure(figsize=(3.0, 6.0), dpi=72)
    axis = figure.add_axes((0.25, 0.25, 0.5, 0.5))
    axis.set_xlim(*xlim)
    axis.set_ylim(*ylim)
    return axis


def depths(top=1000.0, base=1100.0, n=201):
    return np.linspace(top, base, n)


def n_polygons(path):
    return int(np.sum(path.codes == Path.MOVETO))


# fill_solid


def test_fill_solid_returns_the_fill_and_passes_keywords():
    axis = track()
    y = depths()

    fill = Pigment.fill_solid(
        axis,
        y,
        np.full_like(y, 0.5),
        0,
        facecolor="gold",
        hatch="..",
        label="sand",
        alpha=0.5,
    )

    assert fill is axis.collections[0]
    assert (fill.get_label(), fill.get_alpha(), fill.get_hatch()) == ("sand", 0.5, "..")
    assert axis.get_legend_handles_labels()[1] == ["sand"]


def test_fill_solid_shades_a_crossover():
    axis = track(xlim=(0.45, -0.15))
    y = depths()
    nphi = np.full_like(y, 0.25)
    dphi = 0.25 + 0.1 * np.sin((y - 1000.0) / 100.0 * 4 * np.pi)  # two lobes each side

    fill = Pigment.fill_solid(
        axis, y, nphi, dphi, where=dphi > nphi, interpolate=True, facecolor="gold"
    )

    assert len(fill.get_paths()) == 2


def test_fill_solid_accepts_a_single_motif():
    axis = track()
    y = depths()

    Pigment.fill_solid(axis, y, np.ones_like(y), 0, motifs=Motifs.brick)

    assert len(axis.patches) == 1


# add_motifs


def long_fill(axis, style="dolomitic limestone"):
    """Fill 900-1300 m, a longer interval than the track shows."""
    y = depths(900.0, 1300.0, 400)
    return Pigment.fill_solid(axis, y, np.ones_like(y), 0, **Lithology[style])


def test_motifs_cover_only_the_visible_part():
    axis = long_fill(track()).axes

    for patch in axis.patches:
        top, base = sorted(patch.get_path().get_extents().intervaly)
        assert (top, base) == pytest.approx((1000.0, 1100.0), abs=10.0)  # a cell or so
        assert patch.get_clip_box().bounds == axis.bbox.bounds


def test_motifs_do_not_leak_out_of_the_axes():
    axis = track()
    axis.set_axis_off()
    y = depths(900.0, 1300.0, 400)
    Pigment.fill_solid(
        axis, y, np.ones_like(y), 0, facecolor="none", motifs=Motifs.brick
    )
    figure = axis.figure
    figure.canvas.draw()

    image = np.asarray(figure.canvas.buffer_rgba())[..., :3]
    x0, y0, x1, y1 = np.round(axis.bbox.extents).astype(int)
    outside = np.ones(image.shape[:2], dtype=bool)
    outside[image.shape[0] - y1 - 1 : image.shape[0] - y0 + 1, x0 - 1 : x1 + 1] = False

    assert (image[outside] < 250).any(axis=1).sum() == 0


def test_motifs_do_not_change_the_data_limits():
    axis = track()
    y = depths()

    Pigment.fill_solid(axis, y, np.ones_like(y), 0, **Lithology.limestone)

    assert axis.dataLim.bounds == pytest.approx((0.0, 1000.0, 1.0, 100.0))


def test_motifs_follow_pending_autoscaling():
    figure = plt.figure(figsize=(3.0, 6.0), dpi=72)
    axis = figure.add_axes((0.0, 0.0, 1.0, 1.0))  # autoscaled, no limits set
    y = depths()

    Pigment.fill_solid(axis, y, np.ones_like(y), 0, **Lithology.limestone)
    figure.canvas.draw()
    patch = axis.patches[0]
    corners = patch.get_transform().transform(patch.get_path().vertices[:5])

    assert np.ptp(corners, axis=0) == pytest.approx((12.0, 6.0))  # a brick, in points


def test_motifs_take_the_zorder_of_the_fill():
    axis = track()
    y = depths()

    Pigment.fill_solid(
        axis, y, np.ones_like(y), 0, zorder=0.5, **Lithology.cherty_limestone
    )

    assert [patch.get_zorder() for patch in axis.patches] == [0.5, 0.5]


def test_add_motifs_to_a_patch_in_axes_coordinates():
    axis = track()
    box = Rectangle((0.1, 0.1), 0.3, 0.3, transform=axis.transAxes)
    axis.add_patch(box)

    (patch,) = Pigment.add_motifs(axis, box, Motifs.brick)
    clip = patch.get_clip_path().get_fully_transformed_path().get_extents()

    assert clip.bounds == pytest.approx(box.get_window_extent().bounds)


def test_add_motifs_outside_the_view_adds_nothing():
    axis = track()
    y = depths(2000.0, 2100.0)
    fill = axis.fill_betweenx(y, 1.0, 0.0)

    assert Pigment.add_motifs(axis, fill, Lithology.limestone.motifs) == []
    assert Pigment.add_motifs(axis, fill, None) == []


# fill_colormap


def colour_at(image, depth):
    """Return the RGBA colour of the image row at a depth."""
    colours = image.get_array()
    _, _, bottom, top = image.get_extent()
    row = int((depth - bottom) / (top - bottom) * colours.shape[0])
    return np.asarray(colours[row, 0])


def test_colormap_keeps_limits_aspect_and_patches():
    _, axis = plt.subplots()
    axis.invert_yaxis()  # autoscaled, depth downwards
    axis.set_aspect(2.0)
    y = depths()

    image = Pigment.fill_colormap(axis, y, 60 + 40 * np.sin(y / 7.0))

    assert isinstance(image, AxesImage)
    assert axis.yaxis_inverted()
    base, top = axis.get_ylim()
    assert base > 1100.0
    assert top < 1000.0
    assert axis.get_aspect() == 2.0
    assert len(axis.patches) == len(axis.collections) == 0
    assert image.get_clip_box().bounds == axis.bbox.bounds


@pytest.mark.parametrize(
    "y",
    [
        np.linspace(1100.0, 1000.0, 101),  # descending
        np.r_[
            np.linspace(1000.0, 1010.0, 100), np.linspace(1011.0, 1100.0, 10)
        ],  # uneven
    ],
    ids=["descending", "uneven"],
)
def test_colormap_colours_follow_the_depth(y):
    axis = track(xlim=(0.0, 150.0))
    gr = np.where(y < 1050.0, 20.0, 120.0)

    image = Pigment.fill_colormap(axis, y, gr, 0, colormap="viridis")
    viridis = colormaps["viridis"]

    assert colour_at(image, 1030.0) == pytest.approx(viridis(0.0))
    assert colour_at(image, 1080.0) == pytest.approx(viridis(1.0))


def test_colormap_between_two_curves():
    axis = track(xlim=(0.0, 150.0))
    y = depths()

    image = Pigment.fill_colormap(
        axis, y, np.full_like(y, 120.0), np.full_like(y, 40.0)
    )

    assert image.get_extent()[:2] == pytest.approx((40.0, 120.0))


def test_colormap_leaves_nan_gaps_empty():
    axis = track(xlim=(0.0, 150.0))
    y = depths()
    gr = np.full_like(y, 80.0)
    gr[80:120] = np.nan

    image = Pigment.fill_colormap(axis, y, gr)

    assert n_polygons(image.get_clip_path().get_fully_transformed_path()) == 2


def test_colormap_log_track_uses_log_colours():
    axis = track(xlim=(0.2, 2000.0))
    axis.set_xscale("log")
    y = depths()
    rt = np.where(y < 1050.0, 1.0, 100.0)
    rt[100] = 10.0

    image = Pigment.fill_colormap(axis, y, rt, 0.2, colormap="viridis")

    assert colour_at(image, y[100]) == pytest.approx(colormaps["viridis"](0.5))


def test_colormap_with_colour_limits():
    axis = track(xlim=(0.0, 150.0))
    y = depths()

    image = Pigment.fill_colormap(axis, y, np.full_like(y, 75.0), vmin=0, vmax=150)

    assert colour_at(image, 1050.0) == pytest.approx(colormaps["Reds"](0.5))


def test_colormap_without_values_draws_nothing():
    axis = track()
    y = depths()

    assert Pigment.fill_colormap(axis, y, np.full_like(y, np.nan)) is None
    assert len(axis.images) == len(axis.collections) == 0


# Use in the one-page views


def test_well_view_shade():
    view = WellView(
        read("notebooks/tutorial_1_graph_B.LAS"),
        ntrail=2,
        depth={"limit": (1330.0, 1380.0)},
        widths=(1, 3),
    )
    view.set(1, limit=(0.0, 150.0))
    view(plt.figure(figsize=(4, 8)))
    view.add_curve(1, "GAMMATOTAL")

    view.add_shade(1, "GAMMATOTAL", 0, colormap="YlOrBr")

    assert len(view.stage(1).images) == 1
    assert view.stage(1).get_ylim() == (1380.0, 1330.0)


def test_cross_view_gradient():
    view = CrossView(object(), object(), figsize=(6, 5))
    view.set(width_ratios=[2, 30, 4], height_ratios=[3, 30])
    view(2)
    depth = np.linspace(1000.0, 1600.0, 50)
    gr = 70 + 50 * np.sin(depth / 20.0)

    for index in range(2):
        view.add_gradient(index, gr, depth, 0.95, key="GR", colormap="YlOrBr")

    assert all(len(axis.images) == 1 for axis in view.scene)
    assert all(axis.yaxis_inverted() for axis in view.scene)
