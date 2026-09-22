#!/usr/bin/env python3
"""Extract mechanical proof-of-read from text or Markdown files.

For Markdown, --heading selects a heading exactly as written, including # marks
or by heading text if an exact full-heading match is not found.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def words(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def first_last_five(text: str) -> tuple[list[str], list[str]]:
    ws = words(text)
    if len(ws) < 10:
        return ws, ws
    return ws[:5], ws[-5:]


def heading_level(line: str) -> int | None:
    m = re.match(r"^(#{1,6})\s+", line)
    return len(m.group(1)) if m else None


def markdown_heading_levels(lines: list[str]) -> list[int | None]:
    """Locate ATX headings, excluding backtick and tilde fenced code blocks."""
    levels: list[int | None] = []
    fence_char: str | None = None
    fence_length = 0
    for line in lines:
        stripped = line.rstrip("\r\n")
        if fence_char is not None:
            closing = r" {0,3}" + re.escape(fence_char) + "{" + str(fence_length) + r",}[ \t]*"
            if re.fullmatch(closing, stripped):
                fence_char = None
            levels.append(None)
            continue

        opening = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", stripped)
        if opening and (opening.group(1)[0] != "`" or "`" not in opening.group(2)):
            fence_char = opening.group(1)[0]
            fence_length = len(opening.group(1))
            levels.append(None)
        else:
            levels.append(heading_level(stripped))
    return levels


def select_markdown_section(lines: list[str], heading: str | None) -> tuple[str, int, int, str]:
    if not heading:
        return "FULL_FILE", 1, len(lines), "".join(lines)

    # Try exact line match first, then heading text match.
    start_idx = None
    start_level = None
    levels = markdown_heading_levels(lines)

    for i, line in enumerate(lines):
        stripped = line.rstrip("\n")
        if levels[i] is not None and stripped == heading:
            start_idx = i
            start_level = levels[i]
            break

    if start_idx is None:
        wanted = heading.strip().lstrip("#").strip()
        for i, line in enumerate(lines):
            stripped = line.rstrip("\n")
            if levels[i] is not None and stripped.lstrip("#").strip() == wanted:
                start_idx = i
                start_level = levels[i]
                break

    if start_idx is None:
        raise ValueError(f"heading not found: {heading!r}")

    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        lvl = levels[j]
        if lvl is not None and start_level is not None and lvl <= start_level:
            end_idx = j
            break

    return lines[start_idx].rstrip("\n"), start_idx + 1, end_idx, "".join(lines[start_idx:end_idx])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--heading", help="Markdown heading to inspect")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.path.exists():
        raise SystemExit(f"missing file: {args.path}")

    text = args.path.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    heading, start, end, section = select_markdown_section(lines, args.heading)

    first5, last5 = first_last_five(section)

    report = {
        "source": str(args.path),
        "heading": heading,
        "line_range": [start, end],
        "first_5_words": first5,
        "last_5_words": last5,
        "word_count": len(words(section)),
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"source: {report['source']}")
        print(f"heading: {report['heading']}")
        print(f"line_range: {start}-{end}")
        print("first_5_words: " + " ".join(first5))
        print("last_5_words: " + " ".join(last5))
        print(f"word_count: {report['word_count']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
