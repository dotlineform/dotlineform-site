#!/usr/bin/env python3
"""Generate a lightweight CSS token audit report."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import DefaultDict

FONT_RE = re.compile(r"font-size\s*:\s*([^;]+);")
COLOR_RE = re.compile(r"(#(?:[0-9a-fA-F]{3,8})\b|rgba?\([^)]+\)|hsla?\([^)]+\))")
CUSTOM_PROP_RE = re.compile(r"--[\w-]+\s*:")


def is_literal_font(value: str) -> bool:
    value = value.strip()
    if value.startswith("var("):
        return False
    if value in {"inherit", "initial", "unset", "revert"}:
        return False
    return True


def format_counter(counter: Counter[str], lines_by_value: dict[str, list[int]], limit: int = 10) -> list[str]:
    rows = []
    for value, count in counter.most_common(limit):
        line_list = ", ".join(str(line) for line in lines_by_value[value][:6])
        suffix = "" if len(lines_by_value[value]) <= 6 else ", ..."
        rows.append(f"- `{value}`: {count} occurrence(s) at line(s) {line_list}{suffix}")
    return rows


def audit_file(path: Path) -> dict[str, object]:
    text = path.read_text()
    lines = text.splitlines()

    font_lines: DefaultDict[str, list[int]] = defaultdict(list)
    raw_font_lines: DefaultDict[str, list[int]] = defaultdict(list)
    color_lines: DefaultDict[str, list[int]] = defaultdict(list)
    direct_color_lines: DefaultDict[str, list[int]] = defaultdict(list)

    for line_no, line in enumerate(lines, start=1):
        for match in FONT_RE.finditer(line):
            value = match.group(1).strip()
            font_lines[value].append(line_no)
            if is_literal_font(value):
                raw_font_lines[value].append(line_no)

        for match in COLOR_RE.finditer(line):
            value = match.group(1).strip()
            color_lines[value].append(line_no)
            if not CUSTOM_PROP_RE.search(line):
                direct_color_lines[value].append(line_no)

    font_counter = Counter({value: len(numbers) for value, numbers in font_lines.items()})
    raw_font_counter = Counter({value: len(numbers) for value, numbers in raw_font_lines.items()})
    color_counter = Counter({value: len(numbers) for value, numbers in color_lines.items()})
    direct_color_counter = Counter({value: len(numbers) for value, numbers in direct_color_lines.items()})

    return {
        "path": str(path),
        "font_counter": font_counter,
        "font_lines": dict(font_lines),
        "raw_font_counter": raw_font_counter,
        "raw_font_lines": dict(raw_font_lines),
        "color_counter": color_counter,
        "color_lines": dict(color_lines),
        "direct_color_counter": direct_color_counter,
        "direct_color_lines": dict(direct_color_lines),
    }


def build_summary(audits: list[dict[str, object]]) -> list[str]:
    summary = []
    for audit in audits:
        path = audit["path"]
        raw_font_counter = audit["raw_font_counter"]
        direct_color_counter = audit["direct_color_counter"]
        summary.append(
            "- `{}`: {} `font-size` declarations, {} raw literal sizes, {} direct color literal usages".format(
                path,
                sum(audit["font_counter"].values()),
                sum(raw_font_counter.values()),
                sum(direct_color_counter.values()),
            )
        )
    return summary


def build_findings(audits: list[dict[str, object]]) -> list[str]:
    findings: list[str] = []
    for audit in audits:
        path = audit["path"]
        raw_font_counter = audit["raw_font_counter"]
        direct_color_counter = audit["direct_color_counter"]
        findings.append(f"### `{path}`")
        findings.append("")
        findings.append("Raw font-size hotspots:")
        font_rows = format_counter(raw_font_counter, audit["raw_font_lines"])
        findings.extend(font_rows or ["- none"])
        findings.append("")
        findings.append("Direct color literal hotspots:")
        color_rows = format_counter(direct_color_counter, audit["direct_color_lines"])
        findings.extend(color_rows or ["- none"])
        findings.append("")
    return findings


def build_recommendations(audits: list[dict[str, object]]) -> list[str]:
    main_audit = next((audit for audit in audits if str(audit["path"]).endswith("assets/css/main.css")), None)
    studio_audit = next((audit for audit in audits if str(audit["path"]).endswith("assets/studio/css/studio.css")), None)
    recs = [
        "## Recommendations",
        "",
        "### P1 Typography",
        "",
        "- Finalize one shared text scale before touching page selectors further.",
        "- Replace repeated raw caption/meta values in `main.css` with semantic tokens.",
        "- Fit component and page typography to the existing shared tokens instead of preserving local near-duplicate sizes.",
        "",
        "### P2 Color",
        "",
        "- Keep palette tokens centralized and remove the remaining component-level hardcoded colors.",
        "- Add semantic aliases for states and special chips instead of repeating neutrals and weight-dot fills inline.",
        "",
        "### P3 Primitives",
        "",
        "- Standardize shared list, panel, input, button, and toolbar primitives before page-by-page cleanup.",
        "- Migrate pages by primitive family rather than by file or route.",
        "",
        "### P4 Guardrails",
        "",
        "- Re-run this audit after each CSS cleanup pass.",
        "- Block new raw `font-size` and color literals once the replacement token family exists.",
        "",
    ]
    if main_audit:
        top_main = main_audit["raw_font_counter"].most_common(3)
        if top_main:
            recs.append("Main.css immediate target values:")
            recs.extend([f"- `{value}` ({count} occurrence(s))" for value, count in top_main])
            recs.append("")
    if studio_audit:
        top_studio = studio_audit["raw_font_counter"].most_common(5)
        if top_studio:
            recs.append("Studio.css immediate target values:")
            recs.extend([f"- `{value}` ({count} occurrence(s))" for value, count in top_studio])
            recs.append("")
    return recs


def render_report(audits: list[dict[str, object]], files: list[Path]) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# CSS Audit Latest",
        "",
        f"Generated: {timestamp}",
        "",
        "Files:",
    ]
    lines.extend([f"- `{path.as_posix()}`" for path in files])
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.extend(build_summary(audits))
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    lines.extend(build_findings(audits))
    lines.extend(build_recommendations(audits))
    return "\n".join(lines).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a lightweight CSS token audit report.")
    parser.add_argument(
        "files",
        nargs="*",
        default=["assets/css/main.css", "assets/studio/css/studio.css"],
        help="CSS files to audit",
    )
    parser.add_argument(
        "--md-out",
        default="docs/css-audit-latest.md",
        help="Markdown output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = [Path(item) for item in args.files]
    audits = [audit_file(path) for path in files]
    report = render_report(audits, files)
    out_path = Path(args.md_out)
    out_path.write_text(report)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
