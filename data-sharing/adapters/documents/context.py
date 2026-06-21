#!/usr/bin/env python3
"""Shared context helpers for the Documents Data Sharing adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Callable, Dict

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        _docs_services_root = _candidate / "docs-viewer" / "services"
        _data_sharing_root = _candidate / "data-sharing"
        for _path in (_docs_services_root, _data_sharing_root):
            if str(_path) not in sys.path:
                sys.path.insert(0, str(_path))
        break

from docs_data_sharing.write import (  # noqa: E402
    DocsDataSharingWriteDependencies,
    PerformSourceWriteAndRebuild,
)
import docs_source_model as source_model  # noqa: E402


LogEvent = Callable[[Path, str, Dict[str, Any]], None]


@dataclass(frozen=True)
class DocumentsDataSharingDependencies:
    log_event: LogEvent
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild

    def write_dependencies(self) -> DocsDataSharingWriteDependencies:
        return DocsDataSharingWriteDependencies(
            perform_source_write_and_rebuild=self.perform_source_write_and_rebuild,
        )


def require_documents_adapter(adapter: Any) -> Any:
    if adapter is None:
        raise ValueError("documents adapter resolution is required")
    if str(adapter.adapter.get("module") or "").strip() != "documents":
        raise ValueError(f"adapter {adapter.adapter_id!r} is not implemented by the documents service")
    return adapter


def selection_model(adapter: Any) -> str:
    return str(adapter.capability.get("selection_model") or adapter.domain.get("selection_model") or "").strip()


def attach_adapter_context(report: Dict[str, Any], adapter: Any) -> Dict[str, Any]:
    report["data_domain"] = adapter.data_domain
    report["adapter_id"] = adapter.adapter_id
    return report


def default_docs_scope() -> str:
    scopes = list(source_model.SCOPE_ROOTS.keys())
    if not scopes:
        raise ValueError("no Docs Viewer scopes are configured")
    return scopes[0]


def normalize_docs_scope(value: Any, *, required: bool = True) -> str:
    raw = str(value or "").strip()
    if not raw:
        if required:
            raise ValueError("selection.docs_scope is required")
        raw = default_docs_scope()
    return source_model.normalize_scope(raw)


def resolve_docs_scope(adapter: Any, value: Any = "", *, required: bool = True) -> str:
    raw = str(value or "").strip()
    if not raw:
        raw = str(adapter.domain.get("scope") or adapter.domain.get("docs_scope") or "").strip()
    return normalize_docs_scope(raw, required=required)


def request_selection(body: Dict[str, Any]) -> Dict[str, Any]:
    selection = body.get("selection")
    if not isinstance(selection, dict):
        raise ValueError("selection is required")
    return selection
