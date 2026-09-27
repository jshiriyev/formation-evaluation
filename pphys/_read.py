"""Read a LAS file into a :class:`WellLog`, with an optional pickle cache."""

from __future__ import annotations

import hashlib
import os
import pickle
from pathlib import Path
from typing import Any

from ._lasio import WellLog

# Raised by pickle when a cache file is truncated or refers to code that no
# longer exists (e.g. a renamed class). Such cache files are rebuilt.
_UNREADABLE_CACHE = (pickle.UnpicklingError, EOFError, AttributeError, ImportError)


def read(
    file_path: str | os.PathLike[str],
    cache_path: str | os.PathLike[str] | None = None,
    **kwargs: Any,
) -> WellLog:
    """Read a LAS file, optionally through a pickle cache.

    Parameters
    ----------
    file_path : str or path-like
        Path to the LAS file.
    cache_path : str or path-like, optional
        Directory for the cached ``.pkl`` file; it is created if missing.
        Without it the file is parsed directly and nothing is cached.
    **kwargs
        Passed to :class:`lasio.LASFile`, e.g. ``null_policy="none"``.

    Returns
    -------
    WellLog
        The parsed log.

    Notes
    -----
    A cached log is reused only if it was made from the same file (by
    absolute path) with the same ``kwargs`` and is newer than the file.
    Unreadable cache files are rebuilt. Loading a pickle can run arbitrary
    code, so only point ``cache_path`` at a directory you trust.
    """
    file_path = Path(file_path)

    if cache_path is None:
        return WellLog(str(file_path), **kwargs)

    cache_file = _cache_file(file_path, Path(cache_path), kwargs)

    if _is_fresh(cache_file, file_path):
        try:
            log = pickle.loads(cache_file.read_bytes())
        except _UNREADABLE_CACHE:
            pass
        else:
            if isinstance(log, WellLog):
                return log

    log = WellLog(str(file_path), **kwargs)

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(pickle.dumps(log))

    return log


def _cache_file(file_path: Path, cache_dir: Path, kwargs: dict[str, Any]) -> Path:
    """Return the cache file for ``file_path`` parsed with ``kwargs``.

    The name keeps the file stem for readability and adds a hash of the
    absolute path and the read options, so files with the same name in
    different folders, or read with different options, do not collide.
    """
    key = f"{file_path.resolve()}|{sorted(kwargs.items())!r}"
    digest = hashlib.sha256(key.encode()).hexdigest()[:12]
    return cache_dir / f"{file_path.stem}-{digest}.pkl"


def _is_fresh(cache_file: Path, file_path: Path) -> bool:
    """Return True if ``cache_file`` exists and is newer than ``file_path``."""
    if not cache_file.exists():
        return False
    return cache_file.stat().st_mtime_ns > file_path.stat().st_mtime_ns
