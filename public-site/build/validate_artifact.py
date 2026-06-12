#!/usr/bin/env python3
"""Validate the static public-site artifact before GitHub Pages upload."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from public_site_builder.audit import audit_artifact
from public_site_builder.config import PublicSiteConfig, load_config


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "public-site" / "config" / "public-site.json"

ARTIFACT_ROOT_FILES = (
    ".nojekyll",
    "CNAME",
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
    "apple-touch-icon-precomposed.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "safari-pinned-tab.svg",
    "site.webmanifest",
    "404.html",
)

FORBIDDEN_ARTIFACT_GLOBS = (
    "**/.DS_Store",
    "docs-viewer/runtime/js/docs-viewer-management*.js",
    "docs-viewer/runtime/js/docs-viewer-manage.js",
    "docs-viewer/runtime/js/docs-html-import*.js",
    "docs-viewer/runtime/js/reports/**",
    "docs-viewer/source/**",
    "docs-viewer/generated/docs/studio/**",
    "docs-viewer/generated/docs/tmp/**",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to public-site config JSON.",
    )
    parser.add_argument(
        "--destination",
        help="Artifact directory. Defaults to config output.default_destination.",
    )
    parser.add_argument(
        "--expected-docs-runtime-count",
        type=int,
        default=44,
        help="Expected count of public Docs Viewer runtime JavaScript modules.",
    )
    return parser.parse_args(argv)


def resolve_destination(config: PublicSiteConfig, destination: str | None) -> Path:
    raw_destination = destination or config.default_destination
    path = Path(raw_destination)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def validate_artifact(destination: Path, config: PublicSiteConfig, expected_docs_runtime_count: int) -> int:
    errors: list[str] = []
    audit_result = audit_artifact(destination, config)

    for relative in ARTIFACT_ROOT_FILES:
        if not (destination / relative).is_file():
            errors.append(f"missing artifact root file: {relative}")

    runtime_root = destination / "docs-viewer" / "runtime" / "js"
    runtime_modules = sorted(runtime_root.glob("*.js"))
    if len(runtime_modules) != expected_docs_runtime_count:
        errors.append(
            "unexpected public Docs Viewer runtime module count: "
            f"expected {expected_docs_runtime_count}, found {len(runtime_modules)}"
        )

    for pattern in FORBIDDEN_ARTIFACT_GLOBS:
        matches = [
            path.relative_to(destination).as_posix()
            for path in destination.glob(pattern)
            if path.is_file()
        ]
        if matches:
            errors.append(f"artifact contains forbidden files for {pattern}: {', '.join(matches[:10])}")

    if errors:
        raise RuntimeError("; ".join(errors))

    print(
        "Artifact validation passed: "
        f"{audit_result.checked_count} files checked; "
        f"{len(runtime_modules)} Docs Viewer runtime modules"
    )
    return audit_result.checked_count


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(Path(args.config))
        destination = resolve_destination(config, args.destination)
        validate_artifact(destination, config, args.expected_docs_runtime_count)
    except Exception as exc:
        print(f"public-site artifact validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
