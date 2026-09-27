"""Shared fixtures for the pphys tests."""

import os

import lasio
import numpy as np
import pytest
from matplotlib import pyplot as plt

from pphys import WellLog

plt.switch_backend("Agg")  # render without a display

DEPTH = np.array([1000.0, 1000.5, 1001.0])


@pytest.fixture(autouse=True)
def close_figures():
    """Close the figures a test created."""
    yield
    plt.close("all")


@pytest.fixture
def cache(tmp_path):
    """A cache directory that does not exist yet."""
    return tmp_path / "cache"


@pytest.fixture
def write_las():
    """Return a function that writes a three-sample LAS file with a GR curve."""

    def write(path, gr):
        path.parent.mkdir(parents=True, exist_ok=True)
        las = lasio.LASFile()
        las.append_curve("DEPT", DEPTH, unit="m")
        las.append_curve("GR", np.asarray(gr, dtype=float), unit="gAPI")
        las.write(str(path), version=2.0)
        return path

    return write


@pytest.fixture
def age():
    """Return a function that moves a file's modification time into the past.

    Keeps cache-freshness checks independent of the file system's timestamp
    resolution.
    """

    def move_back(path, seconds=10):
        ns = path.stat().st_mtime_ns - seconds * 1_000_000_000
        os.utime(path, ns=(ns, ns))

    return move_back


@pytest.fixture
def parses(monkeypatch):
    """Record every LAS file parsed by a WellLog."""
    calls = []
    original = WellLog.read

    def counting_read(self, file_ref, **kwargs):
        calls.append(file_ref)
        return original(self, file_ref, **kwargs)

    monkeypatch.setattr(WellLog, "read", counting_read)
    return calls
