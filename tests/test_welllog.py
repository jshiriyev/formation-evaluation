"""Tests for :class:`pphys.WellLog`."""

import pickle

import lasio
import numpy as np
import pandas as pd
import pytest

from pphys import WellLog

# 1000.0 to 1010.0 m every 0.5 m (21 samples); GR = 20 + 10 * (depth - 1000).
DEPTH = np.arange(1000.0, 1010.5, 0.5)
GR = 20.0 + 10.0 * (DEPTH - 1000.0)
RHOB = np.full(DEPTH.size, 2.4)
RHOB[5] = np.nan  # 1002.5 m, written as the NULL value


def write_las(path, depth, gr, rhob):
    las = lasio.LASFile()
    las.well["WELL"].value = "TEST-1"
    las.append_curve("DEPT", depth, unit="m")
    las.append_curve("GR", gr, unit="gAPI")
    las.append_curve("RHOB", rhob, unit="g/cc")
    las.write(str(path), version=2.0)
    return path


@pytest.fixture
def log(tmp_path):
    return WellLog(str(write_las(tmp_path / "test.las", DEPTH, GR, RHOB)))


@pytest.fixture
def log_descending(tmp_path):
    path = write_las(tmp_path / "desc.las", DEPTH[::-1], GR[::-1], RHOB[::-1])
    return WellLog(str(path))


def test_reads_file_as_lasfile(log):
    assert isinstance(log, lasio.LASFile)
    assert log.keys() == ["DEPT", "GR", "RHOB"]
    assert log.well["WELL"].value == "TEST-1"
    np.testing.assert_allclose(log.index, DEPTH)
    assert np.isnan(log["RHOB"][5])


def test_empty_constructor():
    assert WellLog().curves == []


def test_mask_without_bounds_selects_all(log):
    assert log.mask().all()


def test_mask_bounds_are_inclusive(log):
    selected = log.index[log.mask(1001.0, 1002.0)]
    np.testing.assert_array_equal(selected, [1001.0, 1001.5, 1002.0])


def test_mask_open_ended(log):
    assert log.mask(dmin=1009.0).sum() == 3
    assert log.mask(dmax=1000.5).sum() == 2


def test_crop_frame(log):
    frame = log.crop(1001.0, 1003.0)

    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == ["GR", "RHOB"]
    assert frame.index.min() == 1001.0
    assert frame.index.max() == 1003.0


def test_crop_curve(log):
    np.testing.assert_allclose(log.crop(1001.0, 1002.0, key="GR"), [30.0, 35.0, 40.0])


def test_resample_curve_interpolates_linearly(log):
    np.testing.assert_allclose(log.resample([1000.25, 1004.75], key="GR"), [22.5, 67.5])


def test_resample_outside_range_is_nan(log):
    values = log.resample([999.0, 1011.0], key="GR")
    assert np.isnan(values).all()


def test_resample_does_not_bridge_nan(log):
    values = log.resample([1002.25, 1002.75, 1004.0], key="RHOB")
    assert np.isnan(values[:2]).all()
    assert values[2] == pytest.approx(2.4)


def test_resample_frame(log):
    depths = np.array([1000.25, 1005.0, 1009.75])
    frame = log.resample(depths)

    assert list(frame.columns) == ["GR", "RHOB"]
    assert frame.index.name == "DEPT"
    np.testing.assert_allclose(frame.index, depths)
    np.testing.assert_allclose(frame["GR"], [22.5, 70.0, 117.5])


def test_resample_descending_index(log, log_descending):
    depths = [1000.25, 1004.75, 1009.75]
    np.testing.assert_allclose(
        log_descending.resample(depths, key="GR"), log.resample(depths, key="GR")
    )


def test_copy_is_independent(log):
    clone = log.copy()
    clone["GR"][0] = -1.0

    assert isinstance(clone, WellLog)
    assert log["GR"][0] == 20.0


def test_copy_window(log):
    clone = log.copy(1001.0, 1003.0)

    np.testing.assert_allclose(clone.index, np.arange(1001.0, 1003.5, 0.5))
    assert all(curve.data.size == 5 for curve in clone.curves)
    assert clone.well["STRT"].value == 1001.0
    assert clone.well["STOP"].value == 1003.0
    assert clone.well["STEP"].value == log.well["STEP"].value
    assert clone.well["WELL"].value == "TEST-1"
    assert log.index.size == DEPTH.size  # original untouched


def test_copy_empty_window_raises(log):
    with pytest.raises(ValueError, match="No depths"):
        log.copy(2000.0, 2100.0)


def test_pickle_roundtrip(log):
    # pphys.read/load cache WellLog objects with pickle.
    restored = pickle.loads(pickle.dumps(log))

    assert isinstance(restored, WellLog)
    np.testing.assert_allclose(restored["GR"], log["GR"])


@pytest.mark.parametrize(
    ("values", "expected"),
    [([1.0, 2.0], True), ([1.0, np.nan], False), ([], True)],
)
def test_is_valid(values, expected):
    assert WellLog.is_valid(values) is expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [([0.0, 2.0], True), ([-1.0, 2.0], False), ([1.0, np.nan], False)],
)
def test_is_positive(values, expected):
    assert WellLog.is_positive(values) is expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [([1.0, 2.0, 3.0], True), ([1.0, 1.0, 2.0], False), ([3.0, 2.0, 1.0], False)],
)
def test_is_sorted(values, expected):
    assert WellLog.is_sorted(values) is expected
