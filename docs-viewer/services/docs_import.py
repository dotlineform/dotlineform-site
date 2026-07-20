#!/usr/bin/env python3
"""Command-line parser for staged Docs Viewer returned-package data.

Run:
  ./docs-viewer/services/docs_import.py --scope library --file document-content.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from docs_document_packages.returned_parser import parse_staged_import as _parse_staged_import


def detect_repo_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "site-tools" / "config" / "site-tools.json").exists():
            raise ValueError(f"--repo-root does not look like repo root: {repo_root}")
        return repo_root

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate

    raise ValueError("Could not detect repo root")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse staged Docs Viewer import data.")
    parser.add_argument("--scope", default="library", help="Docs Viewer scope to import")
    parser.add_argument(
        "--file",
        required=True,
        help="Staged JSON or JSONL filename under $DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/",
    )
    parser.add_argument("--repo-root", default="", help="Override repo root")
    parser.add_argument("--no-records", action="store_true", help="Omit normalized records from the printed report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = detect_repo_root(args.repo_root or None)
        report = _parse_staged_import(
            repo_root=repo_root,
            scope=args.scope,
            staged_file=args.file,
        )
    except Exception as exc:
        print(f"docs_import: {exc}", file=sys.stderr)
        return 1

    if args.no_records:
        report = dict(report)
        report["records"] = []
    print(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
