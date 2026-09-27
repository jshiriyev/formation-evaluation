"""Tests for :class:`pphys.LasView`."""

import lasio
import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from pphys import LasView, WellLog

# 1000.0 to 1020.0 m every 0.5 m (41 samples).
DEPTH = np.arange(1000.0, 1020.5, 0.5)
TOPS = {"B": 1010.0, "A": 1002.0}  # deliberately unsorted


def synthetic_curves():
    """Curves with known defects, keyed by mnemonic: (unit, description, data)."""
    gr = 50.0 + 10.0 * np.sin(DEPTH / 3.0)
    gr[[0, 1]] = np.nan  # starts at 1001.0
    gr[10:13] = np.nan  # gap 1005.0-1006.0
    gr[20] += 80.0  # single-sample spike at 1010.0

    rhob = np.linspace(2.2, 2.6, DEPTH.size)
    rhob[-2:] = [3.5, 3.6]  # above the 3.3 g/cc limit

    nphi = np.linspace(0.1, 0.3, DEPTH.size)
    nphi[5:30] = 0.2  # 25 identical samples: a flat line

    ccl = np.zeros(DEPTH.size)
    ccl[::7] = 5.0  # spiky by design

    return {
        "GR": ("GAPI", "Gamma ray", gr),
        "RHOB": ("G/CC", "Bulk density", rhob),
        "NPHI": ("V/V", "Neutron porosity", nphi),
        "CCL": ("MV", "Casing collar locator", ccl),
        "RT": ("OHMM", "True resistivity", np.geomspace(1.0, 100.0, DEPTH.size)),
        "MYST": ("XYZ", "Unknown curve", np.linspace(0.0, 1.0, DEPTH.size)),
    }


@pytest.fixture
def las_path(tmp_path):
    las = lasio.LASFile()
    las.well["WELL"].value = "TEST-1"
    las.append_curve("DEPT", DEPTH, unit="M", descr="Depth")
    for mnemonic, (unit, descr, data) in synthetic_curves().items():
        las.append_curve(mnemonic, data, unit=unit, descr=descr)
    path = tmp_path / "test.las"
    las.write(str(path), version=2.0)
    return path


@pytest.fixture
def view(las_path):
    return LasView(las_path, tops=TOPS)


def in_memory_las(depth, gr, strt=None):
    """Build a LASFile without writing it (headers set by hand)."""
    las = lasio.LASFile()
    las.append_curve("DEPT", depth, unit="M")
    las.append_curve("GR", gr, unit="GAPI")
    las.well["STRT"].value = depth[0] if strt is None else strt
    las.well["STOP"].value = depth[-1]
    las.well["STEP"].value = 0.5
    las.well["NULL"].value = -999.25
    return las


# Construction


def test_reads_a_path_with_read(las_path, tmp_path):
    view = LasView(las_path, cache_path=tmp_path / "cache")

    assert isinstance(view.log, WellLog)
    assert len(list((tmp_path / "cache").glob("test-*.pkl"))) == 1


def test_accepts_a_loaded_lasfile(las_path):
    las = lasio.read(str(las_path))
    view = LasView(las)

    assert isinstance(view.log, WellLog)
    assert view.log.curves is las.curves  # shared, not copied


def test_properties(view):
    assert view.well_name == "TEST-1"
    assert view.depth_mnemonic == "DEPT"
    assert view.depth_unit == "M"
    assert view.curves == ["GR", "RHOB", "NPHI", "CCL", "RT", "MYST"]
    np.testing.assert_allclose(view.depth, DEPTH)
    assert repr(view) == "LasView(well='TEST-1', curves=6, depth=1000-1020 M)"


@pytest.mark.parametrize(
    "tops",
    [
        TOPS,
        pd.Series(TOPS),
        pd.DataFrame({"formation": list(TOPS), "depth": list(TOPS.values())}),
    ],
    ids=["dict", "series", "dataframe"],
)
def test_tops_inputs(las_path, tops):
    frame = LasView(las_path, tops=tops).tops

    assert frame["formation"].tolist() == ["A", "B"]  # sorted by depth
    assert frame["depth"].tolist() == [1002.0, 1010.0]


def test_invalid_tops_raise(las_path):
    with pytest.raises(TypeError):
        LasView(las_path, tops=[1002.0])
    with pytest.raises(ValueError, match="formation"):
        LasView(las_path, tops=pd.DataFrame({"depth": [1002.0]}))


def test_unknown_curve_lists_available(view):
    with pytest.raises(KeyError, match="available: DEPT, GR"):
        view.statistics("NOPE")


# Tables


def test_summary(view):
    summary = view.summary()

    assert summary["well"] == "TEST-1"
    assert summary["samples"] == DEPTH.size
    assert summary["curves"] == 6
    assert (summary["data top"], summary["data bottom"]) == (1000.0, 1020.0)
    assert summary["median step"] == pytest.approx(0.5)


def test_header_sections(view):
    assert "STRT" in view.header("well")["mnemonic"].tolist()
    assert view.header("curves")["mnemonic"].tolist()[:2] == ["DEPT", "GR"]
    assert list(view.header("version").columns) == [
        "mnemonic",
        "unit",
        "value",
        "description",
    ]


def test_header_unknown_section_raises(view):
    with pytest.raises(ValueError, match="section"):
        view.header("nope")


def test_inventory(view):
    inventory = view.inventory()

    assert inventory.index.tolist()[0] == "DEPT"
    assert inventory.loc["DEPT", "family"] == "depth"
    assert inventory.loc["GR", "family"] == "gamma ray"
    assert pd.isna(inventory.loc["MYST", "family"])

    gr = inventory.loc["GR"]
    assert (gr["top"], gr["bottom"]) == (1001.0, 1020.0)
    assert gr["samples"] == 36
    assert gr["coverage"] == pytest.approx(36 / 41)
    assert gr["gaps"] == 1


def test_statistics(view):
    stats = view.statistics(["MYST", "GR"])

    assert stats.index.tolist() == ["MYST", "GR"]
    assert stats.loc["MYST", "unit"] == "XYZ"
    assert stats.loc["MYST", "count"] == 41
    assert stats.loc["MYST", ["min", "p50", "max"]].tolist() == pytest.approx(
        [0.0, 0.5, 1.0]
    )
    assert stats.loc["GR", "count"] == 36


def test_intervals(view):
    intervals = view.intervals("GR")

    assert intervals[["top", "bottom"]].to_numpy().tolist() == [
        [1001.0, 1004.5],
        [1006.5, 1020.0],
    ]
    assert intervals["thickness"].tolist() == [3.5, 13.5]


def test_min_gap_merges_intervals(view):
    merged = view.intervals("GR", min_gap=2.0)

    assert merged[["top", "bottom"]].to_numpy().tolist() == [[1001.0, 1020.0]]


def test_gaps(view):
    gaps = view.gaps()

    assert gaps.to_numpy().tolist() == [["GR", 1004.5, 1006.5, 2.0]]
    assert view.gaps(min_gap=2.0).empty


# Quality control


def test_quality_flags(view):
    quality = view.quality()

    gr = quality.loc["GR"]
    assert gr["missing"] == pytest.approx(3 / 39)
    assert gr["spikes"] == 1
    assert gr["limits"] == "[0, 500]"

    assert quality.loc["RHOB", "above_max"] == 2
    assert "2 above 3.3" in quality.loc["RHOB", "flags"]

    nphi = quality.loc["NPHI"]
    assert nphi["longest_flat"] == pytest.approx(12.0)  # 25 samples x 0.5 m
    assert "constant over 12 M" in nphi["flags"]

    assert quality.loc["RT", "flags"] == "ok"


def test_quality_skips_spiky_and_unknown_curves(view):
    quality = view.quality()

    assert pd.isna(quality.loc["CCL", "spikes"])  # spiky by design
    assert quality.loc["CCL", "flags"] == "ok"
    assert quality.loc["MYST", "limits"] == ""  # unknown family: no limits
    assert pd.isna(quality.loc["MYST", "below_min"])


def test_quality_spike_threshold(view):
    assert view.quality("GR", spike_threshold=1000.0).loc["GR", "spikes"] == 0


def status(checks, name):
    return checks.set_index("check").loc[name, "status"]


def test_validate_clean_file(view):
    checks = view.validate()

    assert set(checks.columns) == {"check", "status", "detail"}
    for name in [
        "required ~Well items",
        "depth unit",
        "depth order",
        "regular sampling",
        "header STEP",
        "header STRT",
        "header STOP",
        "unique mnemonics",
        "undeclared null values",
        "empty curves",
        "tops within logged interval",
    ]:
        assert status(checks, name) == "pass", name
    assert status(checks, "well identification") == "warn"  # only WELL is set


def test_validate_finds_problems():
    depth = np.array([1000.0, 1000.5, 1001.0, 1002.0])
    las = in_memory_las(depth, [10.0, -999.0, 30.0, 40.0], strt=999.0)

    checks = LasView(las, tops={"deep": 5000.0}).validate().set_index("check")

    assert checks.loc["regular sampling", "status"] == "warn"
    assert "1 of 3 steps" in checks.loc["regular sampling", "detail"]
    assert checks.loc["header STRT", "status"] == "warn"
    assert checks.loc["undeclared null values", "detail"] == "GR: 1 x -999"
    assert checks.loc["tops within logged interval", "status"] == "warn"


def test_validate_fails_on_unordered_depths():
    las = in_memory_las(np.array([1000.0, 1001.0, 1000.5]), [1.0, 2.0, 3.0])

    assert status(LasView(las).validate(), "depth order") == "fail"


# Zones and windows


def test_zones(view):
    zones = view.zones()

    assert zones.to_numpy().tolist() == [
        ["A", 1002.0, 1010.0, 8.0],
        ["B", 1010.0, 1020.0, 10.0],
    ]


def test_zones_without_tops(las_path):
    view = LasView(las_path)

    assert view.zones().empty
    assert view.zone_statistics().empty


def test_zone_statistics(view):
    counts = view.zone_statistics(["RHOB", "MYST"], stat="count")

    assert counts.index.tolist() == ["A", "B"]
    assert counts.loc["A", "RHOB"] == 16  # 1002.0 to 1009.5
    assert counts.loc["B", "RHOB"] == 21  # 1010.0 to 1020.0, base included


def test_window(view):
    window = view.window(1005.0, 1010.0)

    assert isinstance(window, LasView)
    np.testing.assert_allclose(window.depth, np.arange(1005.0, 1010.5, 0.5))
    assert window.tops.equals(view.tops)
    assert view.depth.size == DEPTH.size  # original untouched


# Plots


def tick_labels(axis):
    axis.figure.canvas.draw()
    return [label.get_text() for label in axis.get_yticklabels()]


def test_plot_coverage_events(view):
    figure = view.plot_coverage()
    left, right = figure.axes

    assert isinstance(figure, Figure)
    assert {"1001.0", "1004.5", "1006.5", "1020.0"} <= set(tick_labels(left))
    assert tick_labels(right) == ["A", "B"]
    assert [label.get_text() for label in left.get_xticklabels()][:2] == ["DEPT", "GR"]


def test_plot_coverage_depth_scale(view):
    left = view.plot_coverage(scale="depth").axes[0]

    assert left.get_ylim()[0] > left.get_ylim()[1]  # depth increases downwards


def test_plot_coverage_invalid_scale(view):
    with pytest.raises(ValueError, match="scale"):
        view.plot_coverage(scale="log")


def test_plot_table_default_is_inventory(view):
    texts = [text.get_text() for text in view.plot_table().axes[0].texts]

    assert texts[:4] == ["Curves", "Top", "Bottom", "Description"]
    assert {"GR", "1001.0", "Gamma ray"} <= set(texts)


def test_plot_table_series_and_index(view):
    summary_texts = {
        text.get_text() for text in view.plot_table(view.summary()).axes[0].texts
    }
    stats_texts = {
        text.get_text() for text in view.plot_table(view.statistics()).axes[0].texts
    }

    assert {"item", "value", "TEST-1"} <= summary_texts
    assert {"curve", "GR"} <= stats_texts  # named index becomes a column


def test_plot_logs(view):
    figure = view.plot_logs(["GR", ["RHOB", "NPHI"], "RT"], top=1001.0, base=1015.0)

    assert len(figure.axes) == 3
    assert figure.axes[2].get_xscale() == "log"  # resistivity
    assert figure.axes[0].get_ylim() == (1015.0, 1001.0)
    assert {text.get_text() for text in figure.axes[2].texts} == {"A", "B"}


def test_plot_histograms(view):
    figure = view.plot_histograms(ncols=4)

    assert sum(axis.get_visible() for axis in figure.axes) == 6


def test_plot_crossplot(view):
    assert len(view.plot_crossplot("RHOB", "NPHI").axes) == 1
    assert len(view.plot_crossplot("RHOB", "NPHI", color="GR").axes) == 2  # colour bar


def test_plot_correlation(view):
    image = view.plot_correlation(["GR", "RHOB", "RT"]).axes[0].images[0]

    assert image.get_array().shape == (3, 3)


def test_save_report(view, tmp_path):
    path = view.save_report(tmp_path / "report.pdf")

    assert path.read_bytes().startswith(b"%PDF")
