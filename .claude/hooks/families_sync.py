"""Compare the curve families in pphys/_families.py with their JS port.

pages/onepage-wellview.html carries a copy of the families (name, mnemonic
pattern, identifying units, log scale) and of the unit spellings. CLAUDE.md
asks to keep the two in step; this lists every difference. Colours are not
compared (the page uses its own palette), nor ranges/smooth (QC only).

    uv run python .claude/hooks/families_sync.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, utf8_stdout  # noqa: E402

PAGE = ROOT / "pages" / "onepage-wellview.html"
JS_STR = r"'((?:[^'\\]|\\.)*)'"
JS_FAMILY = re.compile(
    rf"\[\s*{JS_STR}\s*,\s*{JS_STR}\s*,\s*\[([^\]]*)\]\s*,\s*(true|false)\s*,\s*{JS_STR}\s*\]"
)


def _unescape(s: str) -> str:
    return re.sub(r"\\(.)", r"\1", s)


def _strings(s: str) -> tuple[str, ...]:
    return tuple(_unescape(m) for m in re.findall(JS_STR, s))


def js_side() -> tuple[list[tuple], dict[str, tuple[str, ...]]]:
    text = PAGE.read_text("utf-8")
    block = re.search(r"const FAMILIES = \[(.*?)\]\.map\(", text, re.S)
    units = re.search(r"const UNIT_SPELLINGS = \{(.*?)\};", text, re.S)
    if not block or not units:
        raise ValueError(f"FAMILIES or UNIT_SPELLINGS not found in {PAGE.name}")
    families = [
        (_unescape(n), _unescape(p), _strings(u), log == "true")
        for n, p, u, log, _color in JS_FAMILY.findall(block.group(1))
    ]
    spellings = {
        _unescape(k): _strings(v)
        for k, v in re.findall(rf"{JS_STR}\s*:\s*\[([^\]]*)\]", units.group(1))
    }
    return families, spellings


def py_side() -> tuple[list[tuple], dict[str, tuple[str, ...]]]:
    sys.path.insert(0, str(ROOT))
    from pphys import _families

    families = [
        (f.name, f.pattern, tuple(f.units), f.log_scale) for f in _families.FAMILIES
    ]
    return families, {k: tuple(v) for k, v in _families._UNIT_SPELLINGS.items()}


def compare() -> list[str]:
    """Return the differences, Python side first (empty when in step)."""
    py_fam, py_units = py_side()
    js_fam, js_units = js_side()
    diffs = []

    py_names = [f[0] for f in py_fam]
    js_names = [f[0] for f in js_fam]
    for name in py_names:
        if name not in js_names:
            diffs.append(f"family '{name}' is missing from the JS FAMILIES")
    for name in js_names:
        if name not in py_names:
            diffs.append(f"family '{name}' exists only in the JS FAMILIES")
    common = [n for n in py_names if n in js_names]
    if common != [n for n in js_names if n in py_names]:
        diffs.append(
            "family order differs (first match wins, so order matters): "
            f"Python {common} vs JS {[n for n in js_names if n in py_names]}"
        )

    js_by_name = {f[0]: f for f in js_fam}
    for name, pattern, units, log in py_fam:
        js = js_by_name.get(name)
        if not js:
            continue
        if pattern != js[1]:
            diffs.append(
                f"'{name}' pattern differs:\n    py: {pattern}\n    js: {js[1]}"
            )
        if units != js[2]:
            diffs.append(f"'{name}' units differ: py {units} vs js {js[2]}")
        if log != js[3]:
            diffs.append(f"'{name}' log scale differs: py {log} vs js {js[3]}")

    for canon in sorted(set(py_units) | set(js_units)):
        py, js = set(py_units.get(canon, ())), set(js_units.get(canon, ()))
        if canon not in js_units:
            diffs.append(f"unit '{canon}' is missing from the JS UNIT_SPELLINGS")
        elif canon not in py_units:
            diffs.append(f"unit '{canon}' exists only in the JS UNIT_SPELLINGS")
        elif py != js:
            only_py, only_js = sorted(py - js), sorted(js - py)
            diffs.append(
                f"unit '{canon}' spellings differ: only in py {only_py}, only in js {only_js}"
            )
    return diffs


def main() -> int:
    utf8_stdout()
    diffs = compare()
    for diff in diffs:
        print(diff)
    print(
        "families in step" if not diffs else f"{len(diffs)} difference(s)",
        file=sys.stderr,
    )
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
