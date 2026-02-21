#!/usr/bin/env python3
"""
Autofix missing `_works.title_sort` for numeric titles.

Policy:
- Only patches files where:
  - front matter has a `title` containing at least one digit, and
  - front matter is missing `title_sort`.
- Dry-run by default; pass `--write` to apply changes.
"""

import argparse
import re
from pathlib import Path
from typing import Any, Optional, Set


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def yaml_quote(s: str) -> str:
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def numeric_aware_sort_key(value: Any, width: int = 3) -> str:
    s = normalize_text(value)
    if not s:
        return ""
    return re.sub(r"\d+", lambda m: m.group(0).zfill(width), s)


def parse_scalar(raw: str) -> Optional[str]:
    v = raw.strip()
    if v == "" or v == "null":
        return None
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def parse_work_id_selection(expr: str) -> Set[str]:
    out: Set[str] = set()
    if not expr:
        return out
    token_re = re.compile(r"^[0-9]+(?:-[0-9]+)?$")
    for raw in expr.split(","):
        token = raw.strip()
        if not token:
            continue
        if not token_re.fullmatch(token):
            raise SystemExit(f"Invalid --work-ids token: {token}")
        if "-" in token:
            a_raw, b_raw = token.split("-", 1)
            a, b = int(a_raw), int(b_raw)
            if a > b:
                a, b = b, a
            for n in range(a, b + 1):
                out.add(f"{n:05d}")
        else:
            out.add(f"{int(token):05d}")
    return out


def extract_work_id(fm_lines: list[str]) -> str:
    for line in fm_lines:
        m = re.match(r"^work_id:\s*(.*)$", line)
        if not m:
            continue
        v = parse_scalar(m.group(1))
        return normalize_text(v)
    return ""


def patch_file(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return (False, "")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return (False, "")
    fm = parts[1]
    rest = parts[2]
    fm_lines = fm.splitlines()

    title_idx = -1
    title_sort_present = False
    year_idx = -1
    title_val = ""
    for i, line in enumerate(fm_lines):
        m_title = re.match(r"^title:\s*(.*)$", line)
        if m_title:
            title_idx = i
            title_val = normalize_text(parse_scalar(m_title.group(1)))
        if re.match(r"^title_sort:\s*", line):
            title_sort_present = True
        if year_idx < 0 and re.match(r"^year:\s*", line):
            year_idx = i

    if title_idx < 0 or title_sort_present:
        return (False, "")
    if not re.search(r"\d", title_val):
        return (False, "")

    title_sort = numeric_aware_sort_key(title_val, width=3)
    insert_line = f"title_sort: {yaml_quote(title_sort)}"
    insert_at = title_idx + 1
    if year_idx >= 0 and year_idx > title_idx:
        insert_at = year_idx
    fm_lines.insert(insert_at, insert_line)

    new_text = "---\n" + "\n".join(fm_lines) + "\n---" + rest
    if not new_text.endswith("\n"):
        new_text += "\n"
    return (True, new_text)


def main() -> int:
    ap = argparse.ArgumentParser(description="Autofix missing title_sort for numeric titles in _works.")
    ap.add_argument("--site-root", default=".", help="Path to site root (default: current directory)")
    ap.add_argument("--work-ids", default="", help="Comma-separated work_ids/ranges scope (e.g. 66-74,38,40)")
    ap.add_argument("--write", action="store_true", help="Write changes (default is dry-run)")
    ap.add_argument("--max-samples", type=int, default=20, help="Max sample IDs to print")
    args = ap.parse_args()

    site_root = Path(args.site_root).resolve()
    selected = parse_work_id_selection(args.work_ids) if args.work_ids else None
    works_dir = site_root / "_works"

    candidates = 0
    written = 0
    samples: list[str] = []

    for p in sorted(works_dir.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        fm = text.split("---", 2)[1].splitlines() if text.count("---") >= 2 else []
        wid = extract_work_id(fm)
        if selected is not None and wid not in selected:
            continue

        changed, new_text = patch_file(p)
        if not changed:
            continue
        candidates += 1
        if len(samples) < args.max_samples:
            samples.append(wid or p.stem)
        if args.write:
            p.write_text(new_text, encoding="utf-8")
            written += 1

    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"{mode}: candidates={candidates} written={written}")
    if samples:
        print("Sample work_ids: " + ", ".join(samples))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

