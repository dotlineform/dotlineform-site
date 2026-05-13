#!/usr/bin/env python3
"""Documents adapter for Studio Data Sharing workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Callable, Dict, Optional

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from docs_export import build_export, parse_doc_ids as parse_export_doc_ids
from docs_import import list_staged_import_files, parse_staged_import, render_markdown_previews
import docs_management_mutations as mutations
import docs_source_model as source_model
from studio.data_sharing_adapters import AdapterResolution
from studio import data_sharing_service


LogEvent = Callable[[Path, str, Dict[str, Any]], None]
MakeBackupBundle = Callable[[Path, str, str, list[source_model.ScopeDoc], Optional[Dict[str, Any]]], Path]
PerformSourceWriteAndRebuild = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class DocumentsDataSharingDependencies:
    log_event: LogEvent
    make_backup_bundle: MakeBackupBundle
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild


def normalize_summary(value: Any) -> str:
    return mutations.normalize_summary(value)


def relative_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_documents_adapter(repo_root: Path, data_domain: Any, operation: str) -> AdapterResolution:
    adapter = data_sharing_service.resolve_for_service(repo_root, data_domain, operation)
    return require_documents_adapter(adapter)


def require_documents_adapter(adapter: AdapterResolution) -> AdapterResolution:
    if str(adapter.adapter.get("module") or "").strip() != "documents":
        raise ValueError(f"adapter {adapter.adapter_id!r} is not implemented by the documents service")
    return adapter


def prepare_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_documents_adapter(adapter or resolve_documents_adapter(repo_root, body.get("data_domain"), "prepare"))
    scope = source_model.normalize_scope(adapter.scope)
    config_id = str(body.get("config_id") or "").strip()
    if not config_id:
        raise ValueError("config_id is required")

    raw_doc_ids = body.get("doc_ids", [])
    if raw_doc_ids is None:
        raw_doc_ids = []
    if not isinstance(raw_doc_ids, list):
        raise ValueError("doc_ids must be a list")
    doc_ids = parse_export_doc_ids([str(doc_id or "") for doc_id in raw_doc_ids])
    select_all = bool(body.get("select_all"))
    missing_summary_only = body.get("missing_summary_only")
    if missing_summary_only is not None and not isinstance(missing_summary_only, bool):
        raise ValueError("missing_summary_only must be true, false, or null")
    target_format = str(body.get("target_format") or "").strip()

    report = build_export(
        repo_root=repo_root,
        config_id=config_id,
        scope=scope,
        selected_doc_ids=doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
        write=not dry_run,
        config_path=adapter.config_path("sharing_profiles_path").as_posix(),
        target_format=target_format or None,
        output_root=adapter.path("outbound_package_root"),
    )
    report["data_domain"] = adapter.data_domain
    report["adapter_id"] = adapter.adapter_id
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-export",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "scope": scope,
                "config_id": config_id,
                "dry_run": dry_run,
                "target_format": report.get("target_format", ""),
                "output_written": bool(report.get("output_written")),
                "selected": int(report.get("counts", {}).get("selected") or 0),
                "exported": int(report.get("counts", {}).get("exported") or 0),
                "skipped": int(report.get("counts", {}).get("skipped") or 0),
                "failed": int(report.get("counts", {}).get("failed") or 0),
                "truncated": int(report.get("counts", {}).get("truncated") or 0),
                "errors": int(report.get("issue_counts", {}).get("errors") or 0),
                "warnings": int(report.get("issue_counts", {}).get("warnings") or 0),
            },
        )
    if report.get("ok"):
        action = "Validated package" if dry_run else "Prepared package"
        suffix = " without writing." if dry_run else "."
        exported_count = int(report.get("counts", {}).get("exported") or 0)
        document_word = "document" if exported_count == 1 else "documents"
        report["summary_text"] = (
            f"{action} {exported_count} {document_word} "
            f"to {report.get('output_file', '')}{suffix}"
        )
    return report


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_documents_adapter(adapter or resolve_documents_adapter(repo_root, data_domain, "list_returned"))
    scope = source_model.normalize_scope(adapter.scope)
    staging_root = adapter.path("returned_package_staging_root")
    files = list_staged_import_files(repo_root, scope, staging_root=staging_root)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-import-files",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "scope": scope,
                "count": len(files),
            },
        )
    return {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": scope,
        "staging_root": staging_root.as_posix(),
        "files": files,
    }


def review_returned_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    operation = str(body.get("operation") or "review").strip()
    if operation != "review":
        raise ValueError("operation must be review")
    adapter = require_documents_adapter(adapter or resolve_documents_adapter(repo_root, body.get("data_domain"), "review"))
    scope = source_model.normalize_scope(adapter.scope)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    if not staged_filename:
        raise ValueError("staged_filename is required")

    report = parse_staged_import(
        repo_root=repo_root,
        scope=scope,
        staged_file=staged_filename,
        staging_root=adapter.path("returned_package_staging_root"),
    )
    report = render_markdown_previews(
        repo_root=repo_root,
        scope=scope,
        report=report,
        write=not dry_run,
        preview_root=adapter.path("review_output_root"),
    )
    report["data_domain"] = adapter.data_domain
    report["adapter_id"] = adapter.adapter_id
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-import-preview",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "scope": scope,
                "staged_filename": staged_filename,
                "dry_run": dry_run,
                "preview_written": bool(report.get("preview_written")),
                "detected_import_type": str(report.get("detected_import_type") or ""),
                "records": int(report.get("counts", {}).get("records") or 0),
                "parsed_records": int(report.get("counts", {}).get("parsed_records") or 0),
                "malformed_records": int(report.get("counts", {}).get("malformed_records") or 0),
                "errors": int(report.get("counts", {}).get("errors") or 0),
                "warnings": int(report.get("counts", {}).get("warnings") or 0),
                "preview_files": [
                    str(item.get("path") or "")
                    for item in report.get("preview_files", [])
                    if isinstance(item, dict) and item.get("path")
                ],
            },
        )
    if report.get("ok"):
        action = "Validated" if dry_run else "Generated"
        suffix = " without writing" if dry_run else ""
        preview_count = len(report.get("preview_files", []))
        preview_file_label = "preview file" if preview_count == 1 else "preview files"
        report["summary_text"] = (
            f"{action} {preview_count} {adapter.label} import {preview_file_label}{suffix}."
        )
    return report


def selected_record_indices(value: Any) -> list[int]:
    if not isinstance(value, list):
        raise ValueError("record_indices must be a list")
    selected: list[int] = []
    seen: set[int] = set()
    for item in value:
        if isinstance(item, bool):
            raise ValueError("record_indices must contain integers")
        try:
            index = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError("record_indices must contain integers") from exc
        if index < 0:
            raise ValueError("record_indices must contain zero or positive integers")
        if index not in seen:
            selected.append(index)
            seen.add(index)
    return selected


def summary_from_record(record: Dict[str, Any]) -> tuple[str, bool]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if "summary" not in metadata:
        return "", False
    return normalize_summary(metadata.get("summary")), True


def imported_parent_id(record: Dict[str, Any]) -> str:
    return str(record.get("parent_id") or "").strip()


def selected_records(
    report: Dict[str, Any],
    selected_indices: list[int],
) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], list[tuple[int, Dict[str, Any], str]]]:
    records_by_index = {
        int(record.get("record_index")): record
        for record in report.get("records", [])
        if isinstance(record, dict) and isinstance(record.get("record_index"), int)
    }
    selected_rows: list[Dict[str, Any]] = []
    skipped: list[Dict[str, Any]] = []
    selected: list[tuple[int, Dict[str, Any], str]] = []
    seen_doc_ids: set[str] = set()

    for record_index in selected_indices:
        record = records_by_index.get(record_index)
        if not record:
            skipped.append({"record_index": record_index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        doc_id = str(record.get("doc_id") or "").strip()
        selected_rows.append({"record_index": record_index, "doc_id": doc_id})
        if not doc_id:
            skipped.append({"record_index": record_index, "reason": "missing_doc_id", "message": "selected record has no doc_id"})
            continue
        if doc_id in seen_doc_ids:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "duplicate_doc_id", "message": "selected doc_id was already planned"})
            continue
        seen_doc_ids.add(doc_id)
        selected.append((record_index, record, doc_id))

    return selected_rows, skipped, selected


def apply_summary_updates(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: AdapterResolution,
    dependencies: DocumentsDataSharingDependencies,
) -> Dict[str, Any]:
    scope = source_model.normalize_scope(adapter.scope)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    if not staged_filename:
        raise ValueError("staged_filename is required")
    selected_indices = selected_record_indices(body.get("record_indices", []))
    if not selected_indices:
        raise ValueError("record_indices must include at least one selected record")
    confirmed = bool(body.get("confirm"))

    report = parse_staged_import(
        repo_root=repo_root,
        scope=scope,
        staged_file=staged_filename,
        staging_root=adapter.path("returned_package_staging_root"),
    )
    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    selected_rows, skipped, selected = selected_records(report, selected_indices)
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    updates: list[Dict[str, Any]] = []
    rewrite_docs: list[source_model.ScopeDoc] = []
    rewritten_sources: dict[str, str] = {}

    for record_index, record, doc_id in selected:
        target = docs_by_id.get(doc_id)
        if target is None:
            errors.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_target_doc", "message": f"target Library source doc does not exist: {doc_id}"})
            continue
        summary, has_summary = summary_from_record(record)
        if not has_summary or not summary:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_summary", "message": "selected record has no proposed summary"})
            continue
        current_summary = normalize_summary(target.front_matter.get("summary"))
        if summary == current_summary:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "unchanged", "message": "proposed summary matches current source summary"})
            continue

        timestamp = source_model.current_doc_timestamp()
        updated_front_matter = dict(target.front_matter)
        updated_front_matter["added_date"] = str(
            updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or timestamp
        ).strip()
        updated_front_matter["last_updated"] = timestamp
        updated_front_matter["summary"] = summary
        rewritten_sources[doc_id] = source_model.format_source(updated_front_matter, target.body)
        rewrite_docs.append(target)
        updates.append(
            {
                "record_index": record_index,
                "doc_id": doc_id,
                "path": relative_path(repo_root, target.path),
                "from_summary": current_summary,
                "to_summary": summary,
            }
        )

    warning_count = len(warnings) + len(skipped)
    error_count = len(errors)
    ok = bool(report.get("ok")) and error_count == 0
    backup_dir = None
    rebuild = None
    if ok and confirmed and updates and not dry_run:
        backup_dir = dependencies.make_backup_bundle(
            repo_root,
            scope,
            "documents-summary-apply",
            rewrite_docs,
            {
                "staged_filename": staged_filename,
                "record_indices": selected_indices,
                "updated_doc_ids": [item["doc_id"] for item in updates],
            },
        )
        rebuild = dependencies.perform_source_write_and_rebuild(
            repo_root,
            scope,
            [doc.path for doc in rewrite_docs],
            lambda: [source_model.write_text_atomic(doc.path, rewritten_sources[doc.doc_id]) for doc in rewrite_docs],
            suppression_reason="docs-import-summary-apply",
            search_doc_ids=[item["doc_id"] for item in updates],
        )

    payload: Dict[str, Any] = {
        "ok": ok,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": scope,
        "staged_filename": staged_filename,
        "operation": "summary_apply",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "input_ok": bool(report.get("ok")),
        "detected_import_type": report.get("detected_import_type", ""),
        "selected_records": selected_rows,
        "updates": updates,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "selected": len(selected_indices),
            "updates": len(updates),
            "skipped": len(skipped),
            "errors": error_count,
            "warnings": warning_count,
        },
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "summary_apply_written": bool(ok and confirmed and updates and not dry_run),
        "requires_confirmation": bool(ok and updates and not confirmed),
    }
    action = "Validated" if not confirmed or dry_run else "Updated"
    suffix = " without writing" if not confirmed or dry_run else ""
    payload["summary_text"] = f"{action} {len(updates)} {adapter.label} summary update(s){suffix}."
    dependencies.log_event(
        repo_root,
        "docs-import-summary-apply",
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "staged_filename": staged_filename,
            "dry_run": dry_run,
            "confirmed": confirmed,
            "updates": len(updates),
            "skipped": len(skipped),
            "errors": error_count,
            "written": bool(payload["summary_apply_written"]),
        },
    )
    return payload


def apply_hierarchy_updates(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: AdapterResolution,
    dependencies: DocumentsDataSharingDependencies,
) -> Dict[str, Any]:
    scope = source_model.normalize_scope(adapter.scope)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    if not staged_filename:
        raise ValueError("staged_filename is required")
    selected_indices = selected_record_indices(body.get("record_indices", []))
    if not selected_indices:
        raise ValueError("record_indices must include at least one selected record")
    confirmed = bool(body.get("confirm"))

    report = parse_staged_import(
        repo_root=repo_root,
        scope=scope,
        staged_file=staged_filename,
        staging_root=adapter.path("returned_package_staging_root"),
    )
    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    selected_rows, skipped, selected = selected_records(report, selected_indices)
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    updates: list[Dict[str, Any]] = []
    unchanged: list[Dict[str, Any]] = []
    rewrite_docs: list[source_model.ScopeDoc] = []
    rewritten_sources: dict[str, str] = {}

    for record_index, record, doc_id in selected:
        target = docs_by_id.get(doc_id)
        if target is None:
            errors.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_target_doc", "message": f"target Library source doc does not exist: {doc_id}"})
            continue
        parent_id = imported_parent_id(record)
        if parent_id == doc_id:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "self_parent_id", "message": "selected record parent_id points to itself"})
            continue
        if parent_id and parent_id not in docs_by_id:
            warnings.append({"record_index": record_index, "doc_id": doc_id, "parent_id": parent_id, "reason": "unknown_parent_id", "message": f"parent_id is not a current Library source doc and will render at root level: {parent_id}"})
        if parent_id == target.parent_id:
            unchanged.append({"record_index": record_index, "doc_id": doc_id, "parent_id": parent_id, "message": "proposed parent_id matches current source parent_id"})
            continue

        timestamp = source_model.current_doc_timestamp()
        updated_front_matter = dict(target.front_matter)
        updated_front_matter["added_date"] = str(
            updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or timestamp
        ).strip()
        updated_front_matter["last_updated"] = timestamp
        updated_front_matter["parent_id"] = parent_id
        rewritten_sources[doc_id] = source_model.format_source(updated_front_matter, target.body)
        rewrite_docs.append(target)
        updates.append(
            {
                "record_index": record_index,
                "doc_id": doc_id,
                "path": relative_path(repo_root, target.path),
                "from_parent_id": target.parent_id,
                "to_parent_id": parent_id,
                "sort_order": target.sort_order,
            }
        )

    warning_count = len(warnings) + len(skipped)
    error_count = len(errors)
    ok = bool(report.get("ok")) and error_count == 0
    backup_dir = None
    rebuild = None
    if ok and confirmed and updates and not dry_run:
        backup_dir = dependencies.make_backup_bundle(
            repo_root,
            scope,
            "documents-hierarchy-apply",
            rewrite_docs,
            {
                "staged_filename": staged_filename,
                "record_indices": selected_indices,
                "updated_doc_ids": [item["doc_id"] for item in updates],
            },
        )
        rebuild = dependencies.perform_source_write_and_rebuild(
            repo_root,
            scope,
            [doc.path for doc in rewrite_docs],
            lambda: [source_model.write_text_atomic(doc.path, rewritten_sources[doc.doc_id]) for doc in rewrite_docs],
            suppression_reason="docs-import-hierarchy-apply",
            search_doc_ids=[item["doc_id"] for item in updates],
        )

    payload: Dict[str, Any] = {
        "ok": ok,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": scope,
        "staged_filename": staged_filename,
        "operation": "hierarchy_apply",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "input_ok": bool(report.get("ok")),
        "detected_import_type": report.get("detected_import_type", ""),
        "selected_records": selected_rows,
        "updates": updates,
        "unchanged": unchanged,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "selected": len(selected_indices),
            "changed": len(updates),
            "updates": len(updates),
            "unchanged": len(unchanged),
            "skipped": len(skipped),
            "errors": error_count,
            "warnings": warning_count,
        },
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "hierarchy_apply_written": bool(ok and confirmed and updates and not dry_run),
        "requires_confirmation": bool(ok and updates and not confirmed),
    }
    action = "Validated" if not confirmed or dry_run else "Updated"
    suffix = " without writing" if not confirmed or dry_run else ""
    payload["summary_text"] = f"{action} {len(updates)} {adapter.label} hierarchy change(s){suffix}."
    dependencies.log_event(
        repo_root,
        "docs-import-hierarchy-apply",
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "staged_filename": staged_filename,
            "dry_run": dry_run,
            "confirmed": confirmed,
            "changed": len(updates),
            "unchanged": len(unchanged),
            "skipped": len(skipped),
            "warnings": len(warnings),
            "errors": error_count,
            "written": bool(payload["hierarchy_apply_written"]),
        },
    )
    return payload


def apply_returned_changes(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    operation = str(body.get("operation") or "").strip()
    if operation != "apply":
        raise ValueError("operation must be apply")
    apply_action = str(body.get("apply_action") or "").strip()
    if apply_action not in {"summary_apply", "hierarchy_apply"}:
        raise ValueError("apply_action must be summary_apply or hierarchy_apply")
    if dependencies is None:
        raise ValueError("documents apply requires service dependencies")
    adapter = require_documents_adapter(adapter or resolve_documents_adapter(repo_root, body.get("data_domain"), operation))
    if apply_action == "summary_apply":
        return apply_summary_updates(repo_root, body, dry_run, adapter, dependencies)
    return apply_hierarchy_updates(repo_root, body, dry_run, adapter, dependencies)


def handlers_for(
    dependencies_factory: Callable[[], DocumentsDataSharingDependencies],
) -> data_sharing_service.DataSharingAdapterHandlers:
    def prepare_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return prepare_package(repo_root, body, dry_run, adapter, dependencies_factory())

    def list_handler(repo_root: Path, data_domain: Any, adapter: AdapterResolution) -> Dict[str, Any]:
        return list_returned_packages(repo_root, data_domain, adapter, dependencies_factory())

    def review_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return review_returned_package(repo_root, body, dry_run, adapter, dependencies_factory())

    def apply_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return apply_returned_changes(repo_root, body, dry_run, adapter, dependencies_factory())

    return data_sharing_service.DataSharingAdapterHandlers(
        module="documents",
        prepare=prepare_handler,
        list_returned=list_handler,
        review=review_handler,
        apply=apply_handler,
    )
