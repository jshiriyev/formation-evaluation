"""Check the links between the files published to GitHub Pages.

Mirrors the "Check the links between published files" step of
.github/workflows/pages.yml, so a broken link is caught before pushing. The
published files are read from the `cp` lines of its "Assemble the site" step,
so this stays in step with the workflow.

    uv run python .claude/hooks/check_links.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, utf8_stdout  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
LINK = re.compile(r"""(?:href|src)="([^"]*)"|_URL = '([^']*)'""")


def published() -> set[str]:
    """Repository paths that the workflow copies into the site."""
    files = set()
    for match in re.finditer(
        r"^\s*cp\s+(\S+)\s+_site/", WORKFLOW.read_text("utf-8"), re.M
    ):
        files.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob(match.group(1)))
    return files


def check() -> list[str]:
    """Return one message per broken link (empty when everything resolves)."""
    site = published()
    errors = []
    for page in sorted(p for p in site if p.endswith(".html")):
        text = (ROOT / page).read_text("utf-8")
        for match in LINK.finditer(text):
            link = re.sub(r"[?#].*", "", match.group(1) or match.group(2) or "")
            if not link or re.match(r"^[a-z]+:", link) or link.startswith("//"):
                continue
            target = PurePosixPath(page).parent / link
            if link.endswith("/"):
                target /= "index.html"
            parts = []
            for part in target.parts:  # normalize ../ without touching the disk
                if part == "..":
                    if parts:
                        parts.pop()
                elif part != ".":
                    parts.append(part)
            target = "/".join(parts)
            if target in site:
                continue
            line = text.count("\n", 0, match.start()) + 1
            if (ROOT / target).is_file():
                why = f"exists in the repo but is not published; add it to the 'Assemble the site' step (and the push paths) of {WORKFLOW.relative_to(ROOT).as_posix()}"
            else:
                why = "does not exist"
            errors.append(f"{page}:{line}: {link} -> {target} {why}")
    return errors


def main() -> int:
    utf8_stdout()
    errors = check()
    for error in errors:
        print(error)
    print(
        f"{len(errors)} broken link(s) in {len(published())} published files",
        file=sys.stderr,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
