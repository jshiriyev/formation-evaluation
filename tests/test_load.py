"""Tests for :func:`pphys.load`."""

import numpy as np
import pytest

from pphys import WellLog, load, read


@pytest.fixture
def source(tmp_path, write_las, age):
    """A folder with three LAS files and entries that must be skipped."""
    folder = tmp_path / "wells"

    for name, gr in [
        ("b.las", 2.0),
        ("A.LAS", 1.0),
        ("c.las", 3.0),
        ("sub/d.las", 4.0),  # subfolders are not searched
    ]:
        age(write_las(folder / name, [gr] * 3))

    (folder / "notes.txt").write_text("not a log")
    (folder / "e.las").mkdir()  # a folder, not a LAS file

    return folder


def test_reads_each_las_file_in_order(source):
    logs = load(source)

    assert list(logs) == ["A", "b", "c"]
    assert all(isinstance(log, WellLog) for log in logs.values())
    np.testing.assert_allclose(logs["A"]["GR"], 1.0)
    np.testing.assert_allclose(logs["b"]["GR"], 2.0)
    np.testing.assert_allclose(logs["c"]["GR"], 3.0)


def test_without_cache_writes_nothing(source, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    load(source)

    assert list(tmp_path.rglob("*.pkl")) == []


def test_cache_is_reused(source, cache, parses):
    load(source, cache)
    load(source, cache)

    assert len(parses) == 3


def test_shares_cache_with_read(source, cache, parses):
    read(source / "b.las", cache)
    load(source, cache)

    assert len(parses) == 3  # b.las was already cached by read


def test_edited_file_is_reread(source, cache, parses, write_las, age):
    load(source, cache)

    write_las(source / "b.las", [20.0] * 3)
    age(source / "b.las", seconds=5)
    age(next(cache.glob("b-*.pkl")), seconds=10)  # the cache now predates the edit

    logs = load(source, cache)

    assert len(parses) == 4
    np.testing.assert_allclose(logs["b"]["GR"], 20.0)


def test_same_names_in_different_folders(tmp_path, cache, write_las, age):
    age(write_las(tmp_path / "north" / "well.las", [1.0] * 3))
    age(write_las(tmp_path / "south" / "well.las", [2.0] * 3))

    north = load(tmp_path / "north", cache)
    south = load(tmp_path / "south", cache)

    np.testing.assert_allclose(north["well"]["GR"], 1.0)
    np.testing.assert_allclose(south["well"]["GR"], 2.0)


def test_read_options_are_passed_on(tmp_path, write_las):
    write_las(tmp_path / "well.las", [10.0, np.nan, 30.0])

    assert load(tmp_path, null_policy="none")["well"]["GR"][1] == -9999.25


def test_old_cache_files_are_ignored(source, cache):
    cache.mkdir()
    (cache / "b.pkl").write_bytes(b"cpphys._lasio\nLASIO\n.")  # old load's format

    np.testing.assert_allclose(load(source, cache)["b"]["GR"], 2.0)


def test_empty_folder(tmp_path):
    assert load(tmp_path) == {}


def test_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load(tmp_path / "missing")


def test_file_instead_of_folder_raises(tmp_path, write_las):
    with pytest.raises(NotADirectoryError):
        load(write_las(tmp_path / "well.las", [1.0] * 3))


def test_duplicate_names_raise(tmp_path, write_las):
    write_las(tmp_path / "well.las", [1.0] * 3)
    write_las(tmp_path / "well.LAS", [2.0] * 3)

    if len(list(tmp_path.iterdir())) < 2:
        pytest.skip("case-insensitive file system: both names are the same file")

    with pytest.raises(ValueError, match="well"):
        load(tmp_path)
