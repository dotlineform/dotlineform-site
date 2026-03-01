#!/usr/bin/env python3
"""Build a type-level sitemap for site_map.html."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List


def yaml_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def normalize_url(url: str) -> str:
    s = (url or "").strip()
    if not s:
        return "/"
    if s.startswith(("http://", "https://")):
        return s
    if not s.startswith("/"):
        s = "/" + s
    if not s.endswith("/"):
        s = s + "/"
    return s


def parse_scalar(value: str) -> Any:
    s = value.strip()
    if s == "":
        return ""
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low == "null":
        return None
    return s


def read_front_matter(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines:
        return {}
    data: Dict[str, Any] = {}
    i = 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            break
        if line.startswith(" ") or line.startswith("\t"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key:
            i += 1
            continue
        data[key] = parse_scalar(raw)
        i += 1
    return data


def is_published(fm: Dict[str, Any]) -> bool:
    val = fm.get("published")
    return val is not False and str(val).lower() != "false"


def title_for(path: Path, fm: Dict[str, Any]) -> str:
    title = fm.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return path.stem


def make_item(title: str, url: str, source: str, depth: int, node_type: str) -> Dict[str, Any]:
    return {
        "title": title,
        "url": normalize_url(url),
        "source": source,
        "depth": depth,
        "node_type": node_type,
    }


def build_works_section(root: Path) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    items.append(make_item("works index", "/works/", "works/index.md", 0, "index"))
    items.append(make_item("work details index", "/work_details/", "work_details/index.md", 1, "index"))
    items.append(make_item("works curator index", "/works_curator/", "works_curator/index.md", 0, "index"))
    items.append(make_item("series", "/series/", "_series/*.md", 0, "index"))
    items.append(make_item("series curator index", "/series_curator/", "series_curator/index.html", 1, "index"))
    items.append(make_item("studio series index", "/studio/studio-series/", "studio/studio-series/index.html", 1, "index"))
    items.append(make_item("works in series", "/works/:id/", "_works/*.md", 1, "work"))
    items.append(make_item("work details", "/work_details/:id/", "_work_details/*.md", 2, "detail"))
    return {"key": "works", "label": "Works", "items": items}


def build_moments_section() -> Dict[str, Any]:
    items: List[Dict[str, Any]] = [
        make_item("moments index", "/moments/", "moments/index.md", 0, "index"),
        make_item("moment pages", "/moments/:id/", "_moments/*.md", 1, "moment"),
    ]
    return {"key": "moments", "label": "Moments", "items": items}


def build_themes_section() -> Dict[str, Any]:
    items: List[Dict[str, Any]] = [
        make_item("themes index", "/themes/", "themes/index.md", 0, "index"),
        make_item("theme pages", "/themes/:id/", "_themes/*.md", 1, "theme"),
    ]
    return {"key": "themes", "label": "Themes", "items": items}


def build_research_section() -> Dict[str, Any]:
    items: List[Dict[str, Any]] = [
        make_item("research index", "/research/", "research/index.md", 0, "index"),
        make_item("research pages", "/research/:id/", "_research/*.md", 1, "research"),
    ]
    return {"key": "research", "label": "Research", "items": items}


def build_core_section(root: Path) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    pages = [
        ("about.md", "about", "/about/", "core"),
        ("palette.html", "palette", "/palette/", "tooling"),
    ]
    for rel_path, default_title, default_url, node_type in pages:
        path = root / rel_path
        if not path.exists():
            continue
        fm = read_front_matter(path)
        if not is_published(fm):
            continue
        title = str(fm.get("title") or default_title)
        url = str(fm.get("permalink") or default_url)
        items.append(make_item(title, url, rel_path, 0, node_type))

    items = sorted(items, key=lambda x: (x["title"].lower(), x["url"]))
    return {"key": "core", "label": "Core Pages", "items": items}


def to_yaml(sections: List[Dict[str, Any]]) -> str:
    lines: List[str] = ["sections:"]
    for section in sections:
        lines.append("  -")
        lines.append(f"    key: {yaml_quote(section['key'])}")
        lines.append(f"    label: {yaml_quote(section['label'])}")
        lines.append("    items:")
        for item in section.get("items", []):
            lines.append("      -")
            lines.append(f"        title: {yaml_quote(str(item['title']))}")
            lines.append(f"        url: {yaml_quote(str(item['url']))}")
            lines.append(f"        source: {yaml_quote(str(item['source']))}")
            lines.append(f"        depth: {int(item['depth'])}")
            lines.append(f"        node_type: {yaml_quote(str(item['node_type']))}")
    return "\n".join(lines) + "\n"


def build_sections(root: Path) -> List[Dict[str, Any]]:
    return [
        build_works_section(root),
        build_moments_section(),
        build_themes_section(),
        build_research_section(),
        build_core_section(root),
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Site root directory")
    ap.add_argument("--output", default="_data/sitemap.yml", help="Output data path")
    ap.add_argument("--write", action="store_true", help="Write output file (default is dry-run)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    output_path = root / args.output
    sections = build_sections(root)
    payload = to_yaml(sections)
    total_items = sum(len(section.get("items", [])) for section in sections)

    if not args.write:
        print(f"[dry-run] would write {args.output} ({len(sections)} sections, {total_items} rows)")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload, encoding="utf-8")
    print(f"[write] wrote {args.output} ({len(sections)} sections, {total_items} rows)")


if __name__ == "__main__":
    main()
