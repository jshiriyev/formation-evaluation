"""Helpers shared by the Claude Code hooks in this folder (standard library only)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def payload() -> dict:
    """The hook input that Claude Code sends as JSON on stdin."""
    try:
        return json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except ValueError:
        return {}


def relpath(path: str | None) -> str | None:
    """``path`` relative to the repository root, POSIX style; None if outside it."""
    if not path:
        return None
    if os.name == "nt":
        # Git Bash spelling /c/Users/... -> C:/Users/...
        path = re.sub(r"^/([a-zA-Z])/", r"\1:/", path)
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def run(args: list[str], timeout: float | None = None, stdin: str | None = None):
    """Run a command at the repository root and capture its text output."""
    return subprocess.run(
        args,
        cwd=ROOT,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def emit(obj: dict) -> None:
    """Print the hook's JSON answer and exit successfully."""
    sys.stdout.write(json.dumps(obj))
    sys.exit(0)


def utf8_stdout() -> None:
    """Write UTF-8 to a Windows console or pipe (unit spellings include '°')."""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")


def tail(text: str, lines: int = 40) -> str:
    rows = text.strip().splitlines()
    return "\n".join(rows[-lines:])
