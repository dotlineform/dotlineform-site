#!/usr/bin/env python3
"""Config-driven dispatch for Studio Data Sharing adapters."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


REGISTRY_REL_PATH = Path("data-sharing/config/adapters.json")
SCHEMA_VERSION = "data_sharing_adapters_v2"
CANONICAL_OPERATIONS = {"prepare", "list_returned", "review", "apply"}
STATUS_VALUES = {"active", "planned", "stub", "disabled"}
RUNTIME_ARTIFACT_ROOT = Path("var/studio/data-sharing")
RUNTIME_PATH_KEYS = {
    "outbound_package_root": "exports",
    "returned_package_staging_root": "import-staging",
    "review_output_root": "import-preview",
}


def normalize_id(value: Any) -> str:
    return str(value or "").strip().lower()


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def safe_relative_path(value: Any, *, field: str) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"adapter config field {field} is required")
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"adapter config field {field} must be a safe relative path")
    return path


def _require_object(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"adapter config field {field} must be an object")
    return value


def _require_array(value: Any, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"adapter config field {field} must be an array")
    return value


def _require_id(value: Any, *, field: str) -> str:
    normalized = normalize_id(value)
    if not normalized:
        raise ValueError(f"adapter config field {field} is required")
    return normalized


def _validate_status(value: Any, *, field: str, default: str = "active") -> str:
    status = normalize_id(value or default)
    if status not in STATUS_VALUES:
        raise ValueError(f"adapter config field {field} must be one of {', '.join(sorted(STATUS_VALUES))}")
    return status


def _validate_path_collection(value: Any, *, field: str) -> None:
    if isinstance(value, str):
        safe_relative_path(value, field=field)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            safe_relative_path(item, field=f"{field}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_path_collection(item, field=f"{field}.{key}")
        return
    raise ValueError(f"adapter config field {field} must be a string, array, or object of paths")


def _validate_optional_path_object(value: Any, *, field: str) -> dict[str, Any]:
    payload = _require_object(value, field=field)
    _validate_path_collection(payload, field=field)
    return payload


def _validate_runtime_artifact_roots(paths: dict[str, Any], *, data_domain: str, field: str) -> None:
    domain_root = RUNTIME_ARTIFACT_ROOT / data_domain
    for key, leaf in RUNTIME_PATH_KEYS.items():
        actual = safe_relative_path(paths.get(key), field=f"{field}.{key}")
        expected = domain_root / leaf
        if actual != expected:
            raise ValueError(
                f"adapter config field {field}.{key} must be {expected.as_posix()}"
            )


@dataclass(frozen=True)
class AdapterResolution:
    data_domain: str
    operation: str
    adapter_id: str
    adapter: dict[str, Any]
    domain: dict[str, Any]
    capability: dict[str, Any]

    @property
    def label(self) -> str:
        return str(self.domain.get("label") or self.data_domain.title())

    @property
    def scope(self) -> str:
        return normalize_id(self.domain.get("scope") or self.data_domain)

    def path(self, key: str) -> Path:
        paths = self.domain.get("paths") if isinstance(self.domain.get("paths"), dict) else {}
        return safe_relative_path(paths.get(key), field=f"paths.{key}")

    def config_path(self, key: str) -> Path:
        config = self.domain.get("config") if isinstance(self.domain.get("config"), dict) else {}
        return safe_relative_path(config.get(key), field=f"config.{key}")


def adapter_status(adapter: dict[str, Any]) -> str:
    return normalize_id(adapter.get("status") or "active")


def domain_status(adapter: dict[str, Any], domain: dict[str, Any]) -> str:
    return normalize_id(domain.get("status") or adapter_status(adapter) or "active")


def capability_records(adapter: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in adapter.get("capabilities", []):
        if not isinstance(item, dict):
            continue
        operation = normalize_id(item.get("operation"))
        if not operation:
            continue
        record = dict(item)
        record["operation"] = operation
        record["status"] = normalize_id(item.get("status") or "active")
        record["message"] = str(item.get("message") or "").strip()
        records.append(record)
    return records


def validate_registry(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Data Sharing adapter registry schema_version must be {SCHEMA_VERSION}")

    dispatch = _require_array(payload.get("dispatch"), field="dispatch")
    adapters = _require_array(payload.get("adapters"), field="adapters")

    adapter_index: dict[str, dict[str, Any]] = {}
    for index, adapter in enumerate(adapters):
        adapter = _require_object(adapter, field=f"adapters[{index}]")
        adapter_id = _require_id(adapter.get("id"), field=f"adapters[{index}].id")
        if adapter_id in adapter_index:
            raise ValueError(f"Data Sharing adapter registry defines adapter {adapter_id!r} more than once")
        adapter_index[adapter_id] = adapter
        _require_id(adapter.get("module"), field=f"adapters[{index}].module")
        _require_id(adapter.get("label"), field=f"adapters[{index}].label")
        _validate_status(adapter.get("status"), field=f"adapters[{index}].status")
        portability = _require_object(adapter.get("portability"), field=f"adapters[{index}].portability")
        _require_id(portability.get("package"), field=f"adapters[{index}].portability.package")

        data_domains = _require_object(adapter.get("data_domains"), field=f"adapters[{index}].data_domains")
        if not data_domains:
            raise ValueError(f"adapter {adapter_id!r} must declare at least one data_domain")
        for data_domain, domain in data_domains.items():
            domain_id = _require_id(data_domain, field=f"adapters[{index}].data_domains key")
            domain = _require_object(domain, field=f"adapters[{index}].data_domains.{domain_id}")
            _require_id(domain.get("label"), field=f"adapters[{index}].data_domains.{domain_id}.label")
            _require_id(domain.get("scope"), field=f"adapters[{index}].data_domains.{domain_id}.scope")
            _validate_status(domain.get("status"), field=f"adapters[{index}].data_domains.{domain_id}.status")
            selection_model = _require_id(
                domain.get("selection_model"),
                field=f"adapters[{index}].data_domains.{domain_id}.selection_model",
            )
            if selection_model not in {"documents", "records", "file_only", "none"}:
                raise ValueError(
                    f"adapter config field adapters[{index}].data_domains.{domain_id}.selection_model is unsupported"
                )
            paths = _validate_optional_path_object(domain.get("paths"), field=f"adapters[{index}].data_domains.{domain_id}.paths")
            _validate_runtime_artifact_roots(
                paths,
                data_domain=domain_id,
                field=f"adapters[{index}].data_domains.{domain_id}.paths",
            )
            _validate_optional_path_object(
                domain.get("source_write_targets", {}),
                field=f"adapters[{index}].data_domains.{domain_id}.source_write_targets",
            )
            _validate_optional_path_object(domain.get("sources", {}), field=f"adapters[{index}].data_domains.{domain_id}.sources")
            _validate_optional_path_object(domain.get("config", {}), field=f"adapters[{index}].data_domains.{domain_id}.config")

        capabilities = _require_array(adapter.get("capabilities"), field=f"adapters[{index}].capabilities")
        if not capabilities:
            raise ValueError(f"adapter {adapter_id!r} must declare at least one capability")
        seen_capabilities: set[str] = set()
        for cap_index, capability in enumerate(capabilities):
            capability = _require_object(capability, field=f"adapters[{index}].capabilities[{cap_index}]")
            operation = _require_id(capability.get("operation"), field=f"adapters[{index}].capabilities[{cap_index}].operation")
            if operation not in CANONICAL_OPERATIONS:
                raise ValueError(f"adapter {adapter_id!r} capability {operation!r} is not a canonical Data Sharing operation")
            if operation in seen_capabilities:
                raise ValueError(f"adapter {adapter_id!r} declares {operation} capability more than once")
            seen_capabilities.add(operation)
            _validate_status(capability.get("status"), field=f"adapters[{index}].capabilities[{cap_index}].status")
            _require_id(
                capability.get("selection_model"),
                field=f"adapters[{index}].capabilities[{cap_index}].selection_model",
            )
            if operation == "apply":
                apply_actions = _require_array(
                    capability.get("apply_actions"),
                    field=f"adapters[{index}].capabilities[{cap_index}].apply_actions",
                )
                seen_actions: set[str] = set()
                for action_index, action in enumerate(apply_actions):
                    action = _require_object(
                        action,
                        field=f"adapters[{index}].capabilities[{cap_index}].apply_actions[{action_index}]",
                    )
                    action_id = _require_id(
                        action.get("id"),
                        field=f"adapters[{index}].capabilities[{cap_index}].apply_actions[{action_index}].id",
                    )
                    if action_id in seen_actions:
                        raise ValueError(f"adapter {adapter_id!r} declares apply action {action_id!r} more than once")
                    seen_actions.add(action_id)
                    _validate_status(
                        action.get("status"),
                        field=f"adapters[{index}].capabilities[{cap_index}].apply_actions[{action_index}].status",
                    )

    seen_dispatch: set[tuple[str, str]] = set()
    for index, item in enumerate(dispatch):
        item = _require_object(item, field=f"dispatch[{index}]")
        data_domain = _require_id(item.get("data_domain"), field=f"dispatch[{index}].data_domain")
        operation = _require_id(item.get("operation"), field=f"dispatch[{index}].operation")
        if operation not in CANONICAL_OPERATIONS:
            raise ValueError(f"Data Sharing dispatch operation {operation!r} is not canonical")
        key = (data_domain, operation)
        if key in seen_dispatch:
            raise ValueError(f"multiple Data Sharing adapters configured for {data_domain}/{operation}")
        seen_dispatch.add(key)
        adapter_id = _require_id(item.get("adapter_id"), field=f"dispatch[{index}].adapter_id")
        adapter = adapter_index.get(adapter_id)
        if adapter is None:
            raise ValueError(f"adapter {adapter_id!r} is not defined exactly once")
        data_domains = adapter.get("data_domains") if isinstance(adapter.get("data_domains"), dict) else {}
        if data_domain not in data_domains:
            raise ValueError(f"adapter {adapter_id!r} has no configuration for data_domain {data_domain!r}")
        if operation not in {item.get("operation") for item in capability_records(adapter)}:
            raise ValueError(f"adapter {adapter_id!r} does not declare {operation} capability")


def load_registry(repo_root: Path, config_path: str | Path | None = None) -> dict[str, Any]:
    path = repo_root / (Path(config_path) if config_path else REGISTRY_REL_PATH)
    payload = read_json_object(path, "Data Sharing adapter registry")
    validate_registry(payload)
    return payload


def resolve_adapter(
    repo_root: Path,
    *,
    data_domain: Any,
    operation: Any,
    config_path: str | Path | None = None,
    require_active: bool = True,
) -> AdapterResolution:
    resolved_data_domain = normalize_id(data_domain)
    resolved_operation = normalize_id(operation)
    if not resolved_data_domain:
        raise ValueError("data_domain is required")
    if not resolved_operation:
        raise ValueError("operation is required")
    if resolved_operation not in CANONICAL_OPERATIONS:
        raise ValueError(f"operation must be one of {', '.join(sorted(CANONICAL_OPERATIONS))}")

    registry = load_registry(repo_root, config_path)
    matches = [
        item
        for item in registry["dispatch"]
        if isinstance(item, dict)
        and normalize_id(item.get("data_domain")) == resolved_data_domain
        and normalize_id(item.get("operation")) == resolved_operation
    ]
    if not matches:
        raise ValueError(f"no Data Sharing adapter configured for {resolved_data_domain}/{resolved_operation}")

    adapter_id = normalize_id(matches[0].get("adapter_id"))
    adapters = [
        item
        for item in registry["adapters"]
        if isinstance(item, dict) and normalize_id(item.get("id")) == adapter_id
    ]
    if len(adapters) != 1:
        raise ValueError(f"adapter {adapter_id!r} is not defined exactly once")
    adapter = adapters[0]
    capabilities = [
        item
        for item in capability_records(adapter)
        if normalize_id(item.get("operation")) == resolved_operation
    ]
    if not capabilities:
        raise ValueError(f"adapter {adapter_id!r} does not declare {resolved_operation} capability")
    if len(capabilities) > 1:
        raise ValueError(f"adapter {adapter_id!r} declares {resolved_operation} capability more than once")
    capability = capabilities[0]
    data_domains = adapter.get("data_domains") if isinstance(adapter.get("data_domains"), dict) else {}
    domain = data_domains.get(resolved_data_domain)
    if not isinstance(domain, dict):
        raise ValueError(f"adapter {adapter_id!r} has no configuration for data_domain {resolved_data_domain!r}")
    resolved_adapter_status = adapter_status(adapter)
    resolved_domain_status = domain_status(adapter, domain)
    resolved_capability_status = normalize_id(capability.get("status") or resolved_domain_status or resolved_adapter_status or "active")
    if not require_active:
        return AdapterResolution(
            data_domain=resolved_data_domain,
            operation=resolved_operation,
            adapter_id=adapter_id,
            adapter=adapter,
            domain=domain,
            capability=capability,
        )

    if resolved_adapter_status != "active":
        raise ValueError(f"adapter {adapter_id!r} is {resolved_adapter_status} and has no implemented service")
    if resolved_domain_status != "active":
        raise ValueError(f"adapter {adapter_id!r} data_domain {resolved_data_domain!r} is {resolved_domain_status}")
    if resolved_capability_status != "active":
        message = str(capability.get("message") or "").strip()
        detail = f": {message}" if message else ""
        raise ValueError(
            f"adapter {adapter_id!r} capability {resolved_operation!r} is {resolved_capability_status}{detail}"
        )

    return AdapterResolution(
        data_domain=resolved_data_domain,
        operation=resolved_operation,
        adapter_id=adapter_id,
        adapter=adapter,
        domain=domain,
        capability=capability,
    )
