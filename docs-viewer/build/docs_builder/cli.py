from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .browser_config import (
    public_readonly_configs,
    write_browser_config,
)
from .common import (
    DOCS_VIEWER_BROWSER_CONFIG_PATH,
    DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
    SITE_DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
    load_docs_scope_configs,
)
from .pipeline import DocsDataBuilder
from .source import FrontMatterSyntaxError


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer generated document payloads.")
    parser.add_argument("--scope", action="append", default=[], help="Limit build to a named docs scope.")
    parser.add_argument("--source", help="Override docs source directory for a single selected scope.")
    parser.add_argument("--output", help="Override docs data output directory for a single selected scope.")
    parser.add_argument("--viewer-base-url", help="Override viewer page URL base for a single selected scope.")
    parser.add_argument("--only-doc-ids", help="Comma-separated doc ids for a targeted docs payload rebuild.")
    parser.add_argument("--diagnostics", action="store_true", help="Print machine-readable diagnostics for automation.")
    parser.add_argument("--write", action="store_true", help="Write generated files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path.cwd().resolve()
    configs_by_scope = load_docs_scope_configs(repo_root)
    requested_scopes = [scope.strip().lower() for scope in args.scope if scope.strip()]
    selected = [
        config for scope_id, config in configs_by_scope.items()
        if not requested_scopes or scope_id in requested_scopes
    ]
    if not selected:
        raise RuntimeError(f"Unknown docs scope(s): {', '.join(requested_scopes)}")
    if (args.source or args.output or args.viewer_base_url) and len(selected) != 1:
        raise RuntimeError("--source, --output, and --viewer-base-url can only be used when exactly one scope is selected")
    if args.only_doc_ids and len(selected) != 1:
        raise RuntimeError("--only-doc-ids can only be used when exactly one scope is selected")

    all_configs = list(configs_by_scope.values())
    if args.write:
        write_browser_config(
            repo_root,
            all_configs,
            path=DOCS_VIEWER_BROWSER_CONFIG_PATH,
            label="Docs Viewer browser config",
        )
        write_browser_config(
            repo_root,
            public_readonly_configs(all_configs),
            path=DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
            label="Docs Viewer public browser config",
        )
        write_browser_config(
            repo_root,
            public_readonly_configs(all_configs),
            path=SITE_DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
            label="Docs Viewer site public browser config",
        )
    only_doc_ids = None if args.only_doc_ids is None else [item.strip() for item in args.only_doc_ids.split(",") if item.strip()]
    try:
        for config in selected:
            builder = DocsDataBuilder(
                repo_root=repo_root,
                config=config,
                source_dir=Path(args.source) if args.source else None,
                output_dir=Path(args.output) if args.output else None,
                viewer_base_url=args.viewer_base_url,
                only_doc_ids=only_doc_ids,
            )
            builder.run(write=args.write, emit_diagnostics=args.diagnostics)
    except FrontMatterSyntaxError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0
