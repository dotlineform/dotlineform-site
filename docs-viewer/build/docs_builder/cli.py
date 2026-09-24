from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .browser_config import write_browser_config
from .common import DOCS_VIEWER_BROWSER_CONFIG_PATH, load_docs_workspace_config
from .runtime_bootstrap import add_workspace_arguments, apply_workspace_overrides
from .pipeline import DocsDataBuilder
from .source import FrontMatterSyntaxError, InvalidDocIdError, MissingDocIdError
from .collection import CollectionDocsBuilder, selected_collection
from docs_workspace_config import select_workspace_stage


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer generated document payloads.")
    parser.add_argument("--stage", choices=("working", "preview"), required=True, help="Select the exact source/generated stage.")
    add_workspace_arguments(parser)
    parser.add_argument("--source", help="Override the selected stage's docs source directory.")
    parser.add_argument("--output", help="Override the selected stage's generated document directory.")
    parser.add_argument("--viewer-base-url", help="Override the local viewer page URL base.")
    parser.add_argument("--collection", help="Build one configured collection in the selected stage.")
    parser.add_argument("--only-doc-ids", help="Comma-separated doc ids for a targeted docs payload rebuild.")
    parser.add_argument("--links-doc-ids", help="Exact changed/deleted document ids for Links, independently of ordinary rendering; an empty value selects none.")
    parser.add_argument("--links-created-doc-ids", help="Exact documents created by this operation that require initial Links records.")
    parser.add_argument("--skip-media-builds", action="store_true", help="Skip registered media producers during a controlled rebuild.")
    parser.add_argument("--skip-browser-config", action="store_true", help="Skip browser-config writes during a controlled rebuild.")
    parser.add_argument("--diagnostics", action="store_true", help="Print machine-readable diagnostics for automation.")
    parser.add_argument("--write", action="store_true", help="Write generated files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.stage == "preview" and not args.docs_base_dir:
        raise ValueError("Preview builds require explicit temporary --docs-base-dir inputs; use Prepare Preview")
    apply_workspace_overrides(args)
    repo_root = Path.cwd().resolve()
    workspace = load_docs_workspace_config(repo_root)
    config = select_workspace_stage(workspace, args.stage)
    if args.collection and (args.source or args.output or args.viewer_base_url):
        raise RuntimeError("--collection cannot be combined with --source, --output, or --viewer-base-url")
    if args.write and not args.skip_browser_config:
        write_browser_config(repo_root, workspace, path=DOCS_VIEWER_BROWSER_CONFIG_PATH, label="Docs Viewer browser config")
    only_doc_ids = None if args.only_doc_ids is None else [item.strip() for item in args.only_doc_ids.split(",") if item.strip()]
    links_doc_ids = None if args.links_doc_ids is None else [item.strip() for item in args.links_doc_ids.split(",") if item.strip()]
    links_created_doc_ids = [item.strip() for item in (args.links_created_doc_ids or "").split(",") if item.strip()]
    try:
        if args.collection:
            builder = CollectionDocsBuilder(
                repo_root=repo_root, config=config, collection=selected_collection(config, args.collection),
                only_doc_ids=only_doc_ids,
                links_doc_ids=links_doc_ids, links_created_doc_ids=links_created_doc_ids,
                skip_media_builds=args.skip_media_builds,
            )
        else:
            builder = DocsDataBuilder(
                repo_root=repo_root, config=config,
                source_dir=Path(args.source) if args.source else None,
                output_dir=Path(args.output) if args.output else None,
                viewer_base_url=args.viewer_base_url, only_doc_ids=only_doc_ids,
                links_doc_ids=links_doc_ids, links_created_doc_ids=links_created_doc_ids,
                skip_media_builds=args.skip_media_builds,
            )
        builder.run(write=args.write, emit_diagnostics=args.diagnostics)
    except (FrontMatterSyntaxError, InvalidDocIdError, MissingDocIdError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0
