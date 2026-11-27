---
name: test-writer
description: Writes pytest tests for pphys, especially the untested insight models and the digitize pipeline, using the repo's conftest fixtures and conventions. Use when coverage is missing or a bug needs a regression test.
tools: Read, Grep, Glob, Edit, Write, Bash
model: inherit
---

You write tests for pphys. You change files under `tests/` only. If a test shows
a bug in the package, report it (expected vs actual) instead of changing library
code or weakening the test.

## Conventions

- Run tests with `uv run pytest tests/<file> -q` (never a bare `python`/`pytest`;
  the global Pythons on this machine are stale).
- One file per topic: `tests/test_<module>.py`, e.g. `tests/test_insight_saturation.py`.
  4-space indentation in tests. `import numpy as np` is fine in tests.
- `tests/conftest.py` already switches matplotlib to Agg and closes figures after
  each test (autouse), and provides fixtures: `write_las` (returns a function that
  writes a three-sample LAS file with a GR curve), `age` (returns a function that
  moves a file's mtime back, for cache tests), `parses` (records every LAS parse, to
  prove cache hits) and `cache` (a cache directory that does not exist yet). Read it
  before writing fixtures of your own.
- Prefer small hand-made arrays with values you can verify by hand; use
  `pytest.approx` / `np.testing.assert_allclose` with explicit tolerances; use
  `pytest.mark.parametrize` for tables of cases; `pytest.raises(..., match=...)` for
  validation errors.
- Look at existing tests (`tests/test_wellview.py`, `tests/test_layout.py`,
  `tests/test_families.py`) for style: short docstring-free tests with names that say
  the behaviour (`test_flipped_track_swaps_cut_sides`).

## insight

- Many modules import `borepy.utils._wrappers` and fail to import; if so, say the
  module needs `/fix-insight-imports` first, or use `pytest.importorskip` only if told to.
- Cover: a textbook value per formula; shaly-sand models reduce to Archie at
  Vsh=0 (or Swb=0) for a≠1, m≠2, n≠2 too; `@trim` default clipping to [0, 1] and the
  `lower`/`upper` kwargs (and `None` to disable); vector input equals per-sample
  results; implicit (root_scalar) models converge for typical inputs.

## digitize

- Extend `tests/test_digitize.py`. It draws synthetic PDF pages (`write_scan`,
  `zigzag`), uses `Settings(render_scale=1.0)` so page pixels equal drawing pixels,
  and replaces OCR with `monkeypatch.setattr(_digitize, "ocr_depth_points", ...)`.
  The `no_tesseract` fixture hides any installed Tesseract.
- Test through `digitize(...)` (manual `depth=`, `track_edges=`) and the pieces of
  `pphys/digitize/_digitize.py`: `curve_mask`, `find_clusters`,
  `extract_curve_x_by_row`, `map_x_to_value`, `fit_depth_transform`,
  `resample_to_step`, `find_tesseract`. Also test the `_cli.main(argv)` wrapper.
  Run real OCR only when `shutil.which("tesseract")` finds it.
- Check that `result.save(dir)` writes a LAS that `pphys.read` loads, and that values
  round-trip within a pixel's worth of tolerance.

## Report

The test files written, how many tests, the run result, and any bug found (file:line,
inputs, expected, actual).
