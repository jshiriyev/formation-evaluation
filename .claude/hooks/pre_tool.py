"""PreToolUse hook: guards that permission rules alone cannot express.

Bash / PowerShell:
  - deny any `git push` that would update main: an explicit main refspec,
    --all/--mirror, a +refspec (force), or a bare push while main is checked
    out. Pushes to main deploy GitHub Pages, so they are left to the user.
  - ask before running notebooks/*.py, which import the removed pre-rename API.
Edit / Write / NotebookEdit:
  - ask before editing notebooks/*.py, for the same reason.
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import emit, payload, relpath, run  # noqa: E402

MAIN = "main"
STALE = (
    "notebooks/*.py are stale: they import the pre-rename API (pphys.visualization, "
    "Formation, Correlation, Weaver, lasview) and do not run against the current package. "
    "The maintained examples are the notebooks/*.ipynb."
)
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def decide(decision: str, reason: str) -> None:
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        }
    )


def segments(command: str):
    """Split a shell command line into simple commands (approximately)."""
    for part in re.split(r"&&|\|\||[;|\n]", command):
        try:
            words = shlex.split(part, posix=True)
        except ValueError:
            words = part.split()
        if words:
            yield words


def current_branch() -> str:
    result = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=10)
    return result.stdout.strip()


def push_problem(words: list[str]) -> str | None:
    """Why this git command may not run, or None."""
    if not words or Path(words[0]).name.lower() not in ("git", "git.exe"):
        return None
    i = 1
    while i < len(words) and words[i].startswith("-"):  # git -C dir -c k=v push ...
        i += 2 if words[i] in GIT_GLOBAL_WITH_VALUE else 1
    if i >= len(words) or words[i] != "push":
        return None

    args = words[i + 1 :]
    positional = []
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg in ("--all", "--mirror"):
            return f"`git push {arg}` would update {MAIN}"
        if arg in ("-o", "--push-option", "--repo", "--receive-pack", "--exec"):
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        positional.append(arg)

    refspecs = positional[1:]  # positional[0] is the remote
    if not refspecs:
        branch = current_branch()
        if branch == MAIN:
            return f"a bare `git push` while {MAIN} is checked out would update {MAIN}"
        return None
    for spec in refspecs:
        if spec.startswith("+"):
            return f"`{spec}` is a force push"
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        dst = dst.removeprefix("refs/heads/")
        if dst == MAIN or (dst == "HEAD" and current_branch() == MAIN):
            return f"`{spec}` would update {MAIN}"
    return None


def main() -> None:
    data = payload()
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}

    if tool in ("Bash", "PowerShell"):
        command = tool_input.get("command", "")
        for words in segments(command):
            problem = push_problem(words)
            if problem:
                decide(
                    "deny",
                    f"Blocked by .claude/hooks/pre_tool.py: {problem}. Force pushes and pushes "
                    f"to {MAIN} (which deploys GitHub Pages) are left to the user in this repo. "
                    "Push a branch without forcing, or ask the user to do it.",
                )
        if re.search(r"notebooks[/\\][^\s'\"]+\.py\b", command) and re.search(
            r"\b(python3?|py|uv\s+run|pytest|exec\(|runpy)\b", command
        ):
            decide("ask", STALE)

    elif tool in ("Edit", "Write", "NotebookEdit"):
        rel = relpath(tool_input.get("file_path") or tool_input.get("notebook_path"))
        if rel and re.fullmatch(r"notebooks/[^/]+\.py", rel):
            decide(
                "ask",
                STALE + " Edit it only if you mean to port it to the current API.",
            )


if __name__ == "__main__":
    main()
