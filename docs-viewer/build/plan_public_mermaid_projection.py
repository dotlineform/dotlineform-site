#!/usr/bin/env python3
"""Dry-run public Mermaid projection planning for one configured public scope."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

from docs_builder.runtime_bootstrap import apply_repo_local_env, projects_base_dir_from_argv

if __name__ == "__main__":
    apply_repo_local_env(projects_base_dir=projects_base_dir_from_argv(sys.argv[1:]))

from docs_builder.common import is_public_readonly_scope, load_docs_scope_configs
from docs_builder.pipeline import DocsDataBuilder
from docs_builder.sub_scope import SubScopeDocsBuilder, selected_sub_scope
from docs_artifact_locations import ArtifactLocation
from docs_public_mermaid_projection import (
    plan_public_mermaid_projection,
    public_mermaid_projection_report,
)


MANIFEST_FILENAME = "manifest.json"
PREPARED_PROJECTION_RELATIVE_PATH = Path(".publish/public-mermaid-projection")


@dataclass(frozen=True)
class ProjectionPlanningContext:
    plan: dict[str, Any]
    manifest_path: Path
    prepared_location: ArtifactLocation
    previous_manifest: dict[str, Any] | None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan public light/dark Mermaid projection pairs without writing."
    )
    parser.add_argument("--scope", required=True, help="Configured public Docs Viewer scope.")
    parser.add_argument("--sub-scope", help="Configured public Docs Viewer sub-scope.")
    parser.add_argument(
        "--projects-base-dir",
        help="Override DOTLINEFORM_PROJECTS_BASE_DIR after loading .env.local.",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Print the machine-readable source-free projection report.",
    )
    return parser.parse_args(argv)


def _read_previous_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"public Mermaid projection manifest must be a JSON object: {path}")
    return payload


def load_projection_planning_context(
    repo_root: Path,
    *,
    scope_id: str,
    sub_scope_id: str = "",
) -> ProjectionPlanningContext:
    normalized_scope = str(scope_id or "").strip().lower()
    configs = load_docs_scope_configs(repo_root, scope_ids=[normalized_scope])
    config = configs.get(normalized_scope)
    if config is None:
        raise ValueError(f"unsupported docs scope: {normalized_scope}")
    if config.scope_type != "public" or not is_public_readonly_scope(
        viewer_base_url=config.viewer_base_url,
        include_scope_param=config.include_scope_param,
    ):
        raise ValueError(f"scope {normalized_scope!r} is not a public read-only scope")

    normalized_sub_scope = str(sub_scope_id or "").strip().lower()
    if normalized_sub_scope:
        sub_scope = selected_sub_scope(config, normalized_sub_scope)
        if sub_scope.public_projection is None:
            raise ValueError(
                f"sub-scope {normalized_scope}/{normalized_sub_scope} has no public projection"
            )
        builder = SubScopeDocsBuilder(
            repo_root=repo_root,
            config=config,
            sub_scope=sub_scope,
        )
        manifest_scope = f"{normalized_scope}/{normalized_sub_scope}"
        published_documents_location = sub_scope.published.documents.location
    else:
        if config.public_projection is None:
            raise ValueError(f"scope {normalized_scope!r} has no public projection")
        builder = DocsDataBuilder(
            repo_root=repo_root,
            config=config,
            skip_media_builds=True,
        )
        manifest_scope = normalized_scope
        published_documents_location = config.published.documents.location

    docs = builder.load_docs()
    builder.validate_canonical_doc_ids(docs)
    builder.validate_docs(docs)
    eligible_docs = docs if normalized_sub_scope else builder.public_recent_docs(docs)
    prepared_location = ArtifactLocation(
        provider=published_documents_location.provider,
        path=published_documents_location.path / PREPARED_PROJECTION_RELATIVE_PATH,
    )
    manifest_path = (
        builder.output_dir
        / PREPARED_PROJECTION_RELATIVE_PATH
        / MANIFEST_FILENAME
    )
    previous_manifest = _read_previous_manifest(manifest_path)
    plan = plan_public_mermaid_projection(
        scope=manifest_scope,
        documents=((doc.doc_id, doc.body_markdown) for doc in eligible_docs),
        public_url_prefix=builder.output_url_base,
        previous_manifest=previous_manifest,
    )
    return ProjectionPlanningContext(
        plan=plan,
        manifest_path=manifest_path,
        prepared_location=prepared_location,
        previous_manifest=previous_manifest,
    )


def build_projection_plan(
    repo_root: Path,
    *,
    scope_id: str,
    sub_scope_id: str = "",
) -> tuple[dict[str, Any], Path]:
    context = load_projection_planning_context(
        repo_root,
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
    )
    return context.plan, context.manifest_path


def print_human_report(plan: dict[str, Any], manifest_path: Path, repo_root: Path) -> None:
    summary = plan["summary"]
    manifest_label = (
        manifest_path.resolve().relative_to(repo_root.resolve()).as_posix()
        if manifest_path.resolve().is_relative_to(repo_root.resolve())
        else str(manifest_path)
    )
    print(f"Public Mermaid projection plan (dry-run) scope={plan['scope']}")
    print(f"  diagrams total: {summary['diagram_count']}")
    print(f"  variants total: {summary['variant_count']}")
    print(f"  diagrams would create: {summary['create_count']}")
    print(f"  diagrams would replace: {summary['replace_count']}")
    print(f"  diagrams unchanged: {summary['unchanged_count']}")
    print(f"  failures: {summary['failure_count']}")
    print(f"  diagram families would remove: {summary['removal_family_count']}")
    print(f"  variants would remove: {summary['removal_variant_count']}")
    print(f"  next manifest: {manifest_label} (not written)")
    for item in plan["diagrams"]:
        projection = item["projection"]
        variants = projection["variants"]
        print(
            f"  {item['action']} {projection['projection_id']}: "
            f"light={variants['light']['artifact_identity']} "
            f"dark={variants['dark']['artifact_identity']}"
        )
    for failure in plan["failures"]:
        print(
            f"  failed {failure['projection_id']} line={failure['source_line']}: "
            f"{failure['message']}"
        )
    for removal in plan["removals"]:
        print(
            f"  remove {removal['projection_id']}: "
            + " ".join(removal["variant_identities"])
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path.cwd().resolve()
    try:
        plan, manifest_path = build_projection_plan(
            repo_root,
            scope_id=args.scope,
            sub_scope_id=args.sub_scope or "",
        )
    except (json.JSONDecodeError, RuntimeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    print_human_report(plan, manifest_path, repo_root)
    if args.diagnostics:
        report = public_mermaid_projection_report(plan)
        report["manifest_path"] = (
            manifest_path.resolve().relative_to(repo_root).as_posix()
            if manifest_path.resolve().is_relative_to(repo_root)
            else str(manifest_path)
        )
        print(
            "Public Mermaid projection diagnostics: "
            + json.dumps(report, ensure_ascii=False, separators=(",", ":"))
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
