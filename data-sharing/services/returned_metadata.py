"""Resolve returned-package staging files through internal export metadata."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from services.paths import configured_workspace_paths, marker_path

SUPPORTED_EXTENSIONS = {".json", ".jsonl"}
EXPORT_ID_RE = re.compile(r"^ds_\d{8}T\d{6}Z$")


def modified_utc(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def parse_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("expected JSON object")
    return payload


def export_id_from_jsonl_header(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("first JSONL row must be a header object")
            if payload.get("record_type") != "data_sharing_header":
                raise ValueError("first JSONL row is missing data_sharing_header record_type")
            return normalize_text(payload.get("export_id"))
    raise ValueError("JSONL file is empty")


def export_id_from_staged_file(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".jsonl":
        export_id = export_id_from_jsonl_header(path)
    elif extension == ".json":
        export_id = normalize_text(parse_json_object(path).get("export_id"))
    else:
        raise ValueError(f"unsupported extension: {extension or '<none>'}")
    if not export_id:
        raise ValueError("staged file is missing export_id")
    if not EXPORT_ID_RE.fullmatch(export_id):
        raise ValueError(f"invalid export_id: {export_id}")
    return export_id


def load_export_metadata(export_id: str, *, metadata_root: Path) -> tuple[dict[str, Any], Path]:
    metadata_path = metadata_root / f"{export_id}.meta.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata file not found for export_id {export_id}")
    metadata = parse_json_object(metadata_path)
    metadata_export_id = normalize_text(metadata.get("export_id"))
    if metadata_export_id != export_id:
        raise ValueError(f"metadata export_id {metadata_export_id or '<missing>'} does not match {export_id}")
    return metadata, metadata_path


def supports_return_import(metadata: dict[str, Any]) -> bool:
    return metadata.get("supports_return_import") is not False


def staged_file_record(path: Path, *, metadata_root: Path, workspace_root: Path) -> dict[str, Any]:
    stat = path.stat()
    record: dict[str, Any] = {
        "filename": path.name,
        "path": marker_path(path, workspace_root=workspace_root),
        "format": path.suffix.lower().lstrip("."),
        "size_bytes": stat.st_size,
        "modified_utc": modified_utc(path),
        "metadata_ok": False,
    }
    try:
        export_id = export_id_from_staged_file(path)
        metadata, metadata_path = load_export_metadata(export_id, metadata_root=metadata_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        record["metadata_error"] = str(exc)
        return record

    required_fields = ["app", "data_domain"]
    missing_fields = [field for field in required_fields if not normalize_text(metadata.get(field))]
    if missing_fields:
        record.update(
            {
                "export_id": export_id,
                "metadata_file": marker_path(metadata_path, workspace_root=workspace_root),
                "metadata_error": f"metadata missing required fields: {', '.join(missing_fields)}",
            }
        )
        return record

    record.update(
        {
            "metadata_ok": True,
            "metadata_file": marker_path(metadata_path, workspace_root=workspace_root),
            "export_id": export_id,
            "app": normalize_text(metadata.get("app")),
            "data_domain": normalize_text(metadata.get("data_domain")),
            "adapter_id": normalize_text(metadata.get("adapter_id")),
            "config_id": normalize_text(metadata.get("config_id")),
            "profile_id": normalize_text(metadata.get("profile_id")),
            "scope": normalize_text(metadata.get("scope")),
            "target_format": normalize_text(metadata.get("target_format")),
            "record_shape": normalize_text(metadata.get("record_shape")),
            "supports_return_import": supports_return_import(metadata),
        }
    )
    return record


def list_staged_files_with_metadata(
    repo_root: Path,
    staging_root: Path | str | None = None,
    metadata_root: Path | str | None = None,
) -> dict[str, Any]:
    defaults = configured_workspace_paths(repo_root)
    resolved_staging_root = (Path(staging_root) if staging_root else defaults.import_staging).resolve()
    resolved_metadata_root = (Path(metadata_root) if metadata_root else defaults.meta).resolve()
    files: list[dict[str, Any]] = []
    blocked_files: list[dict[str, Any]] = []
    if resolved_staging_root.exists():
        for path in sorted(resolved_staging_root.iterdir()):
            if path.name.endswith(".context.json") or path.name.endswith(".meta.json"):
                continue
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            record = staged_file_record(
                path,
                metadata_root=resolved_metadata_root,
                workspace_root=defaults.root,
            )
            if record.get("metadata_ok") and record.get("supports_return_import") is False:
                record["return_import_supported"] = False
                record["blocked_reason"] = "export_only_profile"
                blocked_files.append(record)
                continue
            files.append(record)
    return {
        "ok": True,
        "staging_root": marker_path(resolved_staging_root, workspace_root=defaults.root),
        "meta_root": marker_path(resolved_metadata_root, workspace_root=defaults.root),
        "files": files,
        "blocked_files": blocked_files,
    }


__all__ = [
    "EXPORT_ID_RE",
    "export_id_from_staged_file",
    "list_staged_files_with_metadata",
    "load_export_metadata",
    "supports_return_import",
]
