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
    capabilities = {
        normalize_id(item)
        for item in adapter.get("capabilities", [])
        if normalize_id(item)
    }
    if resolved_operation not in capabilities:
        raise ValueError(f"adapter {adapter_id!r} does not declare {resolved_operation} capability")
    data_domains = adapter.get("data_domains") if isinstance(adapter.get("data_domains"), dict) else {}
    domain = data_domains.get(resolved_data_domain)
    if not isinstance(domain, dict):
        raise ValueError(f"adapter {adapter_id!r} has no configuration for data_domain {resolved_data_domain!r}")

    return AdapterResolution(
        data_domain=resolved_data_domain,
        operation=resolved_operation,
        adapter_id=adapter_id,
        adapter=adapter,
        domain=domain,
    )
