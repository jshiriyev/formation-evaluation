"""Tests for the fill-style tables (FillStyle, StyleTable and the built-in tables)."""

import dataclasses

import numpy as np
import pytest
from matplotlib import pyplot as plt
from matplotlib.colors import is_color_like
from matplotlib.patches import Rectangle

from pphys import read
from pphys.onepage import (
    FillStyle,
    Lithology,
    Mineral,
    Motifs,
    Pigment,
    Porespace,
    StyleTable,
    WellView,
)

# The graphic lithology key the Lithology table follows.
KEY = [
    ["limestone", "dolomite", "chert"],
    ["dolomitic limestone", "cherty dolomite", "cherty limestone"],
    ["shaly limestone", "shaly dolomite", "cherty dolomitic limestone"],
    ["shale", "calcareous shale", "dolomitic shale"],
    ["sandstone", "shaly sandstone", "sandy shale"],
    ["ironstone", "coal"],
    ["gypsum", "anhydrite", "halite"],
]

# FillStyle


def test_fill_style_defaults():
    style = FillStyle()

    assert (style.facecolor, style.hatch, style.motifs, style.label) == (
        "white",
        None,
        (),
        "",
    )


def test_fill_style_unpacks_like_a_dict():
    style = Lithology.shaly_sandstone

    assert dict(**style) == {
        "facecolor": style.facecolor,
        "hatch": "...",
        "motifs": (Motifs.shale,),
        "label": "shaly sandstone",
    }
    assert style["hatch"] == "..."
    with pytest.raises(KeyError):
        style["color"]


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"facecolor": "steelb"}, ValueError, "not a matplotlib colour"),
        ({"hatch": "abc"}, ValueError, "hatch"),
        ({"motifs": ("brick",)}, TypeError, "MotifPattern"),
    ],
)
def test_fill_style_validation(kwargs, error, message):
    with pytest.raises(error, match=message):
        FillStyle(**kwargs)


def test_fill_style_is_immutable():
    style = FillStyle(motifs=[Motifs.brick])

    assert style.motifs == (Motifs.brick,)  # a list becomes a tuple
    with pytest.raises(dataclasses.FrozenInstanceError):
        style.facecolor = "red"


# StyleTable


def test_lookup_ignores_case_spaces_hyphens_and_underscores():
    style = Lithology.get("cherty_dolomitic_limestone")

    assert Lithology["Cherty Dolomitic-Limestone"] is style
    assert Lithology.cherty_dolomitic_limestone is style


def test_unknown_style_suggests_close_names():
    with pytest.raises(KeyError, match="Did you mean limestone"):
        Lithology.get("limstone")


def test_unknown_attribute():
    with pytest.raises(AttributeError, match="No style 'nope'"):
        _ = Lithology.nope
    assert not hasattr(Lithology, "nope")


def test_labels():
    table = StyleTable("t", {"sandy clay": FillStyle(), "x": FillStyle(label="Custom")})

    assert table.sandy_clay.label == "sandy clay"
    assert table.x.label == "Custom"


def test_table_protocol():
    assert len(Lithology) == len(Lithology.names())
    assert "Cherty Dolomite" in Lithology
    assert 42 not in Lithology
    assert list(Lithology) == list(Lithology.names())
    assert dict(Lithology.items())["coal"] is Lithology.coal
    assert repr(Mineral) == f"StyleTable('Minerals', {len(Mineral)} styles)"


def test_duplicate_names_raise():
    with pytest.raises(ValueError, match="Duplicate"):
        StyleTable("t", {"a b": FillStyle(), "A_B": FillStyle()})


# Table contents


def test_lithology_follows_the_key():
    names = [name for row in KEY for name in row]

    assert all(name in Lithology for name in names)
    assert list(Lithology)[: len(names)] == [name.replace(" ", "_") for name in names]


@pytest.mark.parametrize(
    "table", [Lithology, Mineral, Porespace], ids=lambda t: t.title
)
def test_colours_are_valid(table):
    assert all(is_color_like(style.facecolor) for _, style in table.items())


def test_porespace_colours_fixed():
    assert Porespace.water.facecolor == "steelblue"
    assert Porespace.gas.facecolor == "lightcoral"
    assert Porespace.oil.facecolor == "seagreen"


def test_mixed_lithologies_differ_from_their_base():
    assert Lithology.dolomitic_limestone.motifs != Lithology.limestone.motifs
    assert Lithology.calcareous_shale.motifs == (Motifs.shale, Motifs.tick)
    assert Lithology.dolomitic_shale.motifs == (Motifs.shale, Motifs.slant)
    assert Lithology.halite.motifs == (Motifs.plus,)
    assert Lithology.ironstone.motifs == (Motifs.ooid,)


def test_minerals_for_volume_tracks():
    assert {"quartz", "calcite", "dolomite", "illite", "kaolinite"} <= set(Mineral)


# Keys


def text_of(figure):
    return [text.get_text() for text in figure.axes[0].texts]


def swatches(figure):
    return [patch for patch in figure.axes[0].patches if isinstance(patch, Rectangle)]


def test_plot_key_draws_every_style():
    figure = Porespace.plot_key(ncols=4)

    assert len(swatches(figure)) == len(Porespace)
    assert text_of(figure)[0] == "Pore space"  # the title
    assert "water clay bound" in text_of(figure)


def test_plot_key_rows_are_centred():
    figure = Lithology.plot_key(KEY, title="GRAPHIC LITHOLOGY KEY")
    boxes = {box.get_facecolor(): box for box in swatches(figure)}
    coal = boxes[(0.0, 0.0, 0.0, 1.0)]
    centre = coal.get_x() + coal.get_width() / 2

    assert len(swatches(figure)) == 20
    assert text_of(figure)[0] == "GRAPHIC LITHOLOGY KEY"
    assert (
        centre > figure.axes[0].get_xlim()[1] / 2
    )  # coal is right of centre in a 2-item row


def test_plot_key_draws_motifs_and_hatches():
    figure = Lithology.plot_key(["limestone", "sandstone"], title="")
    _, sandstone = swatches(figure)
    motif_patches = [
        patch for patch in figure.axes[0].patches if not isinstance(patch, Rectangle)
    ]

    assert sandstone.get_hatch() == "..."
    assert len(motif_patches) == 1  # the limestone bricks
    assert text_of(figure) == ["limestone", "sandstone"]  # no title


def test_plot_key_unknown_name_raises():
    with pytest.raises(KeyError):
        Lithology.plot_key(["limestone", "marble"])


# Use in plots


def test_fill_solid_accepts_a_style():
    _, axis = plt.subplots()
    axis.set_xlim(0, 1)
    axis.set_ylim(100, 0)
    depth = np.linspace(0, 100, 50)

    Pigment.fill_solid(
        axis, depth, np.ones_like(depth), 0, **Lithology.cherty_limestone
    )

    assert len(axis.patches) == 2  # bricks and chert


def test_well_view_module_title_defaults_to_the_label():
    view = WellView(
        read("notebooks/tutorial_6_graph_B.LAS"),
        ntrail=2,
        depth={"limit": (2028.0, 2082.0)},
        widths=(1, 3),
    )
    view.set(1, limit=(0.0, 1.0))
    view(plt.figure(figsize=(4, 8)))
    view.add_curve(1, "NPHI", multp=0.02)

    view.add_module(1, left=0, right=None, **Mineral.quartz)

    assert "quartz" in [text.get_text() for text in view.label(1).texts]
