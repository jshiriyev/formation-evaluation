"""Format Python files with ruff, keeping each file's own indentation.

The repository mixes tab-indented and 4-space-indented modules (CLAUDE.md,
"Conventions"). A bare ``ruff format`` turns tabs into spaces, so this script
detects the indentation of every file and formats it in that style, with
quotes left as they are.

    uv run python .claude/hooks/fmt.py [--check] [paths ...]   # default: pphys tests

Exit status 1 with --check when a file would change, or when a file cannot be
formatted (mixed indentation, syntax error).
"""

from __future__ import annotations

import io
import subprocess
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATHS = ("pphys", "tests")
QUOTES = "format.quote-style='preserve'"


def indent_style(text: str) -> str:
    """Return "tab", "space", "none" (no indented block) or "mixed".

    Only real indentation counts (INDENT tokens), not whitespace inside
    strings. Raises SyntaxError (TabError included) for code that does not
    tokenize.
    """
    kinds = set()
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.INDENT:
            if "\t" in token.string:
                kinds.add("tab")
            if " " in token.string:
                kinds.add("space")
    if len(kinds) > 1:
        return "mixed"
    return kinds.pop() if kinds else "none"


def collect(paths) -> list[Path]:
    files = []
    for name in paths or DEFAULT_PATHS:
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path
        if path.is_dir():
            files.extend(
                p for p in sorted(path.rglob("*.py")) if "__pycache__" not in p.parts
            )
        elif path.suffix == ".py" and path.exists():
            files.append(path)
    return files


def format_files(files, check: bool = False) -> tuple[list[Path], list[str]]:
    """Format ``files`` in place (or only check them).

    Returns (files that changed or would change, problems that kept a file
    from being formatted).
    """
    groups: dict[str, list[Path]] = {"tab": [], "space": []}
    problems = []
    for path in files:
        try:
            style = indent_style(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError) as exc:
            problems.append(
                f"{_rel(path)}: not formatted, {exc.__class__.__name__}: {exc}"
            )
            continue
        if style == "mixed":
            problems.append(
                f"{_rel(path)}: not formatted, it mixes tab- and space-indented blocks"
            )
            continue
        groups["tab" if style == "tab" else "space"].append(path)

    changed = []
    for style, paths in groups.items():
        if not paths:
            continue
        before = {p: p.read_bytes() for p in paths}
        args = [sys.executable, "-m", "ruff", "format", "--no-cache"]
        args += ["--config", QUOTES, "--config", f"format.indent-style='{style}'"]
        if check:
            args.append("--check")
        result = subprocess.run(
            args + [str(p) for p in paths],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if check:
            changed += [p for p in paths if _rel(p) in result.stdout.replace("\\", "/")]
        else:
            changed += [p for p in paths if p.read_bytes() != before[p]]
        if result.returncode not in (0, 1):
            problems.append(result.stderr.strip() or result.stdout.strip())
    return changed, problems


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    files = collect([a for a in argv if a != "--check"])
    changed, problems = format_files(files, check=check)
    verb = "would reformat" if check else "reformatted"
    for path in changed:
        print(f"{verb} {_rel(path)}")
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(changed)} of {len(files)} files {verb}", file=sys.stderr)
    return 1 if problems or (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
