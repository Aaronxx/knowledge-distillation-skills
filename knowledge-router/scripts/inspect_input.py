#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantify knowledge input(s) for knowledge-router.

Usage:
    python inspect_input.py <path> [path2 ...]   # files and/or directories

For URLs, do NOT call this script - fetch the page first, save as a temp
markdown file, then pass the file here.

Size unit: "CJK-equivalent" = CJK chars + English words * 1.6.
One A4 page at 10pt / 1.55 line-height holds about 850 CJK-equivalent units.
"""

import re
import sys
from pathlib import Path

TEXT_EXTS = {".md", ".markdown", ".txt"}
DISTILL_ONE = 850        # <= this -> 1 page
DISTILL_TWO = 3000       # <= this -> 1-2 pages
DOCS_SUBTopic = 3000     # above this + many H2 -> docs-to-knowledge
DOCS_LARGE = 8000        # above this -> docs-to-knowledge
MULTI_MIN = 1500         # multi-doc below this total -> too small for 3+ pages


def cjk_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", text))


def inspect_file(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    body = re.sub(r"```.*?```", "", raw, flags=re.S)          # code blocks: not prose
    cjk = cjk_count(body)
    words = word_count(body)
    effective = cjk + round(words * 1.6)
    h2 = len(re.findall(r"(?m)^##\s+\S", raw))
    h3 = len(re.findall(r"(?m)^###\s+\S", raw))
    return {
        "file": str(path),
        "cjk": cjk,
        "words": words,
        "effective": effective,
        "lines": raw.count("\n") + 1,
        "h2": h2,
        "h3": h3,
    }


def collect(args: list) -> list:
    files = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            files.extend(sorted(
                f for f in p.rglob("*")
                if f.suffix.lower() in TEXT_EXTS and not f.name.startswith("~$")
            ))
        elif p.is_file():
            files.append(p)
        else:
            print(f"[SKIP] not found: {a}", file=sys.stderr)
    return files


def suggest(n_files: int, total: int, max_h2: int) -> str:
    if n_files >= 2:
        if total < MULTI_MIN:
            return (f"ASK - multi-doc total {total} < {MULTI_MIN}; "
                    f"suggest distill-onepager 1 page or a plain summary, confirm with user")
        return "docs-to-knowledge (multi-doc)"
    if total <= DISTILL_ONE:
        return "distill-onepager (1 page)"
    if total <= DISTILL_TWO:
        return "distill-onepager (1-2 pages, default 2)"
    if total <= DOCS_LARGE:
        if max_h2 >= 5:
            return "docs-to-knowledge (single doc, many subtopics)"
        return "distill-onepager (2 pages)"
    return "docs-to-knowledge (single doc, very large)"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python inspect_input.py <path> [path2 ...]", file=sys.stderr)
        return 2
    files = collect(sys.argv[1:])
    if not files:
        print("No readable text files found.", file=sys.stderr)
        return 1

    total = 0
    total_words = 0
    max_h2 = 0
    print("== inspect_input ==")
    for f in files:
        s = inspect_file(f)
        total += s["effective"]
        total_words += s["words"]
        max_h2 = max(max_h2, s["h2"])
        print(f"  {s['file']}  cjk={s['cjk']} words={s['words']} "
              f"eff={s['effective']} h2={s['h2']} h3={s['h3']}")
    n = len(files)
    print(f"files: {n}")
    print(f"total CJK-equivalent: {total} (english words: {total_words}, weight 1.6)")
    print(f"max h2 in one file: {max_h2}")
    print(f"suggested route: {suggest(n, total, max_h2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
