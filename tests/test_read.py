"""Tests for :func:`pphys.read`."""

import pickle

import numpy as np
import pytest

from pphys import WellLog, read

GR = [10.0, np.nan, 30.0]  # the NaN is written as the NULL value -9999.25


@pytest.fixture
def las_file(tmp_path, write_las, age):
    path = write_las(tmp_path / "data" / "well.las", GR)
    age(path)
    return path


def test_without_cache_writes_nothing(las_file, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    log = read(las_file)

    assert isinstance(log, WellLog)
    np.testing.assert_allclose(log["GR"], GR)
    assert list(tmp_path.rglob("*.pkl")) == []


def test_accepts_str_and_path(las_file):
    np.testing.assert_allclose(read(str(las_file))["GR"], read(las_file)["GR"])


@pytest.mark.parametrize("use_cache", [False, True])
def test_missing_file_raises(tmp_path, cache, use_cache):
    with pytest.raises(FileNotFoundError):
        read(tmp_path / "missing.las", cache if use_cache else None)


def test_cache_directory_is_created(las_file, tmp_path):
    cache = tmp_path / "cache" / "nested"

    read(las_file, cache)

    assert len(list(cache.glob("well-*.pkl"))) == 1


def test_cache_is_reused(las_file, cache, parses):
    first = read(las_file, cache)
    second = read(las_file, cache)

    assert len(parses) == 1
    assert isinstance(second, WellLog)
    np.testing.assert_allclose(second["GR"], first["GR"])


def test_edited_file_invalidates_cache(las_file, cache, parses, write_las, age):
    read(las_file, cache)
    cache_file = next(cache.glob("*.pkl"))

    write_las(las_file, [11.0, 21.0, 31.0])
    age(las_file, seconds=5)
    age(cache_file, seconds=10)  # the cache now predates the edit

    log = read(las_file, cache)
    read(las_file, cache)

    assert len(parses) == 2  # rebuilt once, then reused
    np.testing.assert_allclose(log["GR"], [11.0, 21.0, 31.0])


def test_same_name_in_different_folders(tmp_path, cache, write_las, age):
    a = write_las(tmp_path / "a" / "well.las", [1.0, 2.0, 3.0])
    b = write_las(tmp_path / "b" / "well.las", [4.0, 5.0, 6.0])
    age(a)
    age(b)

    read(a, cache)

    np.testing.assert_allclose(read(b, cache)["GR"], [4.0, 5.0, 6.0])
    np.testing.assert_allclose(read(a, cache)["GR"], [1.0, 2.0, 3.0])
    assert len(list(cache.glob("well-*.pkl"))) == 2


def test_read_options_are_part_of_cache_key(las_file, cache):
    assert np.isnan(read(las_file, cache)["GR"][1])
    assert read(las_file, cache, null_policy="none")["GR"][1] == -9999.25


@pytest.mark.parametrize(
    "content",
    [
        b"\x00 not a pickle",
        pickle.dumps({"not": "a log"}),
        b"cpphys._lasio\nLASIO\n.",  # written before LASIO was renamed WellLog
    ],
    ids=["garbage", "wrong-type", "renamed-class"],
)
def test_unreadable_cache_is_rebuilt(las_file, cache, parses, content):
    read(las_file, cache)
    cache_file = next(cache.glob("*.pkl"))
    cache_file.write_bytes(content)

    log = read(las_file, cache)

    assert isinstance(log, WellLog)
    assert len(parses) == 2
    assert isinstance(pickle.loads(cache_file.read_bytes()), WellLog)
