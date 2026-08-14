#!/usr/bin/env python3
"""Sub-scope lifecycle preview and apply helpers for Docs Viewer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import docs_public_delete_cleanup as public_delete_cleanup

from docs_lifecycle_paths import (
    delete_manifest_paths,
    load_json_object,
    path_record,
    render_json,
    write_text_atomic,
)
from docs_scope_config import (
    CONFIG_REL_PATH,
    SCHEMA_VERSION as SCOPE_CONFIG_SCHEMA_VERSION,
    SCOPE_LIFECYCLE_TOOL_ID,
    SOURCE_DOCUMENTS_PATH,
    SOURCE_SUB_SCOPES_PATH,
    DocsScopeConfig,
    document_source_path,
    is_public_readonly_scope,
    load_docs_scope_configs,
    normalize_sub_scope_id,
    public_documents_path,
    published_documents_path,
    resolve_scope_path,
    source_container_path,
)
from docs_scope_manifest import (
    LIFECYCLE_APPLY_SCHEMA_VERSION,
    LIFECYCLE_PREVIEW_SCHEMA_VERSION,
    normalize_scope_id,
    normalize_title,
    require_confirmed,
)
import docs_source_model as source_model


REPORT_ID = "docs_subscope"
REPORT_ACCESS = "local"


class SubScopeLifecycleApplyError(RuntimeError):
    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "sub-scope lifecycle failed"))
        self.payload = payload


def find_raw_scope_config(payload: dict[str, Any], scope_id: str) -> dict[str, Any]:
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("docs scope config scopes must be an array")
    for item in scopes:
        if isinstance(item, dict) and str(item.get("scope_id") or "").strip() == scope_id:
            return item
    raise ValueError(f"scope_id {scope_id!r} is missing from docs scope config")


def planned_sub_scope_config_record(
    parent_config: DocsScopeConfig,
    sub_scope: str,
    title: str,
    lifecycle: dict[str, str],
) -> dict[str, Any]:
    projection = None
    if parent_config.public_projection is not None:
        projection = {
            "documents": {
                "location": {
                    "provider": "repository",
                    "path": (parent_config.public_projection.documents.location.path / sub_scope).as_posix(),
                }
            },
            "search": None,
        }
    return {
        "sub_scope": sub_scope,
        "title": title,
        "public_projection": projection,
        "lifecycle": lifecycle,
    }


def append_sub_scope_config(repo_root: Path, parent_scope: str, sub_scope_config: dict[str, Any]) -> None:
    config_path = repo_root / CONFIG_REL_PATH
    payload = load_json_object(config_path, "docs scope config")
    if payload.get("schema_version") != SCOPE_CONFIG_SCHEMA_VERSION:
        raise ValueError(f"docs scope config schema_version must be {SCOPE_CONFIG_SCHEMA_VERSION}")
    parent_record = find_raw_scope_config(payload, parent_scope)
    sub_scopes = parent_record.setdefault("sub_scopes", [])
    if not isinstance(sub_scopes, list):
        raise ValueError(f"scope_id {parent_scope!r} sub_scopes must be an array")
    sub_scope = str(sub_scope_config.get("sub_scope") or "").strip()
    if any(isinstance(item, dict) and str(item.get("sub_scope") or "").strip() == sub_scope for item in sub_scopes):
        raise ValueError(f"sub_scope {sub_scope!r} already exists in scope {parent_scope!r}")
    sub_scopes.append(sub_scope_config)
    write_text_atomic(config_path, render_json(payload))


def remove_sub_scope_config(repo_root: Path, parent_scope: str, sub_scope: str) -> None:
    config_path = repo_root / CONFIG_REL_PATH
    payload = load_json_object(config_path, "docs scope config")
    if payload.get("schema_version") != SCOPE_CONFIG_SCHEMA_VERSION:
        raise ValueError(f"docs scope config schema_version must be {SCOPE_CONFIG_SCHEMA_VERSION}")
    parent_record = find_raw_scope_config(payload, parent_scope)
    sub_scopes = parent_record.get("sub_scopes")
    if not isinstance(sub_scopes, list):
        raise ValueError(f"sub_scope {sub_scope!r} is missing from scope {parent_scope!r}")
    retained = [
        item
        for item in sub_scopes
        if not (isinstance(item, dict) and str(item.get("sub_scope") or "").strip() == sub_scope)
    ]
    if len(retained) == len(sub_scopes):
        raise ValueError(f"sub_scope {sub_scope!r} is missing from scope {parent_scope!r}")
    if retained:
        parent_record["sub_scopes"] = retained
    else:
        parent_record.pop("sub_scopes", None)
    write_text_atomic(config_path, render_json(payload))


def sub_scope_storage_contract(
    parent_scope: str,
    parent_config: DocsScopeConfig,
    sub_scope: str,
    sub_scope_config: dict[str, Any],
    *,
    public_static_assets: bool,
) -> dict[str, Any]:
    projection = sub_scope_config.get("public_projection")
    source_root = (
        parent_config.source.location.path / SOURCE_SUB_SCOPES_PATH / sub_scope
    ).as_posix()
    published_docs = (
        parent_config.published.documents.location.path / SOURCE_SUB_SCOPES_PATH / sub_scope
    ).as_posix()
    public_docs = (
        str(projection["documents"]["location"]["path"])
        if isinstance(projection, dict)
        else published_docs
    )
    return {
        "publishing_mode": "parent_scope",
        "public_static_assets": public_static_assets,
        "access": "embedded_detail_documents",
        "source_root": source_root,
        "docs_output": published_docs,
        "publish_output": public_docs,
        "search_output": "",
        "summary": (
            f"Sub-scope under {parent_scope}: creates nested source and published payload roots "
            "plus one parent report host. It does not create a top-level scope, route, or scope "
            "selector entry."
        ),
    }


def sub_scope_path_records(repo_root: Path, parent_config: DocsScopeConfig, sub_scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_root = resolve_scope_path(
        repo_root,
        parent_config.source.location.path / parent_config.source.sub_scopes_path / sub_scope,
    )
    source_documents_root = source_root / SOURCE_DOCUMENTS_PATH
    docs_output = resolve_scope_path(
        repo_root,
        published_documents_path(parent_config) / SOURCE_SUB_SCOPES_PATH / sub_scope,
    )
    records = [
        path_record(repo_root, "sub_scope_source_root", source_root, action="create"),
        path_record(repo_root, "sub_scope_source_documents_root", source_documents_root, action="create"),
        path_record(repo_root, "sub_scope_published_docs_root", docs_output, action="create"),
        path_record(repo_root, "sub_scope_published_docs_payload_root", docs_output / "by-id", action="create"),
        path_record(repo_root, "sub_scope_manifest", docs_output / "manifest.json", action="generate"),
        path_record(repo_root, "sub_scope_manage_manifest", docs_output / "manage-manifest.json", action="generate"),
    ]
    if not is_public_readonly_scope(
        viewer_base_url=parent_config.viewer_base_url,
        include_scope_param=parent_config.include_scope_param,
    ):
        records.append(
            path_record(
                repo_root,
                "sub_scope_subject_associations",
                docs_output / "subject-associations.json",
                action="generate",
            )
        )
    selected_sub_scopes = [
        item for item in parent_config.sub_scopes if item.sub_scope == sub_scope
    ]
    customisation = (
        selected_sub_scopes[0].sub_scope_customisation
        if len(selected_sub_scopes) == 1
        else None
    )
    if (
        customisation is not None
        and customisation.customisation_id == "analysis_tags"
    ):
        records.append(
            path_record(
                repo_root,
                "sub_scope_tag_associations",
                docs_output / "tag-associations.json",
                action="generate",
            )
        )
    publish_records: list[dict[str, Any]] = []
    public_output = public_documents_path(parent_config)
    if public_output is not None:
        publish_output = resolve_scope_path(repo_root, public_output / sub_scope)
        publish_records.extend(
            [
                path_record(repo_root, "sub_scope_public_docs_root", publish_output, action="publish"),
                path_record(repo_root, "sub_scope_public_docs_payload_root", publish_output / "by-id", action="publish"),
            ]
        )
    return records, publish_records


def parent_source_records(
    repo_root: Path,
    parent_config: DocsScopeConfig,
) -> list[source_model.ScopeDoc]:
    return source_model.load_scope_docs_for_config(repo_root, parent_config)


def report_claimants(
    records: list[source_model.ScopeDoc],
    sub_scope: str,
) -> list[source_model.ScopeDoc]:
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


def report_host_source(parent_config: DocsScopeConfig, sub_scope: str, title: str, identity: dict[str, str]) -> str:
    front_matter: dict[str, Any] = {
        "doc_id": identity["doc_id"],
        "title": title,
        "added_date": identity["added_date"],
        "last_updated": identity["added_date"],
    }
    body = (
        f"# {title}\n\n"
        ":::report\n"
        f"id: {REPORT_ID}\n"
        f"access: {REPORT_ACCESS}\n"
        f"sub_scope: {sub_scope}\n"
        ":::\n"
    )
    return source_model.format_source(front_matter, body)


def plan_create_sub_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    parent_scope = normalize_scope_id(body.get("parent_scope") or body.get("scope"))
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    title = normalize_title(body.get("title"))
    configs = load_docs_scope_configs(repo_root)
    parent_config = configs.get(parent_scope)
    if parent_config is None:
        raise ValueError(f"parent scope {parent_scope!r} does not exist")
    if any(item.sub_scope == sub_scope for item in parent_config.sub_scopes):
        raise ValueError(f"sub_scope {sub_scope!r} already exists in scope {parent_scope!r}")

    parent_sources = parent_source_records(repo_root, parent_config)
    claimants = report_claimants(parent_sources, sub_scope)
    if claimants:
        raise ValueError(
            f"sub-scope creation found an existing report host for {parent_scope}/{sub_scope}: "
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
        "tool_id": SCOPE_LIFECYCLE_TOOL_ID,
        "report_host_doc_id": identity["doc_id"],
        "report_host_source_revision": host_revision,
    }
    planned_sub_scope_config = planned_sub_scope_config_record(
        parent_config, sub_scope, title, association
    )
    created_files, publish_files = sub_scope_path_records(repo_root, parent_config, sub_scope)
    host_path = resolve_scope_path(repo_root, document_source_path(parent_config)) / f"{identity['doc_id']}.md"
    created_files.append(path_record(repo_root, "report_host_source", host_path, action="create"))
    conflicts = [
        record["path"]
        for record in [*created_files, *publish_files]
        if record.get("exists")
    ]
    if conflicts:
        raise ValueError(f"sub-scope creation would overwrite existing paths: {', '.join(conflicts)}")
    public_readonly = parent_config.public_projection is not None

    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "create_sub_scope",
        "operation": "preview",
        "scope_id": parent_scope,
        "parent_scope": parent_scope,
        "sub_scope": sub_scope,
        "title": title,
        "planned_report_host_identity": identity,
        "report_host_source_revision": host_revision,
        "collection_target": {"scope": parent_scope, "sub_scope": sub_scope},
        "report_host_target": {"scope": parent_scope, "doc_id": identity["doc_id"]},
        "association": association,
        "planned_sub_scope_config": planned_sub_scope_config,
        "storage_contract": sub_scope_storage_contract(
            parent_scope,
            parent_config,
            sub_scope,
            planned_sub_scope_config,
            public_static_assets=public_readonly,
        ),
        "created_files": created_files,
        "publish_files": publish_files,
        "changed_files": [
            path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
        ],
        "rebuild_plan": ["sub_scope_docs", "parent_docs", "parent_search", "browser_config"],
        "urls": {
            "management": f"/docs/?scope={parent_scope}&doc={identity['doc_id']}",
            "public": "",
        },
        "warnings": [],
        "summary_text": (
            f"Previewed new Docs Viewer sub-scope {parent_scope}/{sub_scope} "
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
    rebuild_sub_scope_outputs: Callable[[Path, str, str], dict[str, Any]],
    rebuild_scope_outputs: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    require_confirmed(body)
    preview = plan_create_sub_scope_preview(repo_root, body)
    result = {**preview, "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION, "operation": "apply", "dry_run": dry_run, "committed": False, "retry_create": True, "rebuild": {}}
    if dry_run:
        return result

    scope = str(preview["parent_scope"])
    sub_scope = str(preview["sub_scope"])
    parent_config = load_docs_scope_configs(repo_root)[scope]
    identity = preview["planned_report_host_identity"]
    host_text = report_host_source(parent_config, sub_scope, str(preview["title"]), identity)
    host_path = resolve_scope_path(repo_root, document_source_path(parent_config)) / f"{identity['doc_id']}.md"
    host_created = False
    try:
        source_model.write_text_atomic_new(host_path, host_text)
        host_created = True
        append_sub_scope_config(repo_root, scope, preview["planned_sub_scope_config"])
    except Exception as error:
        if host_created and host_path.exists() and host_path.read_text(encoding="utf-8") == host_text:
            host_path.unlink()
        raise apply_error(result, error, committed=False, stage="config_commit") from error

    result.update({"committed": True, "retry_create": False})
    source_root = resolve_scope_path(
        repo_root,
        parent_config.source.location.path / parent_config.source.sub_scopes_path / sub_scope,
    )
    docs_output = resolve_scope_path(
        repo_root,
        published_documents_path(parent_config) / SOURCE_SUB_SCOPES_PATH / sub_scope,
    )
    public_root = public_documents_path(parent_config)
    stage = "roots"
    try:
        (source_root / SOURCE_DOCUMENTS_PATH).mkdir(parents=True, exist_ok=False)
        (docs_output / "by-id").mkdir(parents=True, exist_ok=False)
        if public_root is not None:
            (resolve_scope_path(repo_root, public_root / sub_scope) / "by-id").mkdir(parents=True, exist_ok=False)
        stage = "sub_scope_build"
        result["rebuild"]["sub_scope"] = rebuild_sub_scope_outputs(repo_root, scope, sub_scope)
        stage = "parent_rebuild"
        result["rebuild"]["parent"] = rebuild_scope_outputs(
            repo_root,
            scope,
            include_search=False,
            docs_doc_ids=[identity["doc_id"]],
        )
    except Exception as error:
        raise apply_error(result, error, committed=True, stage=stage) from error
    result["summary_text"] = f"Created Docs Viewer sub-scope {scope}/{sub_scope} with report host {identity['doc_id']}."
    return result


def sub_scope_delete_path_records(repo_root: Path, sub_scope_config: Any, parent_config: DocsScopeConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_paths = [
        ("sub_scope_source_root", resolve_scope_path(repo_root, source_container_path(sub_scope_config))),
        ("sub_scope_published_docs_root", resolve_scope_path(repo_root, published_documents_path(sub_scope_config))),
    ]
    public_output = public_documents_path(sub_scope_config)
    if public_output is not None:
        candidate_paths.append(("sub_scope_public_docs_root", resolve_scope_path(repo_root, public_output)))

    delete_files: list[dict[str, Any]] = []
    missing_files: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for kind, path in candidate_paths:
        key = path.resolve().as_posix()
        if key in seen_paths:
            continue
        seen_paths.add(key)
        record = path_record(repo_root, kind, path, action="delete")
        if path.exists():
            delete_files.append(record)
        else:
            missing_files.append(record)
    return delete_files, missing_files


def blocked_delete_preview(parent_scope: str, sub_scope: str, blockers: list[str], **details: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "delete_sub_scope",
        "operation": "preview",
        "scope_id": parent_scope,
        "parent_scope": parent_scope,
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
    parent_scope = normalize_scope_id(body.get("parent_scope") or body.get("scope"))
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    configs = load_docs_scope_configs(repo_root)
    parent_config = configs.get(parent_scope)
    if parent_config is None:
        return blocked_delete_preview(parent_scope, sub_scope, [f"parent scope {parent_scope!r} does not exist"])
    matching = [item for item in parent_config.sub_scopes if item.sub_scope == sub_scope]
    if not matching:
        return blocked_delete_preview(parent_scope, sub_scope, [f"sub_scope {sub_scope!r} is not configured in scope {parent_scope!r}"])

    sub_scope_config = matching[0]
    lifecycle = sub_scope_config.lifecycle
    if lifecycle is None:
        return blocked_delete_preview(
            parent_scope, sub_scope,
            ["sub-scope has no lifecycle-created report-host association"],
            title=sub_scope_config.title,
        )
    association = {
        "tool_id": lifecycle.tool_id,
        "report_host_doc_id": lifecycle.report_host_doc_id,
        "report_host_source_revision": lifecycle.report_host_source_revision,
    }
    host_target = {"scope": parent_scope, "doc_id": lifecycle.report_host_doc_id}
    host_path = resolve_scope_path(repo_root, document_source_path(parent_config)) / f"{lifecycle.report_host_doc_id}.md"
    details = {
        "title": sub_scope_config.title,
        "association": association,
        "report_host_target": host_target,
        "recorded_report_host_source_revision": lifecycle.report_host_source_revision,
    }
    if not host_path.is_file():
        return blocked_delete_preview(parent_scope, sub_scope, ["lifecycle-associated report host source is missing"], **details)

    revision = source_model.source_revision(host_path.read_bytes())
    parent_documents = parent_source_records(repo_root, parent_config)
    host_document = next(
        (
            document
            for document in parent_documents
            if document.path.resolve() == host_path.resolve()
        ),
        None,
    )
    blockers = []
    if revision != lifecycle.report_host_source_revision:
        blockers.append("Report host edited since creation")
    if (
        host_document is None
        or host_document.doc_id != lifecycle.report_host_doc_id
        or host_document.report is None
        or host_document.report.id != REPORT_ID
        or host_document.report.access != REPORT_ACCESS
        or host_document.report.sub_scope != sub_scope
    ):
        blockers.append("lifecycle-associated report host is detached")
    claimants = report_claimants(parent_documents, sub_scope)
    if len(claimants) != 1 or claimants[0].path.resolve() != host_path.resolve():
        blockers.append("sub-scope report-host association is ambiguous")
    if blockers:
        return blocked_delete_preview(
            parent_scope, sub_scope, blockers,
            current_report_host_source_revision=revision, **details,
        )

    delete_files, missing_files = sub_scope_delete_path_records(repo_root, sub_scope_config, parent_config)
    delete_files.append(path_record(repo_root, "report_host_source", host_path, action="delete"))
    public_cleanup_plan = public_delete_cleanup.plan_public_document_delete_cleanup(
        repo_root,
        scope=parent_scope,
        doc_ids=[lifecycle.report_host_doc_id],
    )
    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "delete_sub_scope",
        "operation": "preview",
        "scope_id": parent_scope,
        "parent_scope": parent_scope,
        "sub_scope": sub_scope,
        "title": sub_scope_config.title,
        "allowed": True,
        "blockers": [],
        "collection_target": {"scope": parent_scope, "sub_scope": sub_scope},
        "report_host_target": host_target,
        "report_host_source_revision": revision,
        "association": association,
        "delete_files": delete_files,
        "missing_files": missing_files,
        "changed_files": [
            path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
        ],
        "rebuild_plan": ["parent_docs", "parent_search", "browser_config"],
        "public_cleanup": public_cleanup_plan.response(repo_root),
        "summary_text": f"Previewed deletion for Docs Viewer sub-scope {parent_scope}/{sub_scope} and report host {lifecycle.report_host_doc_id}.",
    }


def apply_delete_sub_scope(
    repo_root: Path,
    body: dict[str, Any],
    *,
    dry_run: bool,
    rebuild_scope_outputs: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    require_confirmed(body)
    preview = plan_delete_sub_scope_preview(repo_root, body)
    if not preview.get("allowed"):
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        raise ValueError("; ".join(str(blocker) for blocker in blockers) or "sub-scope delete is not allowed")

    result = {
        **preview,
        "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION,
        "operation": "apply",
        "dry_run": dry_run,
        "committed": False,
        "retry_delete": True,
        "deleted_files": preview["delete_files"],
        "rebuild": {},
        "urls": {"management": f"/docs/?scope={preview['parent_scope']}", "public": ""},
    }
    if dry_run:
        return result

    scope = str(preview["parent_scope"])
    sub_scope = str(preview["sub_scope"])
    host_id = str(preview["report_host_target"]["doc_id"])
    public_cleanup_plan = public_delete_cleanup.plan_public_document_delete_cleanup(
        repo_root,
        scope=scope,
        doc_ids=[host_id],
    )
    try:
        remove_sub_scope_config(repo_root, scope, sub_scope)
    except Exception as error:
        raise apply_error(result, error, committed=False, stage="config_commit") from error

    result.update({"committed": True, "retry_delete": False})
    try:
        delete_manifest_paths(repo_root, preview["delete_files"])
        result["rebuild"]["parent"] = rebuild_scope_outputs(
            repo_root,
            scope,
            include_search=False,
            docs_doc_ids=[host_id],
        )
        try:
            result["public_cleanup"] = (
                public_delete_cleanup.apply_public_document_delete_cleanup(
                    repo_root,
                    public_cleanup_plan,
                )
            )
        except public_delete_cleanup.PublicDeleteCleanupApplyError as error:
            result["public_cleanup"] = error.result
            raise
    except Exception as error:
        stage = (
            "public_cleanup"
            if isinstance(error, public_delete_cleanup.PublicDeleteCleanupApplyError)
            else "cleanup_rebuild"
        )
        raise apply_error(result, error, committed=True, stage=stage) from error
    result["summary_text"] = f"Deleted Docs Viewer sub-scope {scope}/{sub_scope} and report host {host_id}."
    return result
