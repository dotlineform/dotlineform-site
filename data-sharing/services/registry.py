"""Registry and config path contracts for Data Sharing adapters."""

from __future__ import annotations

from pathlib import Path


CONFIG_ROOT = Path("data-sharing/config")
ADAPTER_REGISTRY_REL_PATH = CONFIG_ROOT / "adapters.json"
ADAPTER_REGISTRY_SCHEMA_REL_PATH = CONFIG_ROOT / "adapters.schema.json"
DOCUMENTS_PREPARE_PROFILES_REL_PATH = Path("data-sharing/adapters/documents/config/prepare-profiles.json")

__all__ = [
    "ADAPTER_REGISTRY_REL_PATH",
    "ADAPTER_REGISTRY_SCHEMA_REL_PATH",
    "CONFIG_ROOT",
    "DOCUMENTS_PREPARE_PROFILES_REL_PATH",
]
