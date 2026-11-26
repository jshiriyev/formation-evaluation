---
name: fix-insight-imports
description: Port pphys.insight modules off the old borepy package name to pphys/insight/_trim.py, fix their other undefined names, and add tests including the Archie limit (a shaly-sand model at Vsh=0 must equal Archie). Use when working on an insight module that fails to import.
argument-hint: "[module path | all]"
allowed-tools: Bash(uv run *), Bash(git diff*), Bash(git status*), Read, Edit, Write, Grep, Glob
---

# /fix-insight-imports

Target: `$ARGUMENTS`: a module path such as
`pphys/insight/saturation/_archie.py`, or `all` / empty for every module that still has
`from borepy.utils._wrappers import trim`
(`uv run ruff check pphys/insight --select F821 --no-cache` and a grep for `borepy`
show the scope; `all` means do them one module at a time, smallest first).

## Facts that matter

- `pphys/insight/__init__.py` is empty and several subfolders have no `__init__.py`
  (namespace packages). Use the absolute import `from pphys.insight._trim import trim`,
  which works from any of them.
- `@trim` clips the result to `[lower, upper]` (default 0..1) and adds those keyword
  arguments to the call; keep it on the same methods.
- Indentation is per file: `insight/saturation/shalyform/*` and
  `insight/permeability/_resistivity.py` use tabs, the rest 4 spaces. The edit hook
  formats and checks this; match the file anyway.
- Shaly-sand models take an `archie` instance for a/m/n
  (`simandoux(archie(m=2)).sw(phi, vsh, rw, rsh, rt)`); implicit ones (simandoux,
  totalshale, dualwater, dispersed) solve each sample with
  `scipy.optimize.root_scalar` (Newton, `x0=1`).
- Matrix constants live in `pphys/insight/lithology/_lithology.json` (not yet wired
  into `neuden`, `mnplot`, `sonneu`); don't wire them in as part of this.

## Steps (per module)

1. Replace the `borepy` import. Then fix the module's other F821 names
   (`uv run ruff check <file> --select F821 --no-cache`): a missing `import numpy`, a
   misspelled variable. If a fix needs a modelling decision (which formula, which
   default), stop and ask rather than guessing.
2. Prove it imports: `uv run python -c "import pphys.insight.<dotted.module>"`.
3. Add tests in `tests/test_insight_<topic>.py` (4-space indentation, plain numpy
   arrays, `pytest.approx`/`numpy.testing`):
   - a hand-computed value from the textbook formula for typical inputs;
   - shaly-sand models: Vsh=0 (or Swb=0) reduces to `archie(...).sw` for the same a/m/n;
   - `@trim`: outputs inside `[0, 1]` by default and the `lower`/`upper` kwargs work;
   - vector input of several samples gives the same as one sample at a time.
   The **test-writer** agent can draft these; the **petrophysics-reviewer** agent
   can check the formulas.
4. `uv run pytest tests/test_insight_<topic>.py -q`. A failing physics test means a
   bug in the model: report it with the expected and actual numbers, don't bend the
   test to pass.

## Report

Per module: import fixed (yes/no), other names fixed, tests added (count), and any
formula that looks wrong, with the line and the textbook form.
