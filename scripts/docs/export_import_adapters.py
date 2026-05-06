#!/usr/bin/env python3
"""Config-driven dispatch for Studio export/import adapters."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


REGISTRY_REL_PATH = Path("assets/studio/data/export_import_adapters.json")
SCHEMA_VERSION = "export_import_adapters_v1"


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
        if isinstance(item, str):
            operation = normalize_id(item)
            if operation:
                records.append({"operation": operation, "status": "active"})
            continue
        if not isinstance(item, dict):
            continue
        operation = normalize_id(item.get("operation"))
        if not operation:
            continue
        records.append(
            {
                "operation": operation,
                "status": normalize_id(item.get("status") or "active"),
                "message": str(item.get("message") or "").strip(),
            }
        )
    return records


def load_registry(repo_root: Path, config_path: str | Path | None = None) -> dict[str, Any]:
    path = repo_root / (Path(config_path) if config_path else REGISTRY_REL_PATH)
    payload = read_json_object(path, "export/import adapter registry")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"export/import adapter registry schema_version must be {SCHEMA_VERSION}")
    if not isinstance(payload.get("dispatch"), list):
        raise ValueError("export/import adapter registry dispatch must be an array")
    if not isinstance(payload.get("adapters"), list):
        raise ValueError("export/import adapter registry adapters must be an array")
    return payload


def resolve_adapter(
    repo_root: Path,
    *,
    data_domain: Any,
    operation: Any,
    config_path: str | Path | None = None,
) -> AdapterResolution:
    resolved_data_domain = normalize_id(data_domain)
    resolved_operation = normalize_id(operation)
    if not resolved_data_domain:
        raise ValueError("data_domain is required")
    if not resolved_operation:
        raise ValueError("operation is required")

    registry = load_registry(repo_root, config_path)
    matches = [
        item
        for item in registry["dispatch"]
        if isinstance(item, dict)
        and normalize_id(item.get("data_domain")) == resolved_data_domain
        and normalize_id(item.get("operation")) == resolved_operation
    ]
    if not matches:
        raise ValueError(f"no export/import adapter configured for {resolved_data_domain}/{resolved_operation}")
    if len(matches) > 1:
        raise ValueError(f"multiple export/import adapters configured for {resolved_data_domain}/{resolved_operation}")

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
