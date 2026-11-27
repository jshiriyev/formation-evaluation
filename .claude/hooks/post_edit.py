"""PostToolUse hook for Write/Edit: keep an edited file in line with the repo rules.

pphys/ and tests/ .py files, in order:
  1. syntax and indentation: a SyntaxError/TabError, or tab- and space-indented
     blocks in one file, blocks (CLAUDE.md, "Conventions");
  2. undefined names (ruff F821): names that HEAD did not already have block,
     pre-existing ones are only counted (insight has ~70 of them);
  3. ruff format in the file's own indentation (fmt.py);
  4. the related tests (TESTS below); a failure blocks.
pphys/_families.py and the families block of pages/onepage-wellview.html:
  a parity report against the other side (a reminder, does not block).
index.html, pages/*.html, .github/workflows/pages.yml: the published-link check.

"Blocks" means Claude is told the reason and has to deal with it; the edit
itself stays in place.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fmt  # noqa: E402
from _common import ROOT, emit, payload, relpath, run, tail  # noqa: E402

ALL = ["tests"]
ONEPAGE = [
    "tests/test_layout.py",
    "tests/test_motifs.py",
    "tests/test_pigment.py",
    "tests/test_templix.py",
    "tests/test_unary.py",
    "tests/test_wellview.py",
]
# Edited file (or folder prefix ending in "/") -> tests to run. Anything else
# falls back to tests/test_<name without leading underscore>.py when it exists.
TESTS = {
    "pphys/__init__.py": ALL,
    "tests/conftest.py": ALL,
    "pphys/_lasio.py": [
        "tests/test_welllog.py",
        "tests/test_read.py",
        "tests/test_load.py",
        "tests/test_view.py",
    ],
    "pphys/_read.py": ["tests/test_read.py", "tests/test_load.py"],
    "pphys/_families.py": ["tests/test_families.py", "tests/test_view.py"],
    "pphys/onepage/__init__.py": ONEPAGE,
    "pphys/onepage/_wellview.py": ["tests/test_wellview.py", "tests/test_layout.py"],
    "pphys/onepage/_crossview.py": ["tests/test_motifs.py", "tests/test_pigment.py"],
    "pphys/onepage/_motifs.py": ["tests/test_motifs.py", "tests/test_templix.py"],
    "pphys/onepage/_pigment.py": [
        "tests/test_pigment.py",
        "tests/test_wellview.py",
        "tests/test_motifs.py",
    ],
    "pphys/onepage/_templix.py": ["tests/test_templix.py"],
    "pphys/onepage/wellview/_unary.py": ["tests/test_unary.py", "tests/test_layout.py"],
    "pphys/onepage/wellview/": ["tests/test_layout.py", "tests/test_wellview.py"],
    "pphys/onepage/crossview/": ["tests/test_motifs.py", "tests/test_pigment.py"],
    "pphys/digitize/": ["tests/test_digitize.py"],
}
FAMILIES_JS = (
    "UNIT_SPELLINGS",
    "CANONICAL_UNIT",
    "FAMILIES",
    "canonUnit",
    "function classify",
)


def related_tests(rel: str) -> list[str]:
    if rel.startswith("tests/test_"):
        return [rel]
    if rel in TESTS:
        return TESTS[rel]
    for prefix, tests in TESTS.items():
        if prefix.endswith("/") and rel.startswith(prefix):
            return tests
    guess = f"tests/test_{Path(rel).stem.lstrip('_')}.py"
    return [guess] if (ROOT / guess).exists() else []


def undefined_names(text: str, rel: str) -> list[dict]:
    result = run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select",
            "F821",
            "--no-cache",
            "--output-format",
            "json",
            "--stdin-filename",
            rel,
            "-",
        ],
        stdin=text,
        timeout=30,
    )
    try:
        return json.loads(result.stdout or "[]")
    except ValueError:
        return []


def check_python(rel: str, blocks: list[str], notes: list[str]) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")

    # 1. syntax and indentation
    try:
        compile(text, rel, "exec")
        style = fmt.indent_style(text)
    except SyntaxError as exc:  # TabError and IndentationError included
        blocks.append(f"{rel}:{exc.lineno}: {exc.__class__.__name__}: {exc.msg}")
        return
    if style == "mixed":
        blocks.append(
            f"{rel} mixes tab- and space-indented blocks. CLAUDE.md: indentation is per "
            "file (tabs in onepage/wellview, onepage/crossview, onepage/_crossview.py, "
            "insight/saturation/shalyform, digitize/utils.py; 4 spaces elsewhere); match "
            "the surrounding block."
        )
        return
    siblings = [p for p in path.parent.glob("*.py") if p != path]
    styles = []  # of the siblings with an indented block
    for sibling in siblings:
        try:
            styles.append(fmt.indent_style(sibling.read_text(encoding="utf-8")))
        except (SyntaxError, UnicodeDecodeError):
            pass
    styles = [s for s in styles if s != "none"]
    sibling_styles = set(styles)
    # One sibling is not a folder convention; two or more that agree are.
    if style != "none" and len(styles) >= 2 and len(sibling_styles) == 1 and style not in sibling_styles:
        notes.append(
            f"{rel} is {style}-indented, but every other module in {path.parent.relative_to(ROOT).as_posix()}/ "
            f"uses {sibling_styles.pop()}s. Check that this is intended."
        )

    # 2. undefined names, compared with HEAD
    head = run(["git", "show", f"HEAD:{rel}"], timeout=10)
    before = (
        Counter(e["message"] for e in undefined_names(head.stdout, rel))
        if head.returncode == 0
        else Counter()
    )
    after = undefined_names(text, rel)
    new = Counter(e["message"] for e in after) - before
    if new:
        lines = [
            f"{rel}:{e['location']['row']}: {e['message']}"
            for e in after
            if e["message"] in new
        ]
        blocks.append("New undefined names (ruff F821):\n" + "\n".join(lines))
    elif after:
        notes.append(
            f"{rel} still has {len(after)} undefined name(s) that HEAD already had (ruff F821)."
        )

    # 3. format in the file's own indentation
    changed, problems = fmt.format_files([path])
    if changed:
        notes.append(
            f"{rel} was reformatted by ruff ({style if style != 'none' else 'space'} indentation); re-read it before the next edit."
        )
    notes.extend(problems)

    # 4. related tests
    tests = [t for t in related_tests(rel) if (ROOT / t).exists()]
    if tests:
        result = run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-x",
                "--no-header",
                "-p",
                "no:cacheprovider",
                *tests,
            ],
            timeout=150,
        )
        summary = tail(result.stdout, 1)
        if result.returncode not in (0, 5):  # 5: nothing collected
            blocks.append(
                f"Related tests failed ({' '.join(tests)}):\n{tail(result.stdout)}"
            )
        else:
            notes.append(
                f"Related tests passed ({' '.join(t.removeprefix('tests/') for t in tests)}): {summary}"
            )


def families_report(notes: list[str]) -> None:
    import families_sync

    try:
        diffs = families_sync.compare()
    except Exception as exc:  # a half-edited file should not break the hook
        notes.append(f"Could not compare the curve families: {exc}")
        return
    if diffs:
        notes.append(
            "pphys/_families.py and the JS port in pages/onepage-wellview.html differ "
            "(CLAUDE.md: keep the two in step). Update the other side unless the difference is intended:\n- "
            + "\n- ".join(diffs)
        )


def main() -> None:
    data = payload()
    tool_input = data.get("tool_input") or {}
    rel = relpath(tool_input.get("file_path") or tool_input.get("notebook_path"))
    if not rel or not (ROOT / rel).is_file():
        return

    blocks: list[str] = []
    notes: list[str] = []

    if rel.endswith(".py") and rel.startswith(("pphys/", "tests/")):
        check_python(rel, blocks, notes)

    if rel == "pphys/_families.py":
        families_report(notes)
    elif rel == "pages/onepage-wellview.html":
        edited = " ".join(
            str(tool_input.get(k, "")) for k in ("old_string", "new_string", "content")
        )
        if any(key in edited for key in FAMILIES_JS):
            families_report(notes)

    if rel in ("index.html", ".github/workflows/pages.yml") or (
        rel.startswith("pages/") and rel.endswith(".html")
    ):
        import check_links

        errors = check_links.check()
        if errors:
            blocks.append(
                "Broken links between published Pages files (the Pages workflow would fail):\n"
                + "\n".join(errors)
            )

    context = "\n\n".join(notes)
    if blocks:
        out = {"decision": "block", "reason": "\n\n".join(blocks)}
        if context:
            out["hookSpecificOutput"] = {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            }
        emit(out)
    if context:
        emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context,
                }
            }
        )


if __name__ == "__main__":
    main()
