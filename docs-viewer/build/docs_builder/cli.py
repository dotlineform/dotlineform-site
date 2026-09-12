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
from .runtime_bootstrap import add_workspace_arguments, apply_workspace_overrides
from .pipeline import DocsDataBuilder
from .source import FrontMatterSyntaxError, InvalidDocIdError, MissingDocIdError
from .sub_scope import SubScopeDocsBuilder, selected_sub_scope
from docs_scope_config import select_scope_stage, require_selected_stage


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer generated document payloads.")
    parser.add_argument("--scope", action="append", default=[], help="Limit build to a named docs scope.")
    parser.add_argument("--stage", choices=("working", "pre-publish"), help="Select the exact Analysis source/generated stage.")
    add_workspace_arguments(parser)
    parser.add_argument("--source", help="Override docs source directory for a single selected scope.")
    parser.add_argument("--output", help="Override docs data output directory for a single selected scope.")
    parser.add_argument("--viewer-base-url", help="Override viewer page URL base for a single selected scope.")
    parser.add_argument("--sub-scope", help="Build a configured sub-scope for a single selected parent scope.")
    parser.add_argument("--only-doc-ids", help="Comma-separated doc ids for a targeted docs payload rebuild.")
    parser.add_argument("--links-doc-ids", help="Exact changed/deleted document ids for Links, independently of ordinary rendering; an empty value selects none.")
    parser.add_argument("--links-created-doc-ids", help="Exact documents created by this operation that require initial Links records.")
    parser.add_argument(
        "--skip-media-builds",
        action="store_true",
        help="Skip registered media producers during a controlled targeted rebuild.",
    )
    parser.add_argument(
        "--skip-browser-config",
        action="store_true",
        help="Skip browser-config writes during a controlled sub-scope or stage rebuild.",
    )
    parser.add_argument("--diagnostics", action="store_true", help="Print machine-readable diagnostics for automation.")
    parser.add_argument("--write", action="store_true", help="Write generated files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    apply_workspace_overrides(args)
    repo_root = Path.cwd().resolve()
    requested_scopes = [scope.strip().lower() for scope in args.scope if scope.strip()]
    configs_by_scope = load_docs_scope_configs(
        repo_root,
        scope_ids=requested_scopes or None,
    )
    selected = list(configs_by_scope.values())
    if args.stage:
        if len(selected) != 1:
            raise RuntimeError("--stage requires one explicit scope")
        selected = [select_scope_stage(selected[0], args.stage)]
    for config in selected:
        require_selected_stage(config)
    if not selected:
        raise RuntimeError(f"Unknown docs scope(s): {', '.join(requested_scopes)}")
    if (args.source or args.output or args.viewer_base_url) and len(selected) != 1:
        raise RuntimeError("--source, --output, and --viewer-base-url can only be used when exactly one scope is selected")
    if args.only_doc_ids and len(selected) != 1:
        raise RuntimeError("--only-doc-ids can only be used when exactly one scope is selected")
    if (args.links_doc_ids is not None or args.links_created_doc_ids is not None) and len(selected) != 1:
        raise RuntimeError("Links document identities require exactly one scope")
    if args.skip_media_builds and len(selected) != 1:
        raise RuntimeError("--skip-media-builds can only be used when exactly one scope is selected")
    if args.sub_scope and len(selected) != 1:
        raise RuntimeError("--sub-scope can only be used when exactly one scope is selected")
    if args.skip_browser_config and not (args.sub_scope or args.stage):
        raise RuntimeError("--skip-browser-config requires --sub-scope or --stage")
    if args.sub_scope and (
        args.source
        or args.output
        or args.viewer_base_url
        or args.only_doc_ids
    ):
        raise RuntimeError(
            "--sub-scope cannot be combined with --source, --output, "
            "--viewer-base-url, or --only-doc-ids"
        )

    replace_scope_ids = requested_scopes or None
    if args.write and not args.skip_browser_config:
        # Local stage configuration retains the complete scope and both stage records.
        write_browser_config(
            repo_root,
            list(configs_by_scope.values()),
            path=DOCS_VIEWER_BROWSER_CONFIG_PATH,
            label="Docs Viewer browser config",
            replace_scope_ids=replace_scope_ids,
        )
    # Stage builds never update the frozen public configuration.
    if args.write and not args.skip_browser_config and not args.stage:
        write_browser_config(
            repo_root,
            public_readonly_configs(selected),
            path=DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
            label="Docs Viewer public browser config",
            published=True,
            replace_scope_ids=replace_scope_ids,
        )
        write_browser_config(
            repo_root,
            public_readonly_configs(selected),
            path=SITE_DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
            label="Docs Viewer site public browser config",
            published=True,
            replace_scope_ids=replace_scope_ids,
        )
    only_doc_ids = None if args.only_doc_ids is None else [item.strip() for item in args.only_doc_ids.split(",") if item.strip()]
    links_doc_ids = None if args.links_doc_ids is None else [item.strip() for item in args.links_doc_ids.split(",") if item.strip()]
    links_created_doc_ids = [item.strip() for item in (args.links_created_doc_ids or "").split(",") if item.strip()]
    try:
        if args.sub_scope:
            config = selected[0]
            sub_scope = selected_sub_scope(config, args.sub_scope.strip().lower())
            builder = SubScopeDocsBuilder(
                repo_root=repo_root,
                config=config,
                sub_scope=sub_scope,
                links_doc_ids=links_doc_ids,
                links_created_doc_ids=links_created_doc_ids,
                skip_media_builds=args.skip_media_builds,
            )
            builder.run(write=args.write, emit_diagnostics=args.diagnostics)
            return 0
        for config in selected:
            builder = DocsDataBuilder(
                repo_root=repo_root,
                config=config,
                source_dir=Path(args.source) if args.source else None,
                output_dir=Path(args.output) if args.output else None,
                viewer_base_url=args.viewer_base_url,
                only_doc_ids=only_doc_ids,
                links_doc_ids=links_doc_ids,
                links_created_doc_ids=links_created_doc_ids,
                skip_media_builds=args.skip_media_builds,
            )
            builder.run(write=args.write, emit_diagnostics=args.diagnostics)
    except (FrontMatterSyntaxError, InvalidDocIdError, MissingDocIdError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0
