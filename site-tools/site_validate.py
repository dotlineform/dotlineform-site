#!/usr/bin/env python3
"""Validate the tracked static site root before GitHub Pages upload."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from site_tools.config import load_config
from site_tools.validation import resolve_site_root, validate_site


TOOL_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TOOL_ROOT.parent
DEFAULT_CONFIG_PATH = TOOL_ROOT / "config" / "site-tools.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to site-tools config JSON.",
    )
    parser.add_argument(
        "--site-root",
        help="Static site directory. Defaults to validation.site_root from config.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(Path(args.config))
        site_root = resolve_site_root(REPO_ROOT, config, args.site_root)
        result = validate_site(site_root, config)
    except Exception as exc:
        print(f"site validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Site validation passed: "
        f"{result.required_file_count} required files; "
        f"{result.required_directory_count} required directories; "
        f"{result.docs_viewer_runtime_count} Docs Viewer runtime modules"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
