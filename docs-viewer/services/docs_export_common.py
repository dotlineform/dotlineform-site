#!/usr/bin/env python3
"""Shared helpers for Docs Viewer data-sharing exports."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


OUTPUT_ROOT = Path("var/analytics/data-sharing")
EXPORT_META_ROOT = Path("var/analytics/data-sharing/meta")
RETURNED_PACKAGE_SCHEMA_VERSION = "data_sharing_returned_package_v1"
TEXT_WHITESPACE_RE = re.compile(r"\s+")
PUNCTUATION_SPACING_RE = re.compile(r"\s+([,.;:!?])")
EXPORT_ID_RE = re.compile(r"^ds_[0-9]{8}T[0-9]{6}Z$")


def normalize_text(value: Any) -> str:
    text = TEXT_WHITESPACE_RE.sub(" ", str(value or "")).strip()
    return PUNCTUATION_SPACING_RE.sub(r"\1", text)


def trim_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and lines[start] == "":
        start += 1
    while end > start and lines[end - 1] == "":
        end -= 1
    return lines[start:end]


def collapse_blank_lines(lines: list[str]) -> list[str]:
    collapsed: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank
    return collapsed


def read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def data_sharing_header_row(export_id: str) -> dict[str, str]:
    return {
        "record_type": "data_sharing_header",
        "schema_version": RETURNED_PACKAGE_SCHEMA_VERSION,
        "export_id": export_id,
    }


def export_id_from_generated_at(generated_at: str) -> str:
    normalized = normalize_text(generated_at)
    match = re.fullmatch(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})Z", normalized)
    if not match:
        raise ValueError(f"generated_at must be UTC YYYY-MM-DDTHH:MM:SSZ: {generated_at}")
    export_id = f"ds_{match.group(1)}{match.group(2)}{match.group(3)}T{match.group(4)}{match.group(5)}{match.group(6)}Z"
    if not EXPORT_ID_RE.fullmatch(export_id):
        raise ValueError(f"generated export_id is invalid: {export_id}")
    return export_id


def package_metadata_path(repo_root: Path, export_id: str) -> Path:
    normalized = normalize_text(export_id)
    if not EXPORT_ID_RE.fullmatch(normalized):
        raise ValueError(f"invalid export_id: {export_id}")
    return repo_root / EXPORT_META_ROOT / f"{normalized}.meta.json"


def package_context_sidecar_path(path: Path) -> Path:
    return path.with_suffix(".context.json")
