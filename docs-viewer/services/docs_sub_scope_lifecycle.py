#!/usr/bin/env python3
"""Sub-scope lifecycle preview and apply helpers for Docs Viewer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


from docs_lifecycle_paths import (
    load_json_object,
    path_record,
    render_json,
    write_text_atomic,
)
from docs_workspace_config import (
    CONFIG_REL_PATH,
    SCHEMA_VERSION as WORKSPACE_CONFIG_SCHEMA_VERSION,
    SUB_SCOPE_LIFECYCLE_TOOL_ID,
    SOURCE_DOCUMENTS_PATH,
    SOURCE_SUB_SCOPES_PATH,
    DocsStageConfig,
    document_source_path,
    load_docs_stage,
    normalize_sub_scope_id,
    public_documents_path,
    generated_documents_path,
    require_document_authoring,
    resolve_workspace_path,
)
import docs_source_model as source_model


REPORT_ID = "docs_subscope"


class SubScopeLifecycleApplyError(RuntimeError):
    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "sub-scope lifecycle failed"))
        self.payload = payload


LIFECYCLE_APPLY_SCHEMA_VERSION = "docs_sub_scope_lifecycle_apply_v1"
LIFECYCLE_PREVIEW_SCHEMA_VERSION = "docs_sub_scope_lifecycle_preview_v1"


def require_confirmed(body: dict[str, Any]) -> None:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to apply sub-scope lifecycle changes")


def request_stage_config(repo_root: Path, body: dict[str, Any]) -> DocsStageConfig:
    if "scope" in body or "parent_scope" in body:
        raise ValueError("scope and parent_scope are retired; supply an explicit stage")
    return load_docs_stage(repo_root, body.get("stage"))


def normalize_title(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("title must be a non-blank string")
    return " ".join(value.split())


def planned_sub_scope_config_record(sub_scope: str, title: str, lifecycle: dict[str, str]) -> dict[str, Any]:
    return {"sub_scope": sub_scope, "title": title, "lifecycle": lifecycle}


def append_sub_scope_config(
    repo_root: Path,
    sub_scope_config: dict[str, Any],
    *,
    stage: str,
) -> None:
    """Append the collection to its selected source owner, preserving other stages."""
    config_path = repo_root / CONFIG_REL_PATH
    payload = load_json_object(config_path, "Docs workspace config")
    if payload.get("schema_version") != WORKSPACE_CONFIG_SCHEMA_VERSION:
        raise ValueError(f"Docs workspace config schema_version must be {WORKSPACE_CONFIG_SCHEMA_VERSION}")
    stages = payload.get("stages")
    if not isinstance(stages, dict) or not isinstance(stages.get(stage), dict):
        raise ValueError(f"stage {stage!r} is not configured")
    parent_record = stages[stage]
    sub_scopes = parent_record.setdefault("sub_scopes", [])
    if not isinstance(sub_scopes, list):
        raise ValueError(f"stage {stage!r} sub_scopes must be an array")
    sub_scope = str(sub_scope_config.get("sub_scope") or "").strip()
    if any(isinstance(item, dict) and str(item.get("sub_scope") or "").strip() == sub_scope for item in sub_scopes):
        raise ValueError(f"sub_scope {sub_scope!r} already exists in this stage")
    sub_scopes.append(sub_scope_config)
    write_text_atomic(config_path, render_json(payload))

def sub_scope_storage_contract(parent_config: DocsStageConfig, sub_scope: str) -> dict[str, Any]:
    source_root = parent_config.source.location.path / SOURCE_SUB_SCOPES_PATH / sub_scope
    generated_docs = parent_config.generated.documents.location.path.parent / SOURCE_SUB_SCOPES_PATH / sub_scope / "documents"
    public_docs = public_documents_path(parent_config)
    return {
        "publishing_mode": "workspace",
        "public_static_assets": public_docs is not None,
        "access": "embedded_detail_documents",
        "source_root": source_root.as_posix(),
        "docs_output": generated_docs.as_posix(),
        "publish_output": (public_docs / sub_scope).as_posix() if public_docs else "",
        "search_output": "",
        "summary": "Creates a sub-scope source/generated collection and its ordinary report host in the selected stage.",
    }


def sub_scope_path_records(repo_root: Path, parent_config: DocsStageConfig, sub_scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_root = resolve_workspace_path(
        repo_root,
        parent_config.source.location.path / parent_config.source.sub_scopes_path / sub_scope,
    )
    source_documents_root = source_root / SOURCE_DOCUMENTS_PATH
    docs_output = resolve_workspace_path(
        repo_root,
        generated_documents_path(parent_config).parent / SOURCE_SUB_SCOPES_PATH / sub_scope / "documents",
    )
    records = [
        path_record(repo_root, "sub_scope_source_root", source_root, action="create"),
        path_record(repo_root, "sub_scope_source_documents_root", source_documents_root, action="create"),
        path_record(repo_root, "sub_scope_generated_docs_root", docs_output, action="create"),
        path_record(repo_root, "sub_scope_generated_docs_payload_root", docs_output / "by-id", action="create"),
        path_record(repo_root, "sub_scope_manifest", docs_output / "manifest.json", action="generate"),
        path_record(repo_root, "sub_scope_manage_manifest", docs_output / "manage-manifest.json", action="generate"),
    ]
    for media_type in ("img", "svg", "files", "html", "build-source/mermaid"):
        records.append(path_record(repo_root, "sub_scope_source_media", source_root / "media" / media_type, action="create"))
    for media_type in ("img", "svg", "files", "html"):
        records.append(path_record(repo_root, "sub_scope_generated_media", docs_output.parent / "media" / media_type, action="create"))
    if parent_config.stage == "working":
        records.append(
            path_record(
                repo_root,
                "sub_scope_subject_associations",
                docs_output / "subject-associations.json",
                action="generate",
            )
        )
    publish_records: list[dict[str, Any]] = []
    public_output = public_documents_path(parent_config)
    if public_output is not None:
        publish_output = resolve_workspace_path(repo_root, public_output / sub_scope)
        publish_records.extend(
            [
                path_record(repo_root, "sub_scope_public_docs_root", publish_output, action="publish"),
                path_record(repo_root, "sub_scope_public_docs_payload_root", publish_output / "by-id", action="publish"),
            ]
        )
    return records, publish_records


def parent_source_records(
    repo_root: Path,
    parent_config: DocsStageConfig,
) -> list[source_model.SourceDoc]:
    return source_model.load_stage_docs_for_config(repo_root, parent_config)


def report_claimants(
    records: list[source_model.SourceDoc],
    sub_scope: str,
) -> list[source_model.SourceDoc]:
    return [
        document
        for document in records
        if document.report is not None
        and document.report.id == REPORT_ID
        and document.report.sub_scope == sub_scope
    ]


def planned_host_identity(body: dict[str, Any], existing: set[str]) -> dict[str, str]:
    raw = body.get("planned_report_host_identity")
    if raw is None:
        if body.get("confirm") is True:
            raise ValueError("planned_report_host_identity is required for confirmed apply")
        added_date = source_model.current_doc_timestamp()
        return {"doc_id": source_model.allocate_doc_id(added_date, existing), "added_date": added_date}
    if not isinstance(raw, dict) or set(raw) != {"doc_id", "added_date"}:
        raise ValueError("planned_report_host_identity must contain exactly doc_id and added_date")
    doc_id = str(raw.get("doc_id") or "").strip()
    added_date = str(raw.get("added_date") or "").strip()
    if not source_model.is_immutable_doc_id(doc_id):
        raise ValueError("planned_report_host_identity.doc_id must use immutable document identity")
    if not source_model.doc_id_matches_added_date(doc_id, added_date):
        raise ValueError("planned_report_host_identity added_date must match its document ID timestamp")
    if doc_id in existing:
        raise ValueError(f"planned report host identity {doc_id!r} already exists")
    return {"doc_id": doc_id, "added_date": added_date}


def report_host_source(parent_config: DocsStageConfig, sub_scope: str, title: str, identity: dict[str, str]) -> str:
    front_matter: dict[str, Any] = {
        "doc_id": identity["doc_id"],
        "title": title,
        "added_date": identity["added_date"],
        "last_updated": identity["added_date"],
    }
    if source_model.collection_supports_draft(parent_config):
        front_matter["draft"] = True
    body = (
        f"# {title}\n\n"
        ":::report\n"
        f"id: {REPORT_ID}\n"
        f"sub_scope: {sub_scope}\n"
        ":::\n"
    )
    return source_model.format_source(front_matter, body)


def plan_create_sub_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Plan a host and collection in one explicit, writable workflow stage."""
    parent_config = request_stage_config(repo_root, body)
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    title = normalize_title(body.get("title"))
    require_document_authoring(parent_config)
    if any(item.sub_scope == sub_scope for item in parent_config.sub_scopes):
        raise ValueError(f"sub_scope {sub_scope!r} already exists in this stage")

    parent_sources = parent_source_records(repo_root, parent_config)
    claimants = report_claimants(parent_sources, sub_scope)
    if claimants:
        raise ValueError(
            f"sub-scope creation found an existing report host for {sub_scope}: "
            + ", ".join(document.path.name for document in claimants)
        )
    existing = {
        value
        for document in parent_sources
        for value in (document.path.stem, document.doc_id)
        if value
    }
    identity = planned_host_identity(body, existing)
    host_text = report_host_source(parent_config, sub_scope, title, identity)
    host_revision = source_model.source_revision(host_text.encode("utf-8"))
    association = {
        "tool_id": SUB_SCOPE_LIFECYCLE_TOOL_ID,
        "report_host_doc_id": identity["doc_id"],
        "report_host_source_revision": host_revision,
    }
    planned_sub_scope_config = planned_sub_scope_config_record(
        sub_scope, title, association
    )
    created_files, publish_files = sub_scope_path_records(repo_root, parent_config, sub_scope)
    host_path = resolve_workspace_path(repo_root, document_source_path(parent_config)) / f"{identity['doc_id']}.md"
    created_files.append(path_record(repo_root, "report_host_source", host_path, action="create"))
    conflicts = [
        record["path"]
        for record in [*created_files, *publish_files]
        if record.get("exists")
    ]
    if conflicts:
        raise ValueError(f"sub-scope creation would overwrite existing paths: {', '.join(conflicts)}")
    stage_target = {"stage": parent_config.stage}

    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "create_sub_scope",
        "operation": "preview",
        **stage_target,
        "sub_scope": sub_scope,
        "title": title,
        "planned_report_host_identity": identity,
        "report_host_source_revision": host_revision,
        "collection_target": {**stage_target, "sub_scope": sub_scope},
        "report_host_target": {**stage_target, "doc_id": identity["doc_id"]},
        "association": association,
        "planned_sub_scope_config": planned_sub_scope_config,
        "storage_contract": sub_scope_storage_contract(parent_config, sub_scope),
        "created_files": created_files,
        "publish_files": publish_files,
        "changed_files": [
            path_record(repo_root, "workspace_config", repo_root / CONFIG_REL_PATH, action="change"),
        ],
        "rebuild_plan": ["sub_scope_docs", "parent_docs", "browser_config"],
        "urls": {
            "management": f"/docs/?stage={parent_config.stage}&doc={identity['doc_id']}",
            "public": "",
        },
        "warnings": [],
        "summary_text": (
            f"Previewed new Docs Viewer sub-scope {sub_scope} "
            f"with report host {identity['doc_id']}."
        ),
    }


def apply_error(result: dict[str, Any], error: Exception, *, committed: bool, stage: str) -> SubScopeLifecycleApplyError:
    retry_field = "retry_create" if result["action"] == "create_sub_scope" else "retry_delete"
    result.update({"ok": False, "committed": committed, retry_field: False, "failed_stage": stage, "error": str(error)})
    return SubScopeLifecycleApplyError(result)


def apply_create_sub_scope(
    repo_root: Path,
    body: dict[str, Any],
    *,
    dry_run: bool,
    rebuild_sub_scope_outputs: Callable[..., dict[str, Any]],
    rebuild_stage_outputs: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Create the previewed host/config, then rebuild only that collection and parent stage."""
    require_confirmed(body)
    preview = plan_create_sub_scope_preview(repo_root, body)
    result = {**preview, "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION, "operation": "apply", "dry_run": dry_run, "committed": False, "retry_create": True, "rebuild": {}}
    if dry_run:
        return result

    sub_scope = str(preview["sub_scope"])
    parent_config = load_docs_stage(repo_root, preview.get("stage"))
    build_kwargs = {"stage": parent_config.stage}
    identity = preview["planned_report_host_identity"]
    host_text = report_host_source(parent_config, sub_scope, str(preview["title"]), identity)
    host_path = resolve_workspace_path(repo_root, document_source_path(parent_config)) / f"{identity['doc_id']}.md"
    host_created = False
    try:
        source_model.write_text_atomic_new(host_path, host_text)
        host_created = True
        append_sub_scope_config(repo_root, preview["planned_sub_scope_config"], **build_kwargs)
    except Exception as error:
        if host_created and host_path.exists() and host_path.read_text(encoding="utf-8") == host_text:
            host_path.unlink()
        raise apply_error(result, error, committed=False, stage="config_commit") from error

    result.update({"committed": True, "retry_create": False})
    source_root = resolve_workspace_path(
        repo_root,
        parent_config.source.location.path / parent_config.source.sub_scopes_path / sub_scope,
    )
    docs_output = resolve_workspace_path(
        repo_root,
        generated_documents_path(parent_config).parent / SOURCE_SUB_SCOPES_PATH / sub_scope / "documents",
    )
    public_root = public_documents_path(parent_config)
    stage = "roots"
    try:
        (source_root / SOURCE_DOCUMENTS_PATH).mkdir(parents=True, exist_ok=False)
        (docs_output / "by-id").mkdir(parents=True, exist_ok=False)
        for media_type in ("img", "svg", "files", "html", "build-source/mermaid"):
            (source_root / "media" / media_type).mkdir(parents=True, exist_ok=True)
        for media_type in ("img", "svg", "files", "html"):
            (docs_output.parent / "media" / media_type).mkdir(parents=True, exist_ok=True)
        if public_root is not None:
            (resolve_workspace_path(repo_root, public_root / sub_scope) / "by-id").mkdir(parents=True, exist_ok=False)
        stage = "sub_scope_build"
        result["rebuild"]["sub_scope"] = rebuild_sub_scope_outputs(repo_root, sub_scope, **build_kwargs)
        stage = "parent_rebuild"
        result["rebuild"]["parent"] = rebuild_stage_outputs(
            repo_root,
            include_search=False,
            docs_doc_ids=[identity["doc_id"]],
            **({"links_created_doc_ids": [identity["doc_id"]]} if parent_config.stage == "working" else {}),
            **build_kwargs,
        )
    except Exception as error:
        raise apply_error(result, error, committed=True, stage=stage) from error
    result["summary_text"] = f"Created Docs Viewer sub-scope {sub_scope} with report host {identity['doc_id']}."
    return result

def blocked_delete_preview(sub_scope: str, blockers: list[str], **details: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "delete_sub_scope",
        "operation": "preview",
        "sub_scope": sub_scope,
        "allowed": False,
        "blockers": blockers,
        "delete_files": [],
        "missing_files": [],
        "changed_files": [],
        "rebuild_plan": [],
        **details,
    }


def plan_delete_sub_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Keep whole-collection retirement unavailable until its cross-stage contract is defined."""
    config = request_stage_config(repo_root, body)
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    return blocked_delete_preview(
        sub_scope, ["Whole-sub-scope deletion is unavailable in the shared lifecycle."], stage=config.stage,
    )


def apply_delete_sub_scope(
    repo_root: Path,
    body: dict[str, Any],
    *,
    dry_run: bool,
    rebuild_stage_outputs: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Reject retirement without mutating Working, prepared or accepted collections."""
    require_confirmed(body)
    preview = plan_delete_sub_scope_preview(repo_root, body)
    raise ValueError("; ".join(preview["blockers"]))
