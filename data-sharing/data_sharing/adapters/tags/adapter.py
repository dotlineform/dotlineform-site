#!/usr/bin/env python3
"""Analytics tags adapter for Data Sharing workflows."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import datetime as dt
import json
from pathlib import Path
import sys
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"
ANALYTICS_APP_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server" / "analytics_app"
if str(ANALYTICS_APP_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYTICS_APP_SERVER_DIR))

from tag_services import tag_alias_mutations, tag_assignment_service, tag_registry_mutations, tag_source_model, tag_write_transactions
from data_sharing_adapters import AdapterResolution, safe_relative_path
from data_sharing.services.dispatch import DataSharingAdapterHandlers
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


@dataclass(frozen=True)
class ReturnedPackage:
    family: str
    mode: str
    import_payload: Dict[str, Any]
    source_payload: Any
    filename: str
    input_format: str


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
    path = (outbound_root / f"{config_id}-{timestamp}.{target_format}").resolve()
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


def load_current_registry(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    return tag_source_model.load_registry(adapter_source_path(repo_root, adapter, "tag_registry"))


def load_current_aliases(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    return tag_source_model.load_aliases(adapter_source_path(repo_root, adapter, "tag_aliases"))


def load_current_assignments(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    return tag_source_model.load_assignments(adapter_source_path(repo_root, adapter, "tag_assignments"))


def load_series_index(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    sources = adapter.domain.get("sources") if isinstance(adapter.domain.get("sources"), dict) else {}
    rel_path = sources.get("series") or tag_source_model.SERIES_INDEX_REL_PATH.as_posix()
    path = (repo_root / safe_relative_path(rel_path, field="sources.series")).resolve()
    if not path.exists() and rel_path == "studio/data/canonical/catalogue/series.json":
        path = (repo_root / tag_source_model.SERIES_INDEX_REL_PATH).resolve()
    return tag_source_model.load_series_index(path)


def load_source_json(repo_root: Path, adapter: AdapterResolution, source_key: str, fallback: Path) -> Dict[str, Any]:
    sources = adapter.domain.get("sources") if isinstance(adapter.domain.get("sources"), dict) else {}
    rel_path = sources.get(source_key) or fallback.as_posix()
    path = (repo_root / safe_relative_path(rel_path, field=f"sources.{source_key}")).resolve()
    return read_json_file(path) if path.exists() else {}


def load_works_index(repo_root: Path, adapter: AdapterResolution) -> Dict[str, Any]:
    return load_source_json(repo_root, adapter, "works", Path("assets/data/works_index.json"))


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
        "scope": adapter.scope,
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


def count_assignment_works(assignments_payload: Mapping[str, Any]) -> int:
    series_obj = assignments_payload.get("series") if isinstance(assignments_payload.get("series"), dict) else {}
    count = 0
    for row in series_obj.values():
        if not isinstance(row, dict):
            continue
        works = row.get("works") if isinstance(row.get("works"), dict) else {}
        count += len(works)
    return count


def tag_ids_from_registry(registry_payload: Mapping[str, Any]) -> list[str]:
    tags = registry_payload.get("tags") if isinstance(registry_payload.get("tags"), list) else []
    return sorted({normalize_text(item.get("tag_id")) for item in tags if isinstance(item, dict) and normalize_text(item.get("tag_id"))})


def alias_keys_from_payload(aliases_payload: Mapping[str, Any]) -> list[str]:
    aliases = aliases_payload.get("aliases") if isinstance(aliases_payload.get("aliases"), dict) else {}
    return sorted(normalize_text(key) for key in aliases.keys() if normalize_text(key))


def series_ids_from_assignments(assignments_payload: Mapping[str, Any]) -> list[str]:
    series = assignments_payload.get("series") if isinstance(assignments_payload.get("series"), dict) else {}
    return sorted(normalize_text(key) for key in series.keys() if normalize_text(key))


def work_ids_from_assignments(assignments_payload: Mapping[str, Any]) -> list[str]:
    series = assignments_payload.get("series") if isinstance(assignments_payload.get("series"), dict) else {}
    work_ids: set[str] = set()
    for row in series.values():
        if not isinstance(row, dict):
            continue
        works = row.get("works") if isinstance(row.get("works"), dict) else {}
        for work_id in works.keys():
            text = normalize_text(work_id)
            if text:
                work_ids.add(text)
    return sorted(work_ids)


def build_registry_package(repo_root: Path, adapter: AdapterResolution, config_id: str, generated_at_utc: str) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    registry = load_current_registry(repo_root, adapter)
    counts = {"tags": len(registry.get("tags", []) if isinstance(registry.get("tags"), list) else [])}
    payload = {
        "package_metadata": package_metadata(
            adapter=adapter,
            config_id=config_id,
            family="registry",
            generated_at_utc=generated_at_utc,
            source_paths=source_files(repo_root, adapter, "registry"),
            counts=counts,
        ),
        "policy": copy.deepcopy(registry.get("policy") if isinstance(registry.get("policy"), dict) else {}),
        "tags": copy.deepcopy(registry.get("tags") if isinstance(registry.get("tags"), list) else []),
    }
    return payload, counts, {"tags": tag_ids_from_registry(registry)}


def build_aliases_package(repo_root: Path, adapter: AdapterResolution, config_id: str, generated_at_utc: str) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    aliases = load_current_aliases(repo_root, adapter)
    aliases_obj = aliases.get("aliases") if isinstance(aliases.get("aliases"), dict) else {}
    tag_ids = sorted(
        {
            normalize_text(tag_id)
            for entry in aliases_obj.values()
            if isinstance(entry, dict)
            for tag_id in (entry.get("tags") if isinstance(entry.get("tags"), list) else [])
            if normalize_text(tag_id)
        }
    )
    counts = {"aliases": len(aliases_obj), "tags": len(tag_ids)}
    payload = {
        "package_metadata": package_metadata(
            adapter=adapter,
            config_id=config_id,
            family="aliases",
            generated_at_utc=generated_at_utc,
            source_paths=source_files(repo_root, adapter, "aliases"),
            counts=counts,
        ),
        "aliases": copy.deepcopy(aliases_obj),
    }
    return payload, counts, {"aliases": alias_keys_from_payload(aliases), "tags": tag_ids}


def build_assignments_package(repo_root: Path, adapter: AdapterResolution, config_id: str, generated_at_utc: str) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    assignments = load_current_assignments(repo_root, adapter)
    series = assignments.get("series") if isinstance(assignments.get("series"), dict) else {}
    series_index = load_series_index(repo_root, adapter)
    works_index = load_works_index(repo_root, adapter)
    counts = {"series": len(series), "works": count_assignment_works(assignments)}
    payload = {
        "package_metadata": package_metadata(
            adapter=adapter,
            config_id=config_id,
            family="assignments",
            generated_at_utc=generated_at_utc,
            source_paths=source_files(repo_root, adapter, "assignments"),
            counts=counts,
        ),
        "series": copy.deepcopy(series),
        "catalogue_context": {
            "series_index_header": copy.deepcopy(series_index.get("header") if isinstance(series_index.get("header"), dict) else {}),
            "works_index_header": copy.deepcopy(works_index.get("header") if isinstance(works_index.get("header"), dict) else {}),
            "series_work_membership": {
                series_id: sorted(work_ids)
                for series_id, work_ids in sorted(tag_source_model.build_series_work_membership(series_index).items())
            },
        },
    }
    return payload, counts, {"series": series_ids_from_assignments(assignments), "works": work_ids_from_assignments(assignments)}


def merge_counts(*items: Mapping[str, int]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            out[key] = out.get(key, 0) + int(value or 0)
    return out


def merge_groups(*items: Mapping[str, list[str]]) -> Dict[str, list[str]]:
    merged: Dict[str, set[str]] = {}
    for groups in items:
        for key, values in groups.items():
            merged.setdefault(key, set()).update(normalize_text(value) for value in values if normalize_text(value))
    return {key: sorted(values) for key, values in merged.items() if values}


def build_bundle_package(repo_root: Path, adapter: AdapterResolution, config_id: str, generated_at_utc: str) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    registry_payload, registry_counts, registry_groups = build_registry_package(repo_root, adapter, config_id, generated_at_utc)
    aliases_payload, aliases_counts, aliases_groups = build_aliases_package(repo_root, adapter, config_id, generated_at_utc)
    assignments_payload, assignments_counts, assignments_groups = build_assignments_package(repo_root, adapter, config_id, generated_at_utc)
    counts = merge_counts(registry_counts, aliases_counts, assignments_counts)
    payload = {
        "package_metadata": package_metadata(
            adapter=adapter,
            config_id=config_id,
            family="bundle",
            generated_at_utc=generated_at_utc,
            source_paths=source_files(repo_root, adapter, "bundle"),
            counts=counts,
        ),
        "families": {
            "registry": {key: value for key, value in registry_payload.items() if key != "package_metadata"},
            "aliases": {key: value for key, value in aliases_payload.items() if key != "package_metadata"},
            "assignments": {key: value for key, value in assignments_payload.items() if key != "package_metadata"},
        },
    }
    return payload, counts, merge_groups(registry_groups, aliases_groups, assignments_groups)


def count_record_total(family: str, counts: Mapping[str, int]) -> int:
    if family == "registry":
        return int(counts.get("tags") or 0)
    if family == "aliases":
        return int(counts.get("aliases") or 0)
    if family == "assignments":
        return int(counts.get("series") or 0)
    return int(counts.get("tags") or 0) + int(counts.get("aliases") or 0) + int(counts.get("series") or 0)


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


def prepare_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_tags_adapter(adapter)
    config_id = normalize_text(body.get("config_id"))
    profiles = prepare_profiles(adapter)
    profile = profiles.get(config_id)
    if profile is None:
        raise ValueError(f"Unknown tags sharing profile: {config_id}")
    family = normalize_text(profile.get("family"))
    target_format = normalize_text(body.get("target_format") or "json").lower()
    if not target_format:
        target_format = "json"
    output_path = resolve_outbound_package_path(repo_root, adapter, config_id, target_format)
    now_utc = utc_now()

    if family == "registry":
        package_payload, family_counts, groups = build_registry_package(repo_root, adapter, config_id, now_utc)
    elif family == "aliases":
        package_payload, family_counts, groups = build_aliases_package(repo_root, adapter, config_id, now_utc)
    elif family == "assignments":
        package_payload, family_counts, groups = build_assignments_package(repo_root, adapter, config_id, now_utc)
    else:
        package_payload, family_counts, groups = build_bundle_package(repo_root, adapter, config_id, now_utc)

    record_total = count_record_total(family, family_counts)
    relative_output = relative_path(repo_root, output_path)
    counts = {
        "selected": record_total,
        "exported": record_total,
        "skipped": 0,
        "failed": 0,
        "truncated": 0,
        **family_counts,
    }
    if not dry_run:
        write_json_file(output_path, package_payload)
    payload: Dict[str, Any] = {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": adapter.scope,
        "config_id": config_id,
        "tag_family": family,
        "target_format": target_format,
        "output_file": relative_output,
        "output_files": [relative_output],
        "counts": counts,
        "count_unit": "record",
        "warnings": [],
        "errors": [],
        "issue_counts": {"errors": 0, "warnings": 0},
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "output_written": not dry_run,
        "summary_text": (
            f"{'Validated' if dry_run else 'Prepared'} {profile['label']} package "
            f"with {record_total} record(s){' without writing' if dry_run else ''}."
        ),
    }
    if not dry_run:
        attach_prepare_activity(
            repo_root,
            body,
            payload,
            record_groups={**groups, "files": [relative_output]},
            detail_items=[
                str(payload["summary_text"]),
                f"Data family: {family}.",
                f"Output file: {relative_output}.",
            ],
            status="completed",
        )
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "tags-data-sharing-prepare",
            {
                "family": family,
                "config_id": config_id,
                "dry_run": dry_run,
                "output_written": bool(payload.get("output_written")),
                "output_file": relative_output,
                "counts": counts,
            },
        )
    return payload


def registry_rows(existing_payload: Dict[str, Any], package: ReturnedPackage) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
    allowed_groups = tag_source_model.extract_allowed_groups(existing_payload)
    tags = tag_source_model.sanitize_import_registry(package.import_payload, allowed_groups)
    current_ids = {
        str(item.get("tag_id") or "").strip().lower()
        for item in existing_payload.get("tags", [])
        if isinstance(item, dict) and str(item.get("tag_id") or "").strip()
    }
    rows: list[Dict[str, Any]] = []
    for index, tag in enumerate(tags):
        tag_id = tag["tag_id"]
        exists = tag_id in current_ids
        if package.mode == "add" and exists:
            meta = "already exists; add mode will skip"
        elif exists:
            meta = "replace existing tag"
        else:
            meta = "add new tag"
        rows.append(
            {
                "id": f"registry:{tag_id}",
                "type": "tag",
                "title": tag_id,
                "meta": meta,
                "record_index": index,
                "selectable": not (package.mode == "add" and exists),
                "record_groups": {"tags": [tag_id]},
                "issues": [],
            }
        )
    return rows, tags


def alias_rows(package: ReturnedPackage) -> tuple[list[Dict[str, Any]], list[tuple[str, Dict[str, Any]]]]:
    order, aliases = tag_source_model.sanitize_import_aliases(package.import_payload)
    rows: list[Dict[str, Any]] = []
    records: list[tuple[str, Dict[str, Any]]] = []
    for index, alias_key in enumerate(order):
        entry = aliases[alias_key]
        tags = [str(item) for item in entry.get("tags", [])]
        records.append((alias_key, entry))
        rows.append(
            {
                "id": f"alias:{alias_key}",
                "type": "alias",
                "title": alias_key,
                "meta": f"{len(tags)} target tag(s)",
                "record_index": index,
                "selectable": True,
                "record_groups": {"aliases": [alias_key], "tags": tags},
                "issues": [],
            }
        )
    return rows, records


def normalize_assignments_import_payload(import_payload: Dict[str, Any], existing_payload: Dict[str, Any]) -> Dict[str, Any]:
    raw_series = import_payload.get("series") if isinstance(import_payload.get("series"), dict) else {}
    current_series = existing_payload.get("series") if isinstance(existing_payload.get("series"), dict) else {}
    out_series: Dict[str, Dict[str, Any]] = {}
    for raw_series_id, raw_entry in raw_series.items():
        series_id = str(raw_series_id or "").strip().lower()
        if not isinstance(raw_entry, dict):
            out_series[series_id] = raw_entry
            continue
        if "staged_row" in raw_entry:
            out_series[series_id] = raw_entry
            continue
        out_series[series_id] = {
            "base_series_updated_at_utc": str((current_series.get(series_id) or {}).get("updated_at_utc") or ""),
            "base_row_snapshot": copy.deepcopy(current_series.get(series_id) or {"tags": []}),
            "staged_row": raw_entry,
            "staged_at_utc": normalize_text(import_payload.get("updated_at_utc")),
        }
    return {
        "version": normalize_text(import_payload.get("version")),
        "updated_at_utc": normalize_text(import_payload.get("updated_at_utc")),
        "series": out_series,
    }


def assignment_rows(
    existing_payload: Dict[str, Any],
    package: ReturnedPackage,
    series_index_payload: Dict[str, Any],
) -> tuple[list[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    import_payload = normalize_assignments_import_payload(package.import_payload, existing_payload)
    session = tag_source_model.sanitize_import_assignments_session(import_payload)
    preview = tag_assignment_service.preview_assignment_import(existing_payload, session, series_index_payload)
    rows: list[Dict[str, Any]] = []
    for index, row in enumerate(preview.get("series", [])):
        if not isinstance(row, dict):
            continue
        series_id = normalize_text(row.get("series_id"))
        status = normalize_text(row.get("status"))
        row_issues: list[Dict[str, Any]] = []
        if status == "conflict":
            row_issues.append(issue("warning", "conflict", "current tag assignments differ from the returned package base row", index))
        if status == "missing":
            row_issues.append(issue("error", "missing_series", "series is not present in the current catalogue index", index))
        invalid_work_ids = [str(item) for item in row.get("invalid_work_ids", []) if str(item)]
        if status == "invalid":
            row_issues.append(issue("error", "invalid_work_ids", f"invalid work ids: {', '.join(invalid_work_ids)}", index))
        staged = session.get("series", {}).get(series_id, {}).get("staged_row", {})
        groups = assignment_record_groups(series_id, staged)
        rows.append(
            {
                "id": f"assignment:{series_id}",
                "type": "tag_assignment",
                "title": series_id,
                "meta": status or "apply",
                "record_index": index,
                "selectable": status == "apply",
                "record_groups": groups,
                "issues": row_issues,
            }
        )
    return rows, session, preview


def assignment_record_groups(series_id: str, staged_row: Any) -> Dict[str, list[str]]:
    groups: Dict[str, list[str]] = {"series": [series_id] if series_id else []}
    tags: list[str] = []
    works: list[str] = []
    row = staged_row if isinstance(staged_row, dict) else {}
    for item in row.get("tags", []) if isinstance(row.get("tags"), list) else []:
        if isinstance(item, dict) and normalize_text(item.get("tag_id")):
            tags.append(normalize_text(item.get("tag_id")))
    works_obj = row.get("works") if isinstance(row.get("works"), dict) else {}
    for work_id, work_row in works_obj.items():
        work_id_text = normalize_text(work_id)
        if work_id_text:
            works.append(work_id_text)
        if isinstance(work_row, dict):
            for item in work_row.get("tags", []) if isinstance(work_row.get("tags"), list) else []:
                if isinstance(item, dict) and normalize_text(item.get("tag_id")):
                    tags.append(normalize_text(item.get("tag_id")))
    if works:
        groups["works"] = sorted(set(works))
    if tags:
        groups["tags"] = sorted(set(tags))
    return groups


def review_returned_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    operation = str(body.get("operation") or "review").strip()
    if operation != "review":
        raise ValueError("operation must be review")
    adapter = require_tags_adapter(adapter)
    staged_filename = normalize_text(body.get("staged_filename") or body.get("file"))
    package = load_returned_package(repo_root, adapter, staged_filename)
    now_utc = utc_now()
    issues: list[Dict[str, Any]] = []

    if package.family == "registry":
        existing = load_current_registry(repo_root, adapter)
        rows, records = registry_rows(existing, package)
        preview_counts = {"records": len(records), "parsed_records": len(records), "malformed_records": 0, "warnings": 0, "errors": 0}
        summary = f"Validated {len(records)} tag registry row(s) in {package.mode} mode without writing."
    elif package.family == "aliases":
        rows, records = alias_rows(package)
        preview_counts = {"records": len(records), "parsed_records": len(records), "malformed_records": 0, "warnings": 0, "errors": 0}
        summary = f"Validated {len(records)} tag alias row(s) in {package.mode} mode without writing."
    else:
        existing = load_current_assignments(repo_root, adapter)
        series_index = load_series_index(repo_root, adapter)
        rows, _session, preview = assignment_rows(existing, package, series_index)
        warnings = int(preview.get("conflict_count") or 0)
        errors = int(preview.get("invalid_count") or 0) + int(preview.get("missing_count") or 0)
        preview_counts = {
            "records": int(preview.get("staged_series_count") or 0),
            "parsed_records": int(preview.get("staged_series_count") or 0),
            "malformed_records": 0,
            "warnings": warnings,
            "errors": errors,
            "applicable": int(preview.get("applicable_count") or 0),
            "conflicts": int(preview.get("conflict_count") or 0),
            "invalid": int(preview.get("invalid_count") or 0),
            "missing": int(preview.get("missing_count") or 0),
        }
        summary = tag_assignment_service.build_assignment_import_preview_summary(preview)
        for row in rows:
            issues.extend(row.get("issues", []))

    payload: Dict[str, Any] = {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": adapter.scope,
        "staged_filename": package.filename,
        "input_format": package.input_format,
        "detected_import_type": f"tags_{package.family}",
        "tag_family": package.family,
        "mode": package.mode,
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "counts": preview_counts,
        "issues": issues,
        "review_rows": rows,
        "summary_text": summary,
    }
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "tags-data-sharing-review",
            {
                "family": package.family,
                "mode": package.mode,
                "staged_filename": package.filename,
                "records": preview_counts.get("records", 0),
                "warnings": preview_counts.get("warnings", 0),
                "errors": preview_counts.get("errors", 0),
            },
        )
    return payload


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


def selection_required(selected: list[int]) -> None:
    if not selected:
        raise ValueError("record_indices must include at least one selected record")


def changed_from_stats(stats: Mapping[str, Any], keys: Iterable[str]) -> bool:
    return any(int(stats.get(key) or 0) > 0 for key in keys)


def selected_registry_payload(records: list[Dict[str, Any]], selected: list[int], mode: str) -> tuple[Dict[str, Any], list[Dict[str, Any]], list[Dict[str, Any]]]:
    by_index = {index: record for index, record in enumerate(records)}
    skipped: list[Dict[str, Any]] = []
    selected_records: list[Dict[str, Any]] = []
    for index in selected:
        record = by_index.get(index)
        if record is None:
            skipped.append({"record_index": index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        selected_records.append(record)
    if mode == "replace" and len(selected_records) != len(records):
        raise ValueError("registry replace mode requires selecting every returned tag row")
    return {"tags": selected_records}, skipped, [{"record_index": index, "tag_id": record["tag_id"]} for index, record in enumerate(records) if index in selected]


def selected_aliases_payload(records: list[tuple[str, Dict[str, Any]]], selected: list[int], mode: str) -> tuple[Dict[str, Any], list[Dict[str, Any]], list[Dict[str, Any]]]:
    by_index = {index: record for index, record in enumerate(records)}
    skipped: list[Dict[str, Any]] = []
    selected_aliases: Dict[str, Dict[str, Any]] = {}
    selected_rows: list[Dict[str, Any]] = []
    for index in selected:
        record = by_index.get(index)
        if record is None:
            skipped.append({"record_index": index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        alias_key, entry = record
        selected_aliases[alias_key] = entry
        selected_rows.append({"record_index": index, "alias": alias_key})
    if mode == "replace" and len(selected_aliases) != len(records):
        raise ValueError("aliases replace mode requires selecting every returned alias row")
    return {"aliases": selected_aliases}, skipped, selected_rows


def selected_assignment_session(
    session: Dict[str, Any],
    preview: Dict[str, Any],
    selected: list[int],
) -> tuple[Dict[str, Any], list[Dict[str, Any]], list[Dict[str, Any]], list[Dict[str, Any]]]:
    preview_rows = [row for row in preview.get("series", []) if isinstance(row, dict)]
    by_index = {index: row for index, row in enumerate(preview_rows)}
    selected_series: Dict[str, Any] = {}
    selected_rows: list[Dict[str, Any]] = []
    skipped: list[Dict[str, Any]] = []
    errors: list[Dict[str, Any]] = []
    for index in selected:
        row = by_index.get(index)
        if row is None:
            skipped.append({"record_index": index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        series_id = normalize_text(row.get("series_id"))
        status = normalize_text(row.get("status"))
        selected_rows.append({"record_index": index, "series_id": series_id})
        if status != "apply":
            errors.append({"record_index": index, "series_id": series_id, "reason": status or "not_applicable", "message": f"selected series is not directly applicable: {status}"})
            continue
        selected_series[series_id] = copy.deepcopy(session.get("series", {}).get(series_id))
    subset = {
        "version": normalize_text(session.get("version")),
        "updated_at_utc": normalize_text(session.get("updated_at_utc")),
        "series": selected_series,
    }
    return subset, skipped, errors, selected_rows


def attach_activity(
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


def apply_registry(
    repo_root: Path,
    adapter: AdapterResolution,
    package: ReturnedPackage,
    body: Dict[str, Any],
    dry_run: bool,
    now_utc: str,
) -> Dict[str, Any]:
    selected = selected_record_indices(body.get("record_indices", []))
    selection_required(selected)
    confirmed = bool(body.get("confirm"))
    existing = load_current_registry(repo_root, adapter)
    rows, records = registry_rows(existing, package)
    subset, skipped, selected_rows = selected_registry_payload(records, selected, package.mode)
    updated_payload, stats = tag_registry_mutations.apply_registry_import(copy.deepcopy(existing), subset, package.mode, now_utc)
    changed = changed_from_stats(stats, ["added", "overwritten", "removed"])
    target_path = adapter_source_path(repo_root, adapter, "tag_registry")
    if confirmed and changed and not dry_run:
        tag_write_transactions.atomic_write_many({target_path: updated_payload})
    summary_text = tag_registry_mutations.build_import_summary_text(stats)
    payload: Dict[str, Any] = {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": adapter.scope,
        "staged_filename": package.filename,
        "operation": "registry_apply",
        "tag_family": "registry",
        "mode": package.mode,
        "confirmed": confirmed,
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "selected_records": selected_rows,
        "skipped": skipped,
        "errors": [],
        "warnings": [],
        "counts": {"selected": len(selected), "changed": int(changed), "skipped": len(skipped), "errors": 0, "warnings": 0, **stats},
        "written": bool(confirmed and changed and not dry_run),
        "requires_confirmation": bool(changed and not confirmed),
        "review_rows": rows,
        "summary_text": f"{'Updated' if confirmed and not dry_run else 'Validated'} tag registry changes: {summary_text}{' without writing' if not confirmed or dry_run else ''}.",
    }
    if payload["written"]:
        attach_activity(
            repo_root,
            body,
            payload,
            record_groups={"tags": [row["tag_id"] for row in selected_rows], "files": [package.filename]},
            detail_items=[payload["summary_text"], f"Mode: {package.mode}; final tags: {stats.get('final_total')}."],
            status="completed",
        )
    return payload


def apply_aliases(
    repo_root: Path,
    adapter: AdapterResolution,
    package: ReturnedPackage,
    body: Dict[str, Any],
    dry_run: bool,
    now_utc: str,
) -> Dict[str, Any]:
    selected = selected_record_indices(body.get("record_indices", []))
    selection_required(selected)
    confirmed = bool(body.get("confirm"))
    existing = load_current_aliases(repo_root, adapter)
    rows, records = alias_rows(package)
    subset, skipped, selected_rows = selected_aliases_payload(records, selected, package.mode)
    updated_payload, stats = tag_alias_mutations.apply_aliases_import(copy.deepcopy(existing), subset, package.mode, now_utc)
    changed = changed_from_stats(stats, ["added", "overwritten", "removed"])
    target_path = adapter_source_path(repo_root, adapter, "tag_aliases")
    if confirmed and changed and not dry_run:
        tag_write_transactions.atomic_write_many({target_path: updated_payload})
    summary_text = tag_registry_mutations.build_import_summary_text(stats, noun="aliases")
    selected_alias_keys = [row["alias"] for row in selected_rows]
    selected_tags = sorted(
        {
            tag_id
            for row in rows
            if row.get("record_index") in selected
            for tag_id in row.get("record_groups", {}).get("tags", [])
        }
    )
    payload: Dict[str, Any] = {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": adapter.scope,
        "staged_filename": package.filename,
        "operation": "aliases_apply",
        "tag_family": "aliases",
        "mode": package.mode,
        "confirmed": confirmed,
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "selected_records": selected_rows,
        "skipped": skipped,
        "errors": [],
        "warnings": [],
        "counts": {"selected": len(selected), "changed": int(changed), "skipped": len(skipped), "errors": 0, "warnings": 0, **stats},
        "written": bool(confirmed and changed and not dry_run),
        "requires_confirmation": bool(changed and not confirmed),
        "review_rows": rows,
        "summary_text": f"{'Updated' if confirmed and not dry_run else 'Validated'} tag alias changes: {summary_text}{' without writing' if not confirmed or dry_run else ''}.",
    }
    if payload["written"]:
        attach_activity(
            repo_root,
            body,
            payload,
            record_groups={"aliases": selected_alias_keys, "tags": selected_tags, "files": [package.filename]},
            detail_items=[payload["summary_text"], f"Mode: {package.mode}; final aliases: {stats.get('final_total')}."],
            status="completed",
        )
    return payload


def apply_assignments(
    repo_root: Path,
    adapter: AdapterResolution,
    package: ReturnedPackage,
    body: Dict[str, Any],
    dry_run: bool,
    now_utc: str,
) -> Dict[str, Any]:
    selected = selected_record_indices(body.get("record_indices", []))
    selection_required(selected)
    confirmed = bool(body.get("confirm"))
    existing = load_current_assignments(repo_root, adapter)
    series_index = load_series_index(repo_root, adapter)
    rows, session, preview = assignment_rows(existing, package, series_index)
    subset, skipped, errors, selected_rows = selected_assignment_session(session, preview, selected)
    subset_preview = tag_assignment_service.preview_assignment_import(existing, subset, series_index)
    updated_payload, apply_stats = tag_assignment_service.apply_assignment_import(
        copy.deepcopy(existing),
        subset,
        subset_preview,
        {},
        now_utc,
    )
    changed = int(apply_stats.get("applied_series") or 0) > 0
    target_path = adapter_source_path(repo_root, adapter, "tag_assignments")
    ok = not errors
    if ok and confirmed and changed and not dry_run:
        tag_write_transactions.atomic_write_many({target_path: updated_payload})
    response_preview = tag_assignment_service.build_assignment_import_preview_response(subset_preview, package.filename, now_utc)
    response_payload = tag_assignment_service.build_assignment_import_apply_response(response_preview, apply_stats)
    groups = selected_assignment_groups(rows, selected)
    payload: Dict[str, Any] = {
        "ok": ok,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": adapter.scope,
        "staged_filename": package.filename,
        "operation": "assignments_apply",
        "tag_family": "assignments",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "selected_records": selected_rows,
        "skipped": skipped,
        "errors": errors,
        "warnings": [],
        "counts": {
            "selected": len(selected),
            "changed": int(changed),
            "skipped": len(skipped) + int(apply_stats.get("skipped_series") or 0),
            "errors": len(errors),
            "warnings": 0,
            **apply_stats,
        },
        "written": bool(ok and confirmed and changed and not dry_run),
        "requires_confirmation": bool(ok and changed and not confirmed),
        "review_rows": rows,
        "summary_text": f"{'Updated' if ok and confirmed and not dry_run else 'Validated'} tag assignment changes: {response_payload.get('summary_text')}{' without writing' if not confirmed or dry_run else ''}.",
    }
    if payload["written"]:
        attach_activity(
            repo_root,
            body,
            payload,
            record_groups={**groups, "files": [package.filename]},
            detail_items=[payload["summary_text"], f"Applied series: {apply_stats.get('applied_series')}; skipped: {apply_stats.get('skipped_series')}."],
            status="completed",
        )
    return payload


def selected_assignment_groups(rows: list[Dict[str, Any]], selected: list[int]) -> Dict[str, list[str]]:
    groups: Dict[str, set[str]] = {"series": set(), "works": set(), "tags": set()}
    selected_set = set(selected)
    for row in rows:
        if row.get("record_index") not in selected_set:
            continue
        record_groups = row.get("record_groups") if isinstance(row.get("record_groups"), dict) else {}
        for key in groups:
            for value in record_groups.get(key, []) if isinstance(record_groups.get(key), list) else []:
                text = normalize_text(value)
                if text:
                    groups[key].add(text)
    return {key: sorted(values) for key, values in groups.items() if values}


def apply_returned_changes(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    operation = str(body.get("operation") or "").strip()
    if operation != "apply":
        raise ValueError("operation must be apply")
    adapter = require_tags_adapter(adapter)
    apply_action = normalize_text(body.get("apply_action"))
    if apply_action not in {"registry_apply", "aliases_apply", "assignments_apply"}:
        raise ValueError("apply_action must be registry_apply, aliases_apply, or assignments_apply")
    staged_filename = normalize_text(body.get("staged_filename") or body.get("file"))
    package = load_returned_package(repo_root, adapter, staged_filename)
    expected_family = {
        "registry_apply": "registry",
        "aliases_apply": "aliases",
        "assignments_apply": "assignments",
    }[apply_action]
    if package.family != expected_family:
        raise ValueError(f"apply_action {apply_action} cannot apply tags {package.family} package")
    now_utc = utc_now()
    if apply_action == "registry_apply":
        payload = apply_registry(repo_root, adapter, package, body, dry_run, now_utc)
    elif apply_action == "aliases_apply":
        payload = apply_aliases(repo_root, adapter, package, body, dry_run, now_utc)
    else:
        payload = apply_assignments(repo_root, adapter, package, body, dry_run, now_utc)
    if dependencies is not None:
        dependencies.log_event(
            repo_root,
            "tags-data-sharing-apply",
            {
                "family": package.family,
                "apply_action": apply_action,
                "staged_filename": package.filename,
                "dry_run": dry_run,
                "confirmed": bool(body.get("confirm")),
                "written": bool(payload.get("written")),
                "counts": payload.get("counts", {}),
            },
        )
    return payload


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[AdapterResolution] = None,
    dependencies: Optional[TagsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    adapter = require_tags_adapter(adapter)
    staging_root = resolve_staging_root(repo_root, adapter)
    files: list[Dict[str, Any]] = []
    if staging_root.exists():
        for path in sorted(staging_root.iterdir()):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            stat = path.stat()
            files.append(
                {
                    "filename": path.name,
                    "path": relative_path(repo_root, path),
                    "format": path.suffix.lower().lstrip("."),
                    "size_bytes": stat.st_size,
                    "modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )
    if dependencies is not None:
        dependencies.log_event(repo_root, "tags-data-sharing-list-returned", {"count": len(files)})
    return {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": adapter.scope,
        "staging_root": relative_path(repo_root, staging_root),
        "files": files,
    }


def handlers_for(
    dependencies_factory: Callable[[], TagsDataSharingDependencies],
) -> DataSharingAdapterHandlers:
    def selectable_records_handler(repo_root: Path, data_domain: Any, adapter: AdapterResolution) -> Dict[str, Any]:
        del repo_root, data_domain
        adapter = require_tags_adapter(adapter)
        return {
            "ok": True,
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": adapter.scope,
            "selection_model": str(adapter.capability.get("selection_model") or adapter.domain.get("selection_model") or "").strip(),
            "records": [],
            "docs": [],
            "source": {
                "kind": "adapter",
                "module": "analytics.tags",
                "source": "profile_only",
                "scope": adapter.scope,
            },
        }

    def list_handler(repo_root: Path, data_domain: Any, adapter: AdapterResolution) -> Dict[str, Any]:
        return list_returned_packages(repo_root, data_domain, adapter, dependencies_factory())

    def review_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return review_returned_package(repo_root, body, dry_run, adapter, dependencies_factory())

    def apply_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return apply_returned_changes(repo_root, body, dry_run, adapter, dependencies_factory())

    def prepare_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return prepare_package(repo_root, body, dry_run, adapter, dependencies_factory())

    return DataSharingAdapterHandlers(
        module="analytics.tags",
        selectable_records=selectable_records_handler,
        prepare=prepare_handler,
        list_returned=list_handler,
        review=review_handler,
        apply=apply_handler,
    )
