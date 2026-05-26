"""Operation dispatch contracts for Data Sharing workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


CANONICAL_OPERATIONS = ("prepare", "list_returned", "review", "apply")

AdapterResolver = Callable[[Path, Any, str], Any]
SelectableRecordsHandler = Callable[[Path, Any, Any], dict[str, Any]]
PrepareHandler = Callable[[Path, dict[str, Any], bool, Any], dict[str, Any]]
ListReturnedHandler = Callable[[Path, Any, Any], dict[str, Any]]
ReviewHandler = Callable[[Path, dict[str, Any], bool, Any], dict[str, Any]]
ApplyHandler = Callable[[Path, dict[str, Any], bool, Any], dict[str, Any]]


@dataclass(frozen=True)
class DataSharingAdapterHandlers:
    module: str
    selectable_records: SelectableRecordsHandler | None = None
    prepare: PrepareHandler | None = None
    list_returned: ListReturnedHandler | None = None
    review: ReviewHandler | None = None
    apply: ApplyHandler | None = None


def adapter_module(adapter: Any) -> str:
    adapter_payload = getattr(adapter, "adapter", {})
    if not isinstance(adapter_payload, dict):
        return ""
    return str(adapter_payload.get("module") or "").strip()


def adapter_id(adapter: Any) -> str:
    return str(getattr(adapter, "adapter_id", "") or "").strip()


def handler_for(
    handlers: dict[str, DataSharingAdapterHandlers],
    adapter: Any,
    operation: str,
) -> Callable[..., dict[str, Any]]:
    module = adapter_module(adapter)
    adapter_handlers = handlers.get(module)
    if adapter_handlers is None:
        raise ValueError(f"adapter {adapter_id(adapter)!r} module {module!r} has no registered Data Sharing service")
    handler = getattr(adapter_handlers, operation, None)
    if handler is None:
        raise ValueError(f"adapter {adapter_id(adapter)!r} does not implement Data Sharing {operation}")
    return handler


def resolve_for_workflow(
    repo_root: Path,
    data_domain: Any,
    operation: str,
    resolve_adapter: AdapterResolver,
) -> Any:
    if operation not in CANONICAL_OPERATIONS:
        raise ValueError(f"unknown Data Sharing operation: {operation}")
    return resolve_adapter(repo_root, data_domain, operation)


def selectable_records(
    repo_root: Path,
    data_domain: Any,
    handlers: dict[str, DataSharingAdapterHandlers],
    resolve_adapter: AdapterResolver,
) -> dict[str, Any]:
    adapter = resolve_for_workflow(repo_root, data_domain, "prepare", resolve_adapter)
    handler = handler_for(handlers, adapter, "selectable_records")
    return handler(repo_root, data_domain, adapter)


def prepare_package(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
    resolve_adapter: AdapterResolver,
) -> dict[str, Any]:
    adapter = resolve_for_workflow(repo_root, body.get("data_domain"), "prepare", resolve_adapter)
    handler = handler_for(handlers, adapter, "prepare")
    return handler(repo_root, body, dry_run, adapter)


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    handlers: dict[str, DataSharingAdapterHandlers],
    resolve_adapter: AdapterResolver,
) -> dict[str, Any]:
    adapter = resolve_for_workflow(repo_root, data_domain, "list_returned", resolve_adapter)
    handler = handler_for(handlers, adapter, "list_returned")
    return handler(repo_root, data_domain, adapter)


def review_returned_package(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
    resolve_adapter: AdapterResolver,
) -> dict[str, Any]:
    operation = str(body.get("operation") or "review").strip()
    if operation != "review":
        raise ValueError("operation must be review")
    adapter = resolve_for_workflow(repo_root, body.get("data_domain"), "review", resolve_adapter)
    handler = handler_for(handlers, adapter, "review")
    return handler(repo_root, body, dry_run, adapter)


def apply_returned_changes(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
    resolve_adapter: AdapterResolver,
) -> dict[str, Any]:
    operation = str(body.get("operation") or "").strip()
    if operation != "apply":
        raise ValueError("operation must be apply")
    adapter = resolve_for_workflow(repo_root, body.get("data_domain"), "apply", resolve_adapter)
    handler = handler_for(handlers, adapter, "apply")
    return handler(repo_root, body, dry_run, adapter)


__all__ = [
    "ApplyHandler",
    "AdapterResolver",
    "CANONICAL_OPERATIONS",
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
    "resolve_for_workflow",
    "review_returned_package",
    "selectable_records",
]
