#!/usr/bin/env python3
"""Build public document-location indexes from current public projections."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docs_builder.runtime_bootstrap import (
    apply_projects_base_dir_override,
    apply_repo_local_env,
    projects_base_dir_from_argv,
)

if __name__ == "__main__":
    apply_repo_local_env(projects_base_dir=projects_base_dir_from_argv(sys.argv[1:]))


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

from docs_document_location_projection import (  # noqa: E402
    SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS,
    document_location_projection_path,
    json_bytes,
    load_public_document_location_payload,
)
from docs_scope_config import load_docs_scope_configs, resolve_scope_path  # noqa: E402


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build public Docs Viewer document-location search indexes."
    )
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Limit the build to analysis or library. Repeat for both.",
    )
    parser.add_argument(
        "--projects-base-dir",
        help="Override DOTLINEFORM_PROJECTS_BASE_DIR after loading .env.local.",
    )
    parser.add_argument("--write", action="store_true", help="Write generated files.")
    return parser.parse_args(argv)


def selected_scope_ids(values: list[str]) -> list[str]:
    requested = [str(value or "").strip().lower() for value in values]
    scope_ids = requested or list(SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS)
    if any(not scope_id for scope_id in scope_ids):
        raise ValueError("scope must not be empty")
    if len(set(scope_ids)) != len(scope_ids):
        raise ValueError("scope must not be repeated")
    unsupported = sorted(
        set(scope_ids) - set(SUPPORTED_DOCUMENT_LOCATION_SCOPE_IDS)
    )
    if unsupported:
        raise ValueError(
            "unsupported document-location scope: " + ", ".join(unsupported)
        )
    return scope_ids


def write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_bytes(payload)
    temp_path.replace(path)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.projects_base_dir:
        apply_projects_base_dir_override(args.projects_base_dir)
    repo_root = Path.cwd().resolve()
    scope_ids = selected_scope_ids(args.scope)
    configs = load_docs_scope_configs(repo_root, scope_ids=scope_ids)
    missing = [scope_id for scope_id in scope_ids if scope_id not in configs]
    if missing:
        raise ValueError("unknown Docs Viewer scope: " + ", ".join(missing))

    for scope_id in scope_ids:
        config = configs[scope_id]
        payload = load_public_document_location_payload(repo_root, config)
        output_path = resolve_scope_path(
            repo_root,
            document_location_projection_path(config),
        )
        output_bytes = json_bytes(payload)
        changed = not output_path.is_file() or output_path.read_bytes() != output_bytes
        if args.write and changed:
            write_bytes_atomic(output_path, output_bytes)
        mode = "wrote" if args.write and changed else "unchanged"
        if not args.write:
            mode = "would write" if changed else "unchanged"
        relative_path = output_path.relative_to(repo_root).as_posix()
        print(
            f"Document locations scope={scope_id}: {mode} {relative_path} "
            f"({len(payload['records'])} records)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
