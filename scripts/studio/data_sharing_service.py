#!/usr/bin/env python3
"""Shared Studio Data Sharing service gateway."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from studio.data_sharing_adapters import AdapterResolution, resolve_adapter


PrepareHandler = Callable[[Path, dict[str, Any], bool, AdapterResolution], dict[str, Any]]
ListReturnedHandler = Callable[[Path, Any, AdapterResolution], dict[str, Any]]
ReviewHandler = Callable[[Path, dict[str, Any], bool, AdapterResolution], dict[str, Any]]
ApplyHandler = Callable[[Path, dict[str, Any], bool, AdapterResolution], dict[str, Any]]


@dataclass(frozen=True)
class DataSharingAdapterHandlers:
    module: str
    prepare: PrepareHandler | None = None
    list_returned: ListReturnedHandler | None = None
    review: ReviewHandler | None = None
    apply: ApplyHandler | None = None


def adapter_module(adapter: AdapterResolution) -> str:
    return str(adapter.adapter.get("module") or "").strip()


def handler_for(
    handlers: dict[str, DataSharingAdapterHandlers],
    adapter: AdapterResolution,
    operation: str,
) -> Callable[..., dict[str, Any]]:
    module = adapter_module(adapter)
    adapter_handlers = handlers.get(module)
    if adapter_handlers is None:
        raise ValueError(f"adapter {adapter.adapter_id!r} module {module!r} has no registered Data Sharing service")
    handler = getattr(adapter_handlers, operation, None)
    if handler is None:
        raise ValueError(f"adapter {adapter.adapter_id!r} does not implement Data Sharing {operation}")
    return handler


def resolve_for_service(repo_root: Path, data_domain: Any, operation: str) -> AdapterResolution:
    return resolve_adapter(repo_root, data_domain=data_domain, operation=operation)


def prepare_package(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    adapter = resolve_for_service(repo_root, body.get("data_domain"), "prepare")
    handler = handler_for(handlers, adapter, "prepare")
    return handler(repo_root, body, dry_run, adapter)


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    adapter = resolve_for_service(repo_root, data_domain, "list_returned")
    handler = handler_for(handlers, adapter, "list_returned")
    return handler(repo_root, data_domain, adapter)


def review_returned_package(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    operation = str(body.get("operation") or "review").strip()
    if operation != "review":
        raise ValueError("operation must be review")
    adapter = resolve_for_service(repo_root, body.get("data_domain"), "review")
    handler = handler_for(handlers, adapter, "review")
    return handler(repo_root, body, dry_run, adapter)


def apply_returned_changes(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
) -> dict[str, Any]:
    operation = str(body.get("operation") or "").strip()
    if operation != "apply":
        raise ValueError("operation must be apply")
    adapter = resolve_for_service(repo_root, body.get("data_domain"), "apply")
    handler = handler_for(handlers, adapter, "apply")
    return handler(repo_root, body, dry_run, adapter)
