#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for knowledge-router's size quantification and routing.

Usage:
    python scripts/test_router.py

Generates temporary fixtures, calls inspect_file()/suggest(), and asserts the
expected route. No network, no external files beyond the skill itself.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inspect_input import inspect_file, suggest  # noqa: E402

FILLER = "这是用于测试路由的填充文本。"  # 13 CJK chars per repeat


def make_doc(path: Path, cjk: int, h2: int, english_words: int = 0) -> None:
    parts = []
    for i in range(h2):
        parts.append(f"## 小节 {i + 1}\n")
    reps = max(1, cjk // 13)
    parts.append(FILLER * reps)
    if english_words:
        parts.append(" " + " ".join(["word"] * english_words))
    path.write_text("\n".join(parts), encoding="utf-8")


def run_case(name: str, path: Path, expected: str) -> bool:
    s = inspect_file(path)
    got = suggest(1, s["effective"], s["h2"])
    ok = expected in got
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: eff={s['effective']} h2={s['h2']} -> {got}")
    return ok


def main() -> int:
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)

        p = d / "small.md"; make_doc(p, 500, 1)
        results.append(run_case("single 500 CJK", p, "distill-onepager (1 page)"))

        p = d / "mid.md"; make_doc(p, 1500, 2)
        results.append(run_case("single 1500 CJK", p, "distill-onepager (1-2 pages"))

        p = d / "mid2.md"; make_doc(p, 4000, 3)
        results.append(run_case("single 4000 CJK / 3 H2", p, "distill-onepager (2 pages)"))

        p = d / "many.md"; make_doc(p, 6000, 6)
        results.append(run_case("single 6000 CJK / 6 H2", p, "docs-to-knowledge"))

        p = d / "large.md"; make_doc(p, 9000, 8)
        results.append(run_case("single 9000 CJK", p, "docs-to-knowledge"))

        p = d / "en1.md"; make_doc(p, 0, 2, english_words=400)
        results.append(run_case("english 400 words", p, "distill-onepager (1 page)"))

        p = d / "en2.md"; make_doc(p, 0, 3, english_words=2000)
        results.append(run_case("english 2000 words", p, "distill-onepager (2 pages)"))

        # multi-doc: 2 files x 1000 = 2000
        a = d / "a.md"; make_doc(a, 1000, 1)
        b = d / "b.md"; make_doc(b, 1000, 1)
        total = inspect_file(a)["effective"] + inspect_file(b)["effective"]
        got = suggest(2, total, 1)
        ok = "docs-to-knowledge" in got
        print(f"[{'PASS' if ok else 'FAIL'}] multi 2x1000: total={total} -> {got}")
        results.append(ok)

        # multi-doc too small: 2 files x 300 = 600
        c = d / "c.md"; make_doc(c, 300, 1)
        e = d / "e.md"; make_doc(e, 300, 1)
        total = inspect_file(c)["effective"] + inspect_file(e)["effective"]
        got = suggest(2, total, 1)
        ok = got.startswith("ASK")
        print(f"[{'PASS' if ok else 'FAIL'}] multi too small: total={total} -> {got}")
        results.append(ok)

    passed = sum(1 for r in results if r)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
