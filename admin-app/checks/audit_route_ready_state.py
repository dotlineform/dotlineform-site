#!/usr/bin/env python3
"""Audit route-ready template contracts across local apps."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppConfig:
    app_id: str
    label: str
    path_patterns: tuple[str, ...]
    ready_attr: str
    busy_attr: str
    allow_initial_ready_true: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ReadyRoot:
    tag: str
    attrs: dict[str, str]
    line: int


@dataclass(frozen=True)
class Finding:
    severity: str
    app: str
    path: Path
    message: str

    def format(self) -> str:
        return f"{self.severity}: {self.path.relative_to(REPO_ROOT)}: {self.message}"

    def to_json(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "app": self.app,
            "path": str(self.path.relative_to(REPO_ROOT)),
            "message": self.message,
        }


class ReadyStateParser(HTMLParser):
    def __init__(self, ready_attr: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ready_attr = ready_attr
        self.roots: list[ReadyRoot] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): "" if value is None else value for name, value in attrs}
        if self.ready_attr in attr_map:
            line, _column = self.getpos()
            self.roots.append(ReadyRoot(tag=tag, attrs=attr_map, line=line))


APP_CONFIGS = (
    AppConfig(
        app_id="studio",
        label="Studio",
        path_patterns=("studio/app/frontend/routes/*.html",),
        ready_attr="data-studio-ready",
        busy_attr="data-studio-busy",
        allow_initial_ready_true=frozenset({"studio/app/frontend/routes/studio-home.html"}),
    ),
    AppConfig(
        app_id="admin",
        label="Admin",
        path_patterns=("admin-app/app/frontend/routes/*.html",),
        ready_attr="data-admin-ready",
        busy_attr="data-admin-busy",
    ),
    AppConfig(
        app_id="analytics",
        label="Analytics",
        path_patterns=("analytics-app/app/frontend/routes/*.html",),
        ready_attr="data-analytics-ready",
        busy_attr="data-analytics-busy",
        allow_initial_ready_true=frozenset({"analytics-app/app/frontend/routes/analytics-home.html"}),
    ),
    AppConfig(
        app_id="docs-viewer",
        label="Docs Viewer",
        path_patterns=(
            "docs-viewer/templates/public-route/index.html",
            "docs-viewer/shell/docs-viewer-manage.html",
            "site/library/index.html",
            "site/analysis/index.html",
        ),
        ready_attr="data-docs-viewer-ready",
        busy_attr="data-docs-viewer-busy",
    ),
)
APP_CONFIG_BY_ID = {config.app_id: config for config in APP_CONFIGS}


def rel_path(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def configured_paths(config: AppConfig) -> list[Path]:
    paths: list[Path] = []
    for pattern in config.path_patterns:
        matches = sorted(REPO_ROOT.glob(pattern))
        if matches:
            paths.extend(path for path in matches if path.is_file())
            continue
        direct_path = REPO_ROOT / pattern
        if direct_path.is_file():
            paths.append(direct_path)
    return sorted(dict.fromkeys(paths))


def parse_ready_roots(text: str, ready_attr: str) -> list[ReadyRoot]:
    parser = ReadyStateParser(ready_attr)
    parser.feed(text)
    parser.close()
    return parser.roots


def audit_template(config: AppConfig, path: Path) -> tuple[list[Finding], int]:
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    roots = parse_ready_roots(text, config.ready_attr)
    relative = rel_path(path)

    if not roots:
        findings.append(
            Finding("error", config.app_id, path, f"template is missing {config.ready_attr}")
        )
        return findings, 0

    if len(roots) > 1:
        findings.append(
            Finding("error", config.app_id, path, f"template has {len(roots)} ready-state roots")
        )

    for root in roots:
        ready_value = root.attrs.get(config.ready_attr, "").strip().lower()
        busy_value = root.attrs.get(config.busy_attr, "").strip().lower()
        location = f"line {root.line}"

        if ready_value not in {"false", "true"}:
            findings.append(
                Finding(
                    "error",
                    config.app_id,
                    path,
                    f"{config.ready_attr} should be true or false on {location}",
                )
            )
        elif ready_value == "true" and relative not in config.allow_initial_ready_true:
            findings.append(
                Finding(
                    "error",
                    config.app_id,
                    path,
                    f"{config.ready_attr} should start false on {location}",
                )
            )

        if config.busy_attr not in root.attrs:
            findings.append(
                Finding(
                    "error",
                    config.app_id,
                    path,
                    f"ready-state root is missing {config.busy_attr} on {location}",
                )
            )
        elif busy_value != "false":
            findings.append(
                Finding(
                    "error",
                    config.app_id,
                    path,
                    f"{config.busy_attr} should start false on {location}",
                )
            )

    return findings, len(roots)


def audit_config(config: AppConfig) -> tuple[list[Finding], dict[str, int]]:
    findings: list[Finding] = []
    paths = configured_paths(config)
    totals = {
        "templates": len(paths),
        "ready_roots": 0,
    }

    if not paths:
        findings.append(
            Finding("error", config.app_id, REPO_ROOT, f"no templates matched {config.label}")
        )
        return findings, totals

    for path in paths:
        template_findings, ready_roots = audit_template(config, path)
        findings.extend(template_findings)
        totals["ready_roots"] += ready_roots

    return findings, totals


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--app",
        choices=tuple(APP_CONFIG_BY_ID),
        action="append",
        help="Limit the audit to one app. May be passed more than once.",
    )
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
    configs = [APP_CONFIG_BY_ID[app_id] for app_id in args.app] if args.app else list(APP_CONFIGS)
    findings: list[Finding] = []
    totals_by_app: dict[str, dict[str, int]] = {}

    for config in configs:
        app_findings, app_totals = audit_config(config)
        findings.extend(app_findings)
        totals_by_app[config.app_id] = app_totals

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    failed = bool(errors or (args.strict and warnings))
    total_templates = sum(totals["templates"] for totals in totals_by_app.values())
    total_ready_roots = sum(totals["ready_roots"] for totals in totals_by_app.values())
    payload = {
        "status": "failed" if failed else "passed",
        "strict": args.strict,
        "totals": {
            "templates": total_templates,
            "ready_roots": total_ready_roots,
        },
        "totals_by_app": totals_by_app,
        "summary": {
            "apps": len(configs),
            "templates": total_templates,
            "ready_roots": total_ready_roots,
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "findings": [finding.to_json() for finding in findings],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "Route ready-state audit: "
            f"{payload['summary']['apps']} apps, "
            f"{payload['summary']['templates']} templates, "
            f"{payload['summary']['ready_roots']} ready roots"
        )
        for config in configs:
            totals = totals_by_app[config.app_id]
            print(
                f"- {config.label}: "
                f"{totals['templates']} templates, {totals['ready_roots']} ready roots"
            )
        for finding in findings:
            print(finding.format())
        print(f"result: {payload['status']} ({len(errors)} errors, {len(warnings)} warnings)")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
