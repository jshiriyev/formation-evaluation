"""Stop hook: run the full test suite when pphys/ or tests/ changed.

At the end of a turn, the Python files under pphys/ and tests/ are
fingerprinted (HEAD trees plus every uncommitted .py file there, edits made
through Bash included). pytest runs only when the fingerprint differs from the
one last evaluated in this session, so a turn that changed nothing costs
nothing. A failure sends Claude back to fix it; if the same failing state
comes back, or after three failed rounds in a row, the user is told instead,
so the hook never loops.

    stop_tests.py             Stop hook
    stop_tests.py --baseline  SessionStart hook: remember the state the session started from
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, emit, payload, run, tail  # noqa: E402

DIRS = ("pphys", "tests")
MAX_ROUNDS = 3


def fingerprint() -> str:
    digest = hashlib.sha1()
    for d in DIRS:
        digest.update(
            run(["git", "rev-parse", f"HEAD:{d}"], timeout=10).stdout.encode()
        )
    status = run(
        ["git", "status", "--porcelain", "-uall", "--", *DIRS], timeout=20
    ).stdout
    for line in sorted(status.splitlines()):
        path = line[3:].split(" -> ")[-1].strip('"')
        if not path.endswith(".py"):
            continue
        digest.update(line.encode())
        file = ROOT / path
        if file.is_file():
            digest.update(file.read_bytes())
    return digest.hexdigest()


def state_file(session: str) -> Path:
    root = hashlib.sha1(str(ROOT).lower().encode()).hexdigest()[:10]
    folder = Path(tempfile.gettempdir()) / "claude-pphys-hooks"
    folder.mkdir(exist_ok=True)
    return folder / f"{root}-{session or 'nosession'}.json"


def main() -> None:
    data = payload()
    path = state_file(data.get("session_id", ""))
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError):
        state = {}

    current = fingerprint()

    if "--baseline" in sys.argv:
        if "last" not in state:  # keep the baseline of a resumed session
            path.write_text(
                json.dumps({"last": current, "status": "baseline", "rounds": 0})
            )
        return

    if state.get("last") == current:
        if state.get("status") == "failed":
            emit(
                {
                    "systemMessage": "pytest is still failing (nothing changed since the last run). Run `uv run python -m pytest` to see it."
                }
            )
        return

    result = run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
        timeout=540,
    )
    summary = tail(result.stdout, 1)
    passed = result.returncode in (0, 5)
    rounds = 0 if passed else state.get("rounds", 0) + 1
    path.write_text(
        json.dumps(
            {
                "last": current,
                "status": "passed" if passed else "failed",
                "rounds": rounds,
            }
        )
    )

    if passed:
        emit({"systemMessage": f"pytest after this turn's changes: {summary}"})
    if rounds > MAX_ROUNDS:
        emit(
            {
                "systemMessage": f"pytest still fails after {MAX_ROUNDS} rounds of fixes: {summary}. Stopping here; run `uv run python -m pytest` to see it."
            }
        )
    emit(
        {
            "decision": "block",
            "reason": "The full test suite fails after this turn's changes (Stop hook, .claude/hooks/stop_tests.py). "
            "Fix the failures, or explain why they are expected, before finishing:\n\n"
            + tail(result.stdout, 60),
        }
    )


if __name__ == "__main__":
    main()
