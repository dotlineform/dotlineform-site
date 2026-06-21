#!/usr/bin/env python3
"""Analytics gateway for Data Sharing workflow dispatch."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        _data_sharing_root = _candidate / "data-sharing"
        if str(_data_sharing_root) not in sys.path:
            sys.path.insert(0, str(_data_sharing_root))
        break

from services.dispatch import (  # noqa: E402
    ApplyHandler,
    DataSharingAdapterHandlers,
    ListReturnedHandler,
    PrepareHandler,
    ReviewHandler,
    SelectableRecordsHandler,
    adapter_module,
    handler_for,
)
from services.dispatch import selectable_records as dispatch_selectable_records  # noqa: E402
from workflows.apply import apply_returned_changes as dispatch_apply_returned_changes  # noqa: E402
from workflows.list_returned import list_returned_packages as dispatch_list_returned_packages  # noqa: E402
from workflows.prepare import prepare_package as dispatch_prepare_package  # noqa: E402
from workflows.review import review_returned_package as dispatch_review_returned_package  # noqa: E402
try:
    from analytics_app.data_sharing_adapters import AdapterResolution, resolve_adapter  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover - supports direct script imports.
    from data_sharing_adapters import AdapterResolution, resolve_adapter  # type: ignore[no-redef]  # noqa: E402


def resolve_for_service(repo_root: Path, data_domain: Any, operation: str) -> AdapterResolution:
    return resolve_adapter(repo_root, data_domain=data_domain, operation=operation)


def selectable_records(
    repo_root: Path,
    data_domain: Any,
    selectors: dict[str, Any] | None,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    return dispatch_selectable_records(repo_root, data_domain, selectors or {}, handlers, resolve_for_service)


def prepare_package(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    return dispatch_prepare_package(repo_root, body, dry_run, handlers, resolve_for_service)


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    return dispatch_list_returned_packages(repo_root, data_domain, handlers, resolve_for_service)


def review_returned_package(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    return dispatch_review_returned_package(repo_root, body, dry_run, handlers, resolve_for_service)


def apply_returned_changes(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    return dispatch_apply_returned_changes(repo_root, body, dry_run, handlers, resolve_for_service)


__all__ = [
    "AdapterResolution",
    "ApplyHandler",
    "DataSharingAdapterHandlers",
    "ListReturnedHandler",
    "PrepareHandler",
    "ReviewHandler",
    "SelectableRecordsHandler",
    "adapter_module",
    "apply_returned_changes",
    "handler_for",
    "list_returned_packages",
    "prepare_package",
    "resolve_for_service",
    "selectable_records",
]
