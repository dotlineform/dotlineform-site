#!/usr/bin/env python3
"""Documents adapter for Studio Data Sharing workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Callable, Dict, Optional

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

ensure_studio_python_paths(__file__)

from docs_data_sharing_apply import (  # noqa: E402
    DocumentsApplyIdentity,
    apply_hierarchy_updates,
    apply_summary_updates,
)
from docs_data_sharing_package import (  # noqa: E402
    build_document_package,
    list_returned_document_packages,
    selectable_document_records,
)
from docs_data_sharing_review import review_returned_document_package  # noqa: E402
from docs_data_sharing_write import (  # noqa: E402
    DocsDataSharingWriteDependencies,
    MakeBackupBundle,
    PerformSourceWriteAndRebuild,
)
import docs_source_model as source_model  # noqa: E402
from studio.data_sharing_adapters import AdapterResolution  # noqa: E402
from studio import data_sharing_service  # noqa: E402


LogEvent = Callable[[Path, str, Dict[str, Any]], None]


@dataclass(frozen=True)
class DocumentsDataSharingDependencies:
    log_event: LogEvent
    make_backup_bundle: MakeBackupBundle
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild

    def write_dependencies(self) -> DocsDataSharingWriteDependencies:
        return DocsDataSharingWriteDependencies(
            make_backup_bundle=self.make_backup_bundle,
            perform_source_write_and_rebuild=self.perform_source_write_and_rebuild,
        )


def resolve_documents_adapter(repo_root: Path, data_domain: Any, operation: str) -> AdapterResolution:
    adapter = data_sharing_service.resolve_for_service(repo_root, data_domain, operation)
    return require_documents_adapter(adapter)


def require_documents_adapter(adapter: AdapterResolution) -> AdapterResolution:
    if str(adapter.adapter.get("module") or "").strip() != "documents":
        raise ValueError(f"adapter {adapter.adapter_id!r} is not implemented by the documents service")
    return adapter


def selection_model(adapter: AdapterResolution) -> str:
    return str(adapter.capability.get("selection_model") or adapter.domain.get("selection_model") or "").strip()


def attach_adapter_context(report: Dict[str, Any], adapter: AdapterResolution) -> Dict[str, Any]:
    report["data_domain"] = adapter.data_domain
    report["adapter_id"] = adapter.adapter_id
    return report


def selectable_records(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    del dependencies
    adapter = require_documents_adapter(adapter or resolve_documents_adapter(repo_root, data_domain, "prepare"))
    report = selectable_document_records(
        repo_root,
        scope=adapter.scope,
        selection_model=selection_model(adapter),
    )
    return attach_adapter_context(report, adapter)


def prepare_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_documents_adapter(adapter or resolve_documents_adapter(repo_root, body.get("data_domain"), "prepare"))
    config_id = str(body.get("config_id") or "").strip()
    target_format = str(body.get("target_format") or "").strip()
    report = build_document_package(
        repo_root,
        scope=adapter.scope,
        config_id=config_id,
        raw_doc_ids=body.get("doc_ids", []),
        select_all=bool(body.get("select_all")),
        missing_summary_only=body.get("missing_summary_only"),
        dry_run=dry_run,
        config_path=adapter.config_path("sharing_profiles_path").as_posix(),
        target_format=target_format,
        output_root=adapter.path("outbound_package_root"),
    )
    report = attach_adapter_context(report, adapter)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-export",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "scope": report.get("scope", source_model.normalize_scope(adapter.scope)),
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
    report = list_returned_document_packages(
        repo_root,
        scope=adapter.scope,
        staging_root=adapter.path("returned_package_staging_root"),
    )
    report = attach_adapter_context(report, adapter)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "docs-import-files",
            {
                "data_domain": adapter.data_domain,
                "adapter_id": adapter.adapter_id,
                "scope": report.get("scope", source_model.normalize_scope(adapter.scope)),
                "count": len(report.get("files", [])),
            },
        )
    return report


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
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    report = review_returned_document_package(
        repo_root,
        scope=adapter.scope,
        staged_filename=staged_filename,
        dry_run=dry_run,
        staging_root=adapter.path("returned_package_staging_root"),
        preview_root=adapter.path("review_output_root"),
    )
    report = attach_adapter_context(report, adapter)
    scope = source_model.normalize_scope(adapter.scope)
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
    scope = source_model.normalize_scope(adapter.scope)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    confirmed = bool(body.get("confirm"))
    identity = DocumentsApplyIdentity(
        data_domain=adapter.data_domain,
        adapter_id=adapter.adapter_id,
        adapter_label=adapter.label,
    )
    common_args = {
        "scope": scope,
        "staged_filename": staged_filename,
        "record_indices": body.get("record_indices", []),
        "confirmed": confirmed,
        "dry_run": dry_run,
        "staging_root": adapter.path("returned_package_staging_root"),
        "identity": identity,
        "dependencies": dependencies.write_dependencies(),
    }
    if apply_action == "summary_apply":
        payload = apply_summary_updates(repo_root, **common_args)
        log_event_name = "docs-import-summary-apply"
        log_details = {
            "updates": len(payload.get("updates", [])),
            "skipped": len(payload.get("skipped", [])),
            "errors": int(payload.get("counts", {}).get("errors") or 0),
            "written": bool(payload.get("summary_apply_written")),
        }
    else:
        payload = apply_hierarchy_updates(repo_root, **common_args)
        log_event_name = "docs-import-hierarchy-apply"
        log_details = {
            "changed": len(payload.get("updates", [])),
            "unchanged": len(payload.get("unchanged", [])),
            "skipped": len(payload.get("skipped", [])),
            "warnings": len(payload.get("warnings", [])),
            "errors": int(payload.get("counts", {}).get("errors") or 0),
            "written": bool(payload.get("hierarchy_apply_written")),
        }

    dependencies.log_event(
        repo_root,
        log_event_name,
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "staged_filename": staged_filename,
            "dry_run": dry_run,
            "confirmed": confirmed,
            **log_details,
        },
    )
    return payload


def handlers_for(
    dependencies_factory: Callable[[], DocumentsDataSharingDependencies],
) -> data_sharing_service.DataSharingAdapterHandlers:
    def selectable_records_handler(repo_root: Path, data_domain: Any, adapter: AdapterResolution) -> Dict[str, Any]:
        return selectable_records(repo_root, data_domain, adapter, dependencies_factory())

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
        selectable_records=selectable_records_handler,
        prepare=prepare_handler,
        list_returned=list_handler,
        review=review_handler,
        apply=apply_handler,
    )
