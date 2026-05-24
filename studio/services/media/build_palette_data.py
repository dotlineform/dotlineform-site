#!/usr/bin/env python3
"""
Build palette data for palette.html from assets/css/main.css.

Default behavior is dry-run (prints the output path and row count).
Use --write to persist _data/palette.yml.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Set


HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3,8})\b")
VAR_DEF_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", re.IGNORECASE)
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)


TOKEN_ORDER = [
    "--text",
    "--muted",
    "--bg",
    "--panel",
    "--panel-2",
    "--border",
    "--border-strong",
    "--link",
    "--link-hover",
    "--link-visited",
]


def extract_block(css: str, marker: str) -> str:
    idx = css.find(marker)
    if idx < 0:
        return ""
    start = css.find("{", idx)
    if start < 0:
        return ""
    depth = 0
    for pos in range(start, len(css)):
        ch = css[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return css[start + 1 : pos]
    return ""


def extract_var_hexes(block: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for m in VAR_DEF_RE.finditer(block):
        key = m.group(1).strip()
        value = m.group(2).strip()
        hm = HEX_RE.search(value)
        if hm:
            out[key] = hm.group(0).lower()
    return out


def split_selectors(raw: str) -> List[str]:
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    parts: List[str] = []
    for p in raw.split(","):
        s = " ".join(p.split())
        if s:
            parts.append(s)
    return parts


def find_var_usages(css: str, var_name: str) -> List[str]:
    found: List[str] = []
    seen: Set[str] = set()
    needle = f"var({var_name})"
    for m in RULE_RE.finditer(css):
        selectors = m.group(1)
        body = m.group(2)
        if needle not in body:
            continue
        for sel in split_selectors(selectors):
            if sel not in seen:
                seen.add(sel)
                found.append(sel)
    return found


def find_direct_hex_usages(css: str) -> Dict[str, List[str]]:
    usage: Dict[str, List[str]] = {}
    seen: Dict[str, Set[str]] = {}

    for m in RULE_RE.finditer(css):
        selectors = split_selectors(m.group(1))
        body = m.group(2)
        for line in body.split(";"):
            if "--" in line:
                continue
            for hm in HEX_RE.finditer(line):
                hx = hm.group(0).lower()
                usage.setdefault(hx, [])
                seen.setdefault(hx, set())
                for sel in selectors:
                    if sel not in seen[hx]:
                        seen[hx].add(sel)
                        usage[hx].append(sel)
    return usage


def summarize_usage(selectors: List[str], limit: int = 5) -> str:
    if not selectors:
        return ""
    if len(selectors) <= limit:
        return ", ".join(selectors)
    return ", ".join(selectors[:limit]) + f" (+{len(selectors) - limit} more)"


def yaml_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_palette_items(css: str) -> List[Dict[str, str]]:
    root_vars = extract_var_hexes(extract_block(css, ":root"))
    light_override_vars = extract_var_hexes(extract_block(css, 'html[data-theme="light"]'))

    media_dark_block = extract_block(css, "@media (prefers-color-scheme: dark)")
    media_dark_root_vars = extract_var_hexes(extract_block(media_dark_block, ":root")) if media_dark_block else {}
    dark_override_vars = extract_var_hexes(extract_block(css, 'html[data-theme="dark"]'))

    light_vars = dict(root_vars)
    light_vars.update(light_override_vars)

    dark_vars = dict(media_dark_root_vars)
    dark_vars.update(dark_override_vars)

    items: List[Dict[str, str]] = []

    for token in TOKEN_ORDER:
        light_hex = light_vars.get(token, "")
        dark_hex = dark_vars.get(token, "")
        usage = summarize_usage(find_var_usages(css, token))
        items.append(
            {
                "id": token,
                "usage": usage,
                "light_hex": light_hex,
                "dark_hex": dark_hex,
            }
        )

    direct_usage = find_direct_hex_usages(css)
    for hx in ["#777", "#d11", "#1166cc"]:
        selectors = direct_usage.get(hx, [])
        usage = summarize_usage(selectors)
        items.append(
            {
                "id": f"direct {hx}",
                "usage": usage,
                "light_hex": hx,
                "dark_hex": hx,
            }
        )

    return items


def to_yaml(items: List[Dict[str, str]]) -> str:
    lines: List[str] = ["items:"]
    for item in items:
        lines.append("  -")
        lines.append(f"    id: {yaml_quote(item.get('id', ''))}")
        lines.append(f"    usage: {yaml_quote(item.get('usage', ''))}")
        lines.append(f"    light_hex: {yaml_quote(item.get('light_hex', ''))}")
        lines.append(f"    dark_hex: {yaml_quote(item.get('dark_hex', ''))}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--css", default="assets/css/main.css", help="Input CSS path")
    ap.add_argument("--output", default="_data/palette.yml", help="Output data path")
    ap.add_argument("--write", action="store_true", help="Write output file (default is dry-run)")
    args = ap.parse_args()

    css_path = Path(args.css)
    if not css_path.exists():
        raise SystemExit(f"CSS not found: {css_path}")

    css = css_path.read_text(encoding="utf-8")
    items = build_palette_items(css)
    output_text = to_yaml(items)

    output_path = Path(args.output)
    if not args.write:
        print(f"[dry-run] would write {output_path} ({len(items)} rows)")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"[write] wrote {output_path} ({len(items)} rows)")


if __name__ == "__main__":
    main()
