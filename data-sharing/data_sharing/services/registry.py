"""Registry and config path contracts for Data Sharing adapters."""

from __future__ import annotations

from pathlib import Path


CONFIG_ROOT = Path("data-sharing/config")
ADAPTER_REGISTRY_REL_PATH = CONFIG_ROOT / "adapters.json"
ADAPTER_REGISTRY_SCHEMA_REL_PATH = CONFIG_ROOT / "adapters.schema.json"
LIBRARY_EXPORT_CONFIG_REL_PATH = CONFIG_ROOT / "library-export-configs.json"
LIBRARY_EXPORT_CONFIG_SCHEMA_REL_PATH = CONFIG_ROOT / "library-export-configs.schema.json"

__all__ = [
    "ADAPTER_REGISTRY_REL_PATH",
    "ADAPTER_REGISTRY_SCHEMA_REL_PATH",
    "CONFIG_ROOT",
    "LIBRARY_EXPORT_CONFIG_REL_PATH",
    "LIBRARY_EXPORT_CONFIG_SCHEMA_REL_PATH",
]
