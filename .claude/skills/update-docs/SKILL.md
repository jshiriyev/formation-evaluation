---
name: update-docs
description: After an API change, bring CLAUDE.md, doc/wellview.md, doc/lasview.md, the README and the WellView web-app contract back in line with the code. Use when public classes, methods, arguments or behaviour in pphys changed, or when asked to update the docs.
argument-hint: "[git range, default: changes since main]"
allowed-tools: Bash(git diff*), Bash(git log*), Bash(git status*), Bash(uv run *), Read, Edit, Grep, Glob
---

# /update-docs

Range: `$ARGUMENTS`, or `main...HEAD` plus uncommitted changes when empty.

## Steps

1. **What changed.** `git diff <range> --stat -- pphys`, then read the diffs of the
   public surface: what each package `__init__.py` re-exports, public class and method
   names, parameters and defaults, return values, raised errors, and behaviour that a
   user can see (e.g. a fill now clipped, a default tick spacing). Ignore pure
   refactors and formatting.
2. **Where it is documented.** Grep for every changed name in:
   - `CLAUDE.md`: architecture notes for Claude. Keep its style: short bullets,
     facts about behaviour and pitfalls, no tutorials.
   - `doc/wellview.md` (WellView reference), `doc/lasview.md` (LasView reference).
   - `README.md`: it still documents the removed `pphys.stream` (Bokeh) and
     `pphys.maxwres`. Point this out; remove those sections only if the user agrees.
   - `pages/onepage-wellview.html`: the payload contract comment at the top of its
     script mirrors the WellView API (`layout`, `calls` of `{method, args, kwargs}`,
     `output`). A renamed method or keyword must change there, and in the JS that
     builds the payload.
   - Notebook markdown cells that describe the API (`notebooks/*.ipynb`).
3. **Edit.** Update each place to match the code exactly (names, defaults, units).
   Don't document planned behaviour as if it existed.
4. **Verify examples.** Extract the Python code blocks of every doc you edited into a
   scratchpad script and run them with `uv run python` (Agg backend; data paths
   relative to the repo root). Fix the docs, not the code, when an example is wrong;
   if the code looks wrong, say so instead.
5. If a notebook demonstrates changed behaviour, suggest `/rerun-notebook <name>`.

## Report

A list of the files edited, each with a one-line summary, plus anything left
undocumented on purpose or needing the user's decision.
