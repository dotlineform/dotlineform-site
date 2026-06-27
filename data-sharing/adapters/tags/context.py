#!/usr/bin/env python3
"""Shared context helpers for the Analytics tags Data Sharing adapter."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import json
from pathlib import Path
import sys
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        _data_sharing_root = _candidate / "data-sharing"
        for _path in (_candidate, _data_sharing_root):
            if str(_path) not in sys.path:
                sys.path.insert(0, str(_path))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
ANALYTICS_APP_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server" / "analytics_app"
if str(ANALYTICS_APP_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYTICS_APP_SERVER_DIR))

from tag_services import tag_source_model
from data_sharing_adapters import AdapterResolution, safe_relative_path
from studio_activity import append_studio_activity, normalize_activity_context_from_contract, studio_activity_entry


LogEvent = Callable[[Path, str, Dict[str, Any]], None]

SUPPORTED_EXTENSIONS = {".json", ".jsonl"}
TAG_WRITE_SOURCE_REFS = [{"kind": "log", "path": "var/analytics/logs/analytics_data_sharing_api.log"}]
SUPPORTED_PREPARE_FORMATS = {"json"}
PREPARE_ACTIVITY_ENDPOINT = "/data-sharing/prepare"
APPLY_ACTIVITY_ENDPOINT = "/data-sharing/apply"
TAG_PREPARE_PROFILES: Dict[str, Dict[str, Any]] = {
    "tag-registry": {"family": "registry", "label": "Tag registry"},
    "tag-aliases": {"family": "aliases", "label": "Tag aliases"},
    "tag-assignments": {"family": "assignments", "label": "Tag assignments"},
    "tags-bundle": {"family": "bundle", "label": "Combined tags bundle"},
}


@dataclass(frozen=True)
class TagsDataSharingDependencies:
    log_event: LogEvent


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def relative_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def require_tags_adapter(adapter: Optional[AdapterResolution]) -> AdapterResolution:
    if adapter is None:
        raise ValueError("tags adapter resolution is required")
    if str(adapter.adapter.get("module") or "").strip() != "analytics.tags":
        raise ValueError(f"adapter {adapter.adapter_id!r} is not implemented by the Analytics tags service")
    return adapter


def adapter_source_path(repo_root: Path, adapter: AdapterResolution, key: str) -> Path:
    targets = adapter.domain.get("source_write_targets") if isinstance(adapter.domain.get("source_write_targets"), dict) else {}
    rel_path = safe_relative_path(targets.get(key), field=f"source_write_targets.{key}")
    return (repo_root / rel_path).resolve()


def resolve_staging_root(repo_root: Path, adapter: AdapterResolution) -> Path:
    return (repo_root / adapter.path("returned_package_staging_root")).resolve()


def resolve_outbound_root(repo_root: Path, adapter: AdapterResolution) -> Path:
    return (repo_root / adapter.path("outbound_package_root")).resolve()


def resolve_outbound_package_path(repo_root: Path, adapter: AdapterResolution, config_id: str, target_format: str) -> Path:
    if not tag_source_model.SLUG_RE.fullmatch(config_id):
        raise ValueError("config_id must be slug-safe")
    if target_format not in SUPPORTED_PREPARE_FORMATS:
        raise ValueError("target_format must be json")
    timestamp = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")
    outbound_root = resolve_outbound_root(repo_root, adapter)
    path = (outbound_root / f"{timestamp}-{config_id}.{target_format}").resolve()
    if path != outbound_root and outbound_root not in path.parents:
        raise ValueError(f"output file must stay under {adapter.path('outbound_package_root')}")
    return path


def resolve_staged_path(repo_root: Path, adapter: AdapterResolution, staged_filename: str) -> Path:
    filename = normalize_text(staged_filename)
    if not filename:
        raise ValueError("staged_filename is required")
    rel_path = Path(filename)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise ValueError("staged_filename must be a safe relative filename")
    path = (resolve_staging_root(repo_root, adapter) / rel_path).resolve()
    allowed_root = resolve_staging_root(repo_root, adapter)
    if path != allowed_root and allowed_root not in path.parents:
        raise ValueError(f"staged file must stay under {adapter.path('returned_package_staging_root')}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("staged file must be JSON or JSONL")
    return path


def read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid returned package JSON: {exc.msg}") from exc


def read_jsonl_file(path: Path) -> list[Any]:
    records: list[Any] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid returned package JSONL on line {line_number}: {exc.msg}") from exc
    return records


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_current_registry(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    return tag_source_model.load_registry(adapter_source_path(repo_root, adapter, "tag_registry"))


def load_current_aliases(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    return tag_source_model.load_aliases(adapter_source_path(repo_root, adapter, "tag_aliases"))


def load_current_assignments(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    return tag_source_model.load_assignments(adapter_source_path(repo_root, adapter, "tag_assignments"))


def load_series_index(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    sources = adapter.domain.get("sources") if isinstance(adapter.domain.get("sources"), dict) else {}
    rel_path = sources.get("series")
    if not rel_path:
        raise ValueError("tags adapter sources.series is required")
    path = (repo_root / safe_relative_path(rel_path, field="sources.series")).resolve()
    return tag_source_model.load_series_index(path)


def load_source_json(repo_root: Path, adapter: AdapterResolution, source_key: str) -> Dict[str, Any]:
    sources = adapter.domain.get("sources") if isinstance(adapter.domain.get("sources"), dict) else {}
    rel_path = sources.get(source_key)
    if not rel_path:
        raise ValueError(f"tags adapter sources.{source_key} is required")
    path = (repo_root / safe_relative_path(rel_path, field=f"sources.{source_key}")).resolve()
    return read_json_file(path) if path.exists() else {}


def load_works_index(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    return load_source_json(repo_root, adapter, "works")


def issue(level: str, code: str, message: str, record_index: int | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"level": level, "code": code, "message": message}
    if record_index is not None:
        payload["record_index"] = record_index
    return payload


def prepare_profiles(adapter: AdapterResolution) -> Dict[str, Dict[str, Any]]:
    profiles = adapter.capability.get("sharing_profiles")
    if not isinstance(profiles, list):
        return dict(TAG_PREPARE_PROFILES)
    out: Dict[str, Dict[str, Any]] = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        profile_id = normalize_text(profile.get("id"))
        family = normalize_text(profile.get("family"))
        if profile_id and family in {"registry", "aliases", "assignments", "bundle"}:
            out[profile_id] = {
                "family": family,
                "label": normalize_text(profile.get("label")) or TAG_PREPARE_PROFILES.get(profile_id, {}).get("label") or profile_id,
                "selection": profile.get("selection") if isinstance(profile.get("selection"), dict) else {},
            }
    return out or dict(TAG_PREPARE_PROFILES)


def source_files(repo_root: Path, adapter: AdapterResolution, family: str) -> Dict[str, str]:
    keys = {
        "registry": ["tag_registry"],
        "aliases": ["tag_aliases"],
        "assignments": ["tag_assignments", "series", "works"],
        "bundle": ["tag_registry", "tag_aliases", "tag_assignments", "series", "works"],
    }.get(family, [])
    sources = adapter.domain.get("sources") if isinstance(adapter.domain.get("sources"), dict) else {}
    targets = adapter.domain.get("source_write_targets") if isinstance(adapter.domain.get("source_write_targets"), dict) else {}
    files: Dict[str, str] = {}
    for key in keys:
        rel_path = sources.get(key) or targets.get(key)
        if rel_path:
            files[key] = safe_relative_path(rel_path, field=f"sources.{key}").as_posix()
    return files


def package_metadata(
    *,
    adapter: AdapterResolution,
    config_id: str,
    family: str,
    generated_at_utc: str,
    source_paths: Dict[str, str],
    counts: Dict[str, int],
) -> Dict[str, Any]:
    return {
        "schema_version": "tags_data_sharing_package_v1",
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "config_id": config_id,
        "package_family": family,
        "generated_at_utc": generated_at_utc,
        "source_paths": source_paths,
        "counts": counts,
        "returned_package_hints": {
            "registry": ["tags"],
            "aliases": ["aliases"],
            "assignments": ["series"],
        },
    }


def selected_record_indices(value: Any) -> list[int]:
    if not isinstance(value, list):
        raise ValueError("record_indices must be a list")
    selected: list[int] = []
    seen: set[int] = set()
    for item in value:
        if isinstance(item, bool):
            raise ValueError("record_indices must contain integers")
        try:
            index = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError("record_indices must contain integers") from exc
        if index < 0:
            raise ValueError("record_indices must contain zero or positive integers")
        if index not in seen:
            selected.append(index)
            seen.add(index)
    return selected


def selected_record_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("record_ids must be a list")
    selected: list[str] = []
    seen: set[str] = set()
    for item in value:
        record_id = normalize_text(item)
        if not record_id:
            raise ValueError("record_ids must contain non-empty strings")
        if record_id not in seen:
            selected.append(record_id)
            seen.add(record_id)
    return selected


def selection_required(selected: list[int]) -> None:
    if not selected:
        raise ValueError("record_indices must include at least one selected record")


def changed_from_stats(stats: Mapping[str, Any], keys: Iterable[str]) -> bool:
    return any(int(stats.get(key) or 0) > 0 for key in keys)


def attach_prepare_activity(
    repo_root: Path,
    body: Mapping[str, Any],
    payload: Dict[str, Any],
    *,
    record_groups: Mapping[str, Any],
    detail_items: list[str],
    status: str,
) -> None:
    raw_context = body.get("activity_context")
    if not raw_context:
        return
    try:
        activity_context = normalize_activity_context_from_contract(
            repo_root,
            raw_context,
            endpoint=PREPARE_ACTIVITY_ENDPOINT,
            record_id=f"{payload.get('data_domain')}:{payload.get('config_id')}",
            record_id_field="export_id",
        )
        if not activity_context:
            return
        payload["activity_context"] = activity_context
        append_studio_activity(
            repo_root,
            studio_activity_entry(
                activity_context,
                script_purpose_id="prepare-share-package",
                now_utc=str(payload.get("updated_at_utc") or utc_now()),
                status=status,
                record_groups=record_groups,
                detail_items=detail_items,
                source_refs=TAG_WRITE_SOURCE_REFS,
            ),
        )
        payload["activity_log"] = {"written_count": 1}
    except Exception as exc:  # noqa: BLE001
        payload["activity_log"] = {"written_count": 0, "error": str(exc)}


def attach_apply_activity(
    repo_root: Path,
    body: Mapping[str, Any],
    payload: Dict[str, Any],
    *,
    record_groups: Mapping[str, Any],
    detail_items: list[str],
    status: str,
) -> None:
    raw_context = body.get("activity_context")
    if not raw_context:
        return
    try:
        activity_context = normalize_activity_context_from_contract(
            repo_root,
            raw_context,
            endpoint=APPLY_ACTIVITY_ENDPOINT,
            record_id=payload.get("staged_filename"),
            record_id_field="staged_filename",
        )
        if not activity_context:
            return
        payload["activity_context"] = activity_context
        append_studio_activity(
            repo_root,
            studio_activity_entry(
                activity_context,
                script_purpose_id="save-tag-data",
                now_utc=str(payload.get("updated_at_utc") or utc_now()),
                status=status,
                record_groups=record_groups,
                detail_items=detail_items,
                source_refs=TAG_WRITE_SOURCE_REFS,
            ),
        )
        payload["activity_log"] = {"written_count": 1}
    except Exception as exc:  # noqa: BLE001
        payload["activity_log"] = {"written_count": 0, "error": str(exc)}
