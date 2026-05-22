#!/usr/bin/env python3
"""Audit a built public site for local-only Studio surface output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ABSENT_PATHS = (
    "studio",
    "docs",
    "assets/studio",
    "assets/data/docs/scopes/studio",
    "assets/data/search/studio",
)

REQUIRED_PATHS = (
    "index.html",
    "library/index.html",
    "analysis/index.html",
    "assets/docs-viewer/js/docs-viewer.js",
    "assets/docs-viewer/css/docs-viewer.css",
    "assets/docs-viewer/data/docs-viewer-public-config.json",
    "assets/data/docs/scopes/library/index.json",
    "assets/data/docs/scopes/analysis/index.json",
    "assets/data/search/library/index.json",
    "assets/data/search/analysis/index.json",
)

FORBIDDEN_HREFS = (
    'href="/studio/"',
    'href="/docs/"',
    'href="/docs/?',
)


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def audit_public_build(site_root: Path) -> list[str]:
    failures: list[str] = []
    root = site_root.resolve()

    if not root.exists():
        return [f"site root does not exist: {site_root}"]
    if not root.is_dir():
        return [f"site root is not a directory: {site_root}"]

    for rel_path in REQUIRED_PATHS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"required public output missing: {rel_path}")

    for rel_path in ABSENT_PATHS:
        path = root / rel_path
        if path.exists():
            failures.append(f"local-only output should be absent: {rel_path}")

    html_paths = sorted(root.rglob("*.html"))
    for html_path in html_paths:
        if not html_path.exists():
            continue
        text = read_text(html_path)
        for forbidden in FORBIDDEN_HREFS:
            if forbidden in text:
                failures.append(f"forbidden public link {forbidden!r} in {relative(html_path, root)}")

    config_path = root / "assets" / "docs-viewer" / "data" / "docs-viewer-public-config.json"
    if config_path.exists():
        try:
            config = json.loads(read_text(config_path))
        except json.JSONDecodeError as exc:
            failures.append(f"public Docs Viewer config is invalid JSON: {exc}")
        else:
            scopes = config.get("scopes")
            scope_ids = {
                str(scope.get("scope_id", "")).strip().lower()
                for scope in scopes
                if isinstance(scope, dict)
            } if isinstance(scopes, list) else set()
            if scope_ids != {"library", "analysis"}:
                failures.append(
                    "public Docs Viewer config must include only library and analysis scopes"
                )

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-root",
        default="_site",
        help="Built site root to audit. Defaults to _site.",
    )
    args = parser.parse_args(argv)

    failures = audit_public_build(Path(args.site_root))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(f"public build surface OK: {Path(args.site_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
