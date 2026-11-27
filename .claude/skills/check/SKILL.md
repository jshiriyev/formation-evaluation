---
name: check
description: Pre-push gate for pphys. Runs the undefined-name scan, the format check, the full test suite, the GitHub Pages link check, the curve-families parity check and a stale-import scan, then gives a go/no-go summary. Use before pushing or opening a PR, or when asked whether the branch is ready.
argument-hint: "[--fix]"
allowed-tools: Bash(uv run *), Bash(git status*), Bash(git diff*), Bash(git log*), Bash(git branch*), Bash(git rev-parse*), Read, Grep, Glob
---

# /check: pre-push gate

Run every step even when an earlier one fails, then report. Run independent
steps in parallel. With `--fix` ($ARGUMENTS), fix what is safely mechanical
(formatting, a new undefined name, a broken link) and re-run that step; never
"fix" a failing test by editing the test's expectation.

## Steps

1. **Branch and tree.** `git branch --show-current`, `git status --short`,
   `git log --oneline @{upstream}..HEAD 2>/dev/null` (unpushed commits).
   On `main`: say that pushing it is left to the user (the pre-tool hook denies it).
2. **Undefined names.** `uv run ruff check pphys tests --no-cache --select F821 --output-format concise`.
   About 70 hits in `pphys/insight/` are pre-existing (old `borepy` era). To tell
   **new** hits (no-go) from known ones (note only), take the .py files changed since
   `main` (`git diff --name-only main -- '*.py'`) and, for each, count the hits in the
   `main` version too:
   `git show main:<file> | uv run ruff check --select F821 --no-cache --stdin-filename <file> -`.
   A name is new when the current file has more hits for it than `main` had.
3. **Format.** `uv run python .claude/hooks/fmt.py --check`. Never use bare
   `ruff format`; it would turn the tab-indented modules into spaces.
4. **Tests.** `uv run pytest -q`.
5. **Pages links.** `uv run python .claude/hooks/check_links.py` (the same check the
   Pages workflow runs on `index.html`, `pages/*.html`).
6. **Families parity.** `uv run python .claude/hooks/families_sync.py`
   (`pphys/_families.py` vs the JS port in `pages/onepage-wellview.html`).
   Differences are a no-go only if this branch touched either file
   (`git diff --name-only main...HEAD`); otherwise list them as known drift.
7. **Stale imports.** Grep `pphys/`, `tests/`, `doc/`, `README.md` and the `.ipynb`
   notebooks for `borepy`, `pphys.visualization`, `pphys.stream`, `pphys.maxwres`,
   `Correlation`, `Weaver`, `lasview` (lower-case module) and `Formation(`.
   Known and expected: `borepy` in `pphys/insight/` (fixed by `/fix-insight-imports`)
   and anything in `notebooks/*.py`. Anything else is new; `pphys.stream` and
   `pphys.maxwres` are out of scope (ROADMAP.md) and must not reappear in the docs.
8. **README status.** If this branch finished a ROADMAP.md item, check that the item is
   ticked and the README's workflow table shows the new status.

## Report

A table with one row per step: ✅ / ⚠️ (known, pre-existing) / ❌ (new problem),
and a one-line detail. Then the verdict: **GO** (no ❌) or **NO-GO**, followed by
the ❌ items with file:line and the smallest fix for each. Keep it short.
