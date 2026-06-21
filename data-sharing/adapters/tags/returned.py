#!/usr/bin/env python3
"""Returned package parsing for Analytics tags Data Sharing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from data_sharing_adapters import AdapterResolution

from .context import normalize_text, read_json_file, read_jsonl_file, resolve_staged_path


@dataclass(frozen=True)
class ReturnedPackage:
    family: str
    mode: str
    import_payload: Dict[str, Any]
    source_payload: Any
    filename: str
    input_format: str


def normalize_mode(value: Any) -> str:
    mode = str(value or "merge").strip().lower()
    if mode not in {"add", "merge", "replace"}:
        raise ValueError("mode must be one of: add, merge, replace")
    return mode


def load_returned_package(repo_root: Path, adapter: AdapterResolution, staged_filename: str) -> ReturnedPackage:
    path = resolve_staged_path(repo_root, adapter, staged_filename)
    if not path.exists():
        raise FileNotFoundError(f"staged file not found: {path.name}")
    input_format = path.suffix.lower().lstrip(".")
    source_payload = read_jsonl_file(path) if input_format == "jsonl" else read_json_file(path)

    if isinstance(source_payload, dict):
        mode = normalize_mode(source_payload.get("mode") or source_payload.get("import_mode"))
        if isinstance(source_payload.get("import_registry"), dict):
            return ReturnedPackage("registry", mode, dict(source_payload["import_registry"]), source_payload, path.name, input_format)
        if isinstance(source_payload.get("import_aliases"), dict):
            return ReturnedPackage("aliases", mode, dict(source_payload["import_aliases"]), source_payload, path.name, input_format)
        if isinstance(source_payload.get("import_assignments"), dict):
            return ReturnedPackage("assignments", "", dict(source_payload["import_assignments"]), source_payload, path.name, input_format)
        if isinstance(source_payload.get("tags"), list):
            return ReturnedPackage("registry", mode, {"tags": source_payload["tags"]}, source_payload, path.name, input_format)
        if isinstance(source_payload.get("aliases"), dict):
            return ReturnedPackage("aliases", mode, {"aliases": source_payload["aliases"]}, source_payload, path.name, input_format)
        if isinstance(source_payload.get("series"), dict):
            return ReturnedPackage("assignments", "", {"series": source_payload["series"]}, source_payload, path.name, input_format)

    if isinstance(source_payload, list):
        records = [item for item in source_payload if isinstance(item, dict)]
        if records and all("tag_id" in item for item in records):
            return ReturnedPackage("registry", "merge", {"tags": records}, source_payload, path.name, input_format)

    raise ValueError("returned package must include import_registry, import_aliases, import_assignments, tags, aliases, or series")
