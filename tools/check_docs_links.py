#!/usr/bin/env python3
"""
Simple link checker for Markdown docs.

Scans markdown files under docs/ and reports any relative links that do not
resolve to an existing file. HTTP/HTTPS/mailto links are ignored.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS_ROOT = Path(__file__).resolve().parents[1] / "docs"
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def is_relative(path: str) -> bool:
    return not (
        path.startswith("http://")
        or path.startswith("https://")
        or path.startswith("mailto:")
        or path.startswith("#")
    )


def check_file(md_path: Path) -> list[str]:
    missing: list[str] = []
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    for match in LINK_PATTERN.finditer(text):
        target = match.group(1).split("#", 1)[0]
        if not target or not is_relative(target):
            continue
        candidate = (md_path.parent / target).resolve()
        if not candidate.exists():
            rel = candidate.relative_to(DOCS_ROOT.parent)
            missing.append(f"{md_path.relative_to(DOCS_ROOT.parent)} -> {rel}")
    return missing


def main() -> int:
    if not DOCS_ROOT.exists():
        print("docs/ not found; nothing to check.")
        return 0

    missing_links: list[str] = []
    for md_path in DOCS_ROOT.rglob("*.md"):
        missing_links.extend(check_file(md_path))

    if missing_links:
        print("Broken links found:")
        for item in missing_links:
            print(f" - {item}")
        return 1

    print("All checked docs links resolved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
