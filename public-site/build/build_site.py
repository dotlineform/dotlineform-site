#!/usr/bin/env python3
"""Build the static public-site artifact."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from public_site_builder.audit import audit_artifact
from public_site_builder.builder import build_site
from public_site_builder.config import PublicSiteConfig, load_config


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "public-site" / "config" / "public-site.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to public-site config JSON.",
    )
    parser.add_argument(
        "--destination",
        help="Output directory. Defaults to config output.default_destination.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run artifact surface audit after building.",
    )
    return parser.parse_args(argv)


def resolve_destination(config: PublicSiteConfig, destination: str | None) -> Path:
    raw_destination = destination or config.default_destination
    path = Path(raw_destination)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(Path(args.config))
        destination = resolve_destination(config, args.destination)
        result = build_site(REPO_ROOT, destination, config)
        print(f"Built public site artifact: {result.destination}")
        print(f"Copied public files: {result.copied_count}")
        print(f"Rendered route pages: {result.rendered_count}")
        if args.audit:
            audit_result = audit_artifact(result.destination, config)
            print(f"Artifact audit passed: {audit_result.checked_count} files checked")
    except Exception as exc:
        print(f"public-site build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
