"""Read every LAS file in a directory into :class:`WellLog` objects."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ._lasio import WellLog
from ._read import read


def load(
    source_path: str | os.PathLike[str],
    cache_path: str | os.PathLike[str] | None = None,
    **kwargs: Any,
) -> dict[str, WellLog]:
    """Read all LAS files in a directory, optionally through a pickle cache.

    Parameters
    ----------
    source_path : str or path-like
        Directory containing the LAS files. Files ending in ``.las`` in any
        letter case are read; subdirectories are not searched.
    cache_path : str or path-like, optional
        Cache directory, handled exactly as in :func:`pphys.read`. Without it
        every file is parsed and nothing is cached.
    **kwargs
        Passed to :class:`lasio.LASFile`, e.g. ``null_policy="none"``.

    Returns
    -------
    dict of str to WellLog
        Logs keyed by file name without extension, in case-insensitive
        alphabetical order.

    Raises
    ------
    FileNotFoundError
        If ``source_path`` does not exist.
    NotADirectoryError
        If ``source_path`` is not a directory.
    ValueError
        If two files would get the same key, e.g. ``well.las`` and
        ``well.LAS`` on a case-sensitive file system.
    """
    source_dir = Path(source_path)

    paths = sorted(
        (path for path in source_dir.iterdir() if _is_las_file(path)),
        key=lambda path: path.name.lower(),
    )

    logs: dict[str, WellLog] = {}

    for path in paths:
        if path.stem in logs:
            raise ValueError(
                f"More than one LAS file named {path.stem!r} in {source_dir}."
            )
        logs[path.stem] = read(path, cache_path, **kwargs)

    return logs


def _is_las_file(path: Path) -> bool:
    """Return True if ``path`` is a file with a ``.las`` extension in any case."""
    return path.suffix.lower() == ".las" and path.is_file()
