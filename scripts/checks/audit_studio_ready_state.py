#!/usr/bin/env python3
"""Audit Studio route-ready template contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STUDIO_ROOT = REPO_ROOT / "studio"
IGNORED_PAGE_ROOTS = (
    STUDIO_ROOT / "data" / "canonical" / "catalogue-markdown",
    STUDIO_ROOT / "docs-viewer" / "source",
)
STATIC_SCRIPT = "studio-static-route.js"
DASHBOARD_SCRIPT = "studio-dashboard.js"

ATTR_RE_TEMPLATE = r"""{name}\s*=\s*["']([^"']+)["']"""
SCRIPT_TAG_RE = re.compile(r"""<script\b[^>]*>""", re.IGNORECASE)
SCRIPT_TYPE_RE = re.compile(r"""\btype\s*=\s*(["'])module\1""", re.IGNORECASE)
SCRIPT_SRC_RE = re.compile(r"""\bsrc\s*=\s*(["'])(.*?)\1""", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    severity: str
    path: Path
    message: str

    def format(self) -> str:
        return f"{self.severity}: {self.path.relative_to(REPO_ROOT)}: {self.message}"

    def to_json(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "path": str(self.path.relative_to(REPO_ROOT)),
            "message": self.message,
        }


def attr_values(text: str, name: str) -> list[str]:
    pattern = re.compile(ATTR_RE_TEMPLATE.format(name=re.escape(name)))
    return pattern.findall(text)


def has_attr_value(text: str, name: str, value: str) -> bool:
    return value in attr_values(text, name)


def module_scripts(text: str) -> list[str]:
    scripts: list[str] = []
    for tag in SCRIPT_TAG_RE.findall(text):
        if not SCRIPT_TYPE_RE.search(tag):
            continue
        src_match = SCRIPT_SRC_RE.search(tag)
        if src_match:
            scripts.append(src_match.group(2))
    return scripts


def has_script(text: str, script_name: str) -> bool:
    return any(script_name in src for src in module_scripts(text))


def studio_pages() -> list[Path]:
    pages: list[Path] = []
    for path in STUDIO_ROOT.rglob("*.md"):
        if not path.is_file():
            continue
        if any(path.is_relative_to(root) for root in IGNORED_PAGE_ROOTS):
            continue
        pages.append(path)
    return sorted(pages)


def audit_page(path: Path) -> tuple[list[Finding], dict[str, int]]:
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    counts = {
        "ready": 0,
        "static": 0,
        "dashboard": 0,
    }

    has_ready_attr = bool(attr_values(text, "data-studio-ready"))
    has_busy_attr = bool(attr_values(text, "data-studio-busy"))
    static_routes = attr_values(text, "data-studio-static-route")
    dashboard_routes = attr_values(text, "data-studio-dashboard-route")
    scripts = module_scripts(text)
    non_static_scripts = [src for src in scripts if STATIC_SCRIPT not in src]

    if has_ready_attr:
        counts["ready"] = 1
        if not has_attr_value(text, "data-studio-ready", "false"):
            findings.append(Finding("error", path, 'ready roots should start with data-studio-ready="false"'))
        if not has_busy_attr:
            findings.append(Finding("error", path, "ready roots should also declare data-studio-busy"))
        elif not has_attr_value(text, "data-studio-busy", "false"):
            findings.append(Finding("error", path, 'ready roots should start with data-studio-busy="false"'))

    if static_routes:
        counts["static"] = 1
        if dashboard_routes:
            findings.append(Finding("error", path, "route uses both static and dashboard ready markers"))
        if not has_script(text, STATIC_SCRIPT):
            findings.append(Finding("error", path, f"static route is missing {STATIC_SCRIPT}"))
        if not has_ready_attr or not has_busy_attr:
            findings.append(Finding("error", path, "static route is missing the shared ready/busy baseline"))
        if attr_values(text, "data-studio-metric"):
            findings.append(Finding("error", path, "static route contains dashboard metric markers"))
        if non_static_scripts:
            joined = ", ".join(non_static_scripts)
            findings.append(
                Finding(
                    "warning",
                    path,
                    f"static route also loads module script(s): {joined}; use a route-specific ready contract if this adds async behavior",
                )
            )

    if dashboard_routes:
        counts["dashboard"] = 1
        if not has_script(text, DASHBOARD_SCRIPT):
            findings.append(Finding("error", path, f"dashboard route is missing {DASHBOARD_SCRIPT}"))
        if has_script(text, STATIC_SCRIPT):
            findings.append(Finding("error", path, f"dashboard route should not load {STATIC_SCRIPT}"))
        if not has_ready_attr or not has_busy_attr:
            findings.append(Finding("error", path, "dashboard route is missing the shared ready/busy baseline"))

    return findings, counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero for warnings as well as errors.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of human-readable output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings: list[Finding] = []
    totals = {
        "pages": 0,
        "ready": 0,
        "static": 0,
        "dashboard": 0,
    }

    for path in studio_pages():
        page_findings, counts = audit_page(path)
        findings.extend(page_findings)
        totals["pages"] += 1
        for key, value in counts.items():
            totals[key] += value

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    failed = bool(errors or (args.strict and warnings))
    payload = {
        "status": "failed" if failed else "passed",
        "strict": args.strict,
        "totals": {
            "templates": totals["pages"],
            "ready_roots": totals["ready"],
            "static_routes": totals["static"],
            "dashboard_routes": totals["dashboard"],
        },
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "findings": [finding.to_json() for finding in findings],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "Studio ready-state audit: "
            f"{totals['pages']} templates, "
            f"{totals['ready']} ready roots, "
            f"{totals['static']} static routes, "
            f"{totals['dashboard']} dashboard routes"
        )
        for finding in findings:
            print(finding.format())
        print(f"result: {payload['status']} ({len(errors)} errors, {len(warnings)} warnings)")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
