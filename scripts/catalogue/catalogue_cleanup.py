#!/usr/bin/env python3
"""Catalogue generated-artifact cleanup planning and payload updates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from catalogue import catalogue_activity as activity
from catalogue.catalogue_build_media import CATALOGUE_MEDIA_STAGING_REL_DIR
from catalogue.catalogue_source import load_json_file, normalize_detail_uid_value, normalize_series_ids_value, slug_id
from catalogue.series_ids import normalize_series_id


def canonicalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): canonicalize_for_hash(value[key]) for key in sorted(value.keys(), key=lambda item: str(item))}
    if isinstance(value, list):
        return [canonicalize_for_hash(item) for item in value]
    if isinstance(value, tuple):
        return [canonicalize_for_hash(item) for item in value]
    if isinstance(value, float):
        if value == 0.0:
            return 0
        if value.is_integer():
            return int(value)
        return float(f"{value:.15g}")
    return value


def compute_payload_version(payload: Any) -> str:
    canonical = json.dumps(
        canonicalize_for_hash(payload),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"blake2b-{hashlib.blake2b(canonical, digest_size=16).hexdigest()}"


def finalize_moments_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    moments_map = payload.get("moments")
    if not isinstance(moments_map, dict):
        raise ValueError("moments_index.json must include a moments object")
    schema = str((payload.get("header") or {}).get("schema") or "moments_index_v1")
    payload["header"] = {
        "schema": schema,
        "version": compute_payload_version({"schema": schema, "moments": moments_map}),
        "generated_at_utc": activity.utc_now(),
        "count": len(moments_map),
    }
    return payload


def sorted_object_map(value: Mapping[str, Any]) -> Dict[str, Any]:
    return {str(key): value[key] for key in sorted(value.keys(), key=lambda item: str(item))}


def finalize_object_map_payload(payload: Dict[str, Any], map_key: str, default_schema: str) -> Dict[str, Any]:
    records_map = payload.get(map_key)
    if not isinstance(records_map, dict):
        raise ValueError(f"payload must include a {map_key} object")
    sorted_map = sorted_object_map(records_map)
    schema = str((payload.get("header") or {}).get("schema") or default_schema)
    payload["header"] = {
        "schema": schema,
        "version": compute_payload_version({"schema": schema, map_key: sorted_map}),
        "generated_at_utc": activity.utc_now(),
        "count": len(sorted_map),
    }
    payload[map_key] = sorted_map
    return payload


def finalize_works_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return finalize_object_map_payload(payload, "works", "works_index_v4")


def finalize_series_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return finalize_object_map_payload(payload, "series", "series_index_v2")


def finalize_work_storage_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return finalize_object_map_payload(payload, "works", "work_storage_index_v1")


def work_record_detail_count(payload: Mapping[str, Any]) -> int:
    count = 0
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return count
    for section in sections:
        if not isinstance(section, dict):
            continue
        details = section.get("details")
        if isinstance(details, list):
            count += len(details)
    return count


def finalize_work_record_payload(payload: Dict[str, Any], work_id: str) -> Dict[str, Any]:
    work_record = payload.get("work")
    if not isinstance(work_record, dict):
        raise ValueError("work record payload must include a work object")
    sections = payload.get("sections")
    if not isinstance(sections, list):
        sections = []
        payload["sections"] = sections
    content_html = payload.get("content_html")
    payload["header"] = {
        "schema": str((payload.get("header") or {}).get("schema") or "work_record_v3"),
        "version": compute_payload_version(
            {
                "work": work_record,
                "sections": sections,
                "content_html": content_html,
            }
        ),
        "generated_at_utc": activity.utc_now(),
        "work_id": work_id,
        "count": work_record_detail_count(payload),
    }
    return payload


def finalize_series_record_payload(payload: Dict[str, Any], series_id: str) -> Dict[str, Any]:
    series_record = payload.get("series")
    if not isinstance(series_record, dict):
        raise ValueError("series record payload must include a series object")
    header = payload.get("header") if isinstance(payload.get("header"), dict) else {}
    works = series_record.get("works")
    count = len(works) if isinstance(works, list) else header.get("count")
    if not isinstance(count, int):
        count = 0
    payload["header"] = {
        "schema": str(header.get("schema") or "series_record_v1"),
        "version": compute_payload_version(
            {
                "series": series_record,
                "content_html": payload.get("content_html"),
                "work_count": count,
            }
        ),
        "generated_at_utc": activity.utc_now(),
        "series_id": series_id,
        "count": count,
    }
    return payload


def finalize_recent_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("recent_index.json must include an entries array")
    schema = str((payload.get("header") or {}).get("schema") or "recent_index_v1")
    payload["header"] = {
        "schema": schema,
        "version": compute_payload_version({"schema": schema, "entries": entries}),
        "generated_at_utc": activity.utc_now(),
        "count": len(entries),
    }
    return payload


def collect_matching_paths(root: Path, patterns: Iterable[str]) -> list[Path]:
    collected: list[Path] = []
    seen: set[Path] = set()
    if not root.exists():
        return collected
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            collected.append(path)
    return collected


def unique_existing_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not path.exists() or not path.is_file():
            continue
        seen.add(resolved)
        out.append(path)
    return out


def collect_moment_repo_artifacts(repo_root: Path, moment_id: str) -> list[Path]:
    return unique_existing_paths(
        [
            repo_root / "_moments" / f"{moment_id}.md",
            repo_root / "assets" / "moments" / "index" / f"{moment_id}.json",
        ]
    )


def collect_moment_repo_media_artifacts(repo_root: Path, moment_id: str) -> list[Path]:
    return collect_matching_paths(repo_root / "assets" / "moments" / "img", [f"{moment_id}-thumb-*.*"])


def collect_moment_staged_media_artifacts(repo_root: Path, moment_id: str) -> list[Path]:
    staging_root = repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "moments"
    paths: list[Path] = []
    paths.extend(collect_matching_paths(staging_root / "make_srcset_images", [f"{moment_id}.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "primary", [f"{moment_id}-primary-*.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "thumb", [f"{moment_id}-thumb-*.*"]))
    return paths


def collect_moment_delete_cleanup(repo_root: Path, moment_id: str) -> Dict[str, Any]:
    repo_artifacts = collect_moment_repo_artifacts(repo_root, moment_id)
    repo_media = collect_moment_repo_media_artifacts(repo_root, moment_id)
    staged_media = collect_moment_staged_media_artifacts(repo_root, moment_id)
    delete_paths = unique_existing_paths([*repo_artifacts, *repo_media, *staged_media])
    return {
        "repo_artifacts": repo_artifacts,
        "repo_media": repo_media,
        "staged_media": staged_media,
        "delete_paths": delete_paths,
    }


def collect_work_repo_artifacts(repo_root: Path, work_id: str) -> list[Path]:
    return unique_existing_paths(
        [
            repo_root / "_works" / f"{work_id}.md",
            repo_root / "assets" / "works" / "index" / f"{work_id}.json",
        ]
    )


def collect_work_repo_media_artifacts(repo_root: Path, work_id: str) -> list[Path]:
    return collect_matching_paths(repo_root / "assets" / "works" / "img", [f"{work_id}-thumb-*.*"])


def collect_work_staged_media_artifacts(repo_root: Path, work_id: str) -> list[Path]:
    staging_root = repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "works"
    paths: list[Path] = []
    paths.extend(collect_matching_paths(staging_root / "make_srcset_images", [f"{work_id}.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "primary", [f"{work_id}-primary-*.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "thumb", [f"{work_id}-thumb-*.*"]))
    return paths


def collect_detail_repo_artifacts(repo_root: Path, detail_uid: str) -> list[Path]:
    return unique_existing_paths([repo_root / "_work_details" / f"{detail_uid}.md"])


def collect_detail_repo_media_artifacts(repo_root: Path, detail_uid: str) -> list[Path]:
    return collect_matching_paths(repo_root / "assets" / "work_details" / "img", [f"{detail_uid}-thumb-*.*"])


def collect_detail_staged_media_artifacts(repo_root: Path, detail_uid: str) -> list[Path]:
    staging_root = repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "work_details"
    paths: list[Path] = []
    paths.extend(collect_matching_paths(staging_root / "make_srcset_images", [f"{detail_uid}.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "primary", [f"{detail_uid}-primary-*.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "thumb", [f"{detail_uid}-thumb-*.*"]))
    return paths


def collect_series_repo_artifacts(repo_root: Path, series_id: str) -> list[Path]:
    return unique_existing_paths(
        [
            repo_root / "_series" / f"{series_id}.md",
            repo_root / "assets" / "series" / "index" / f"{series_id}.json",
        ]
    )


def path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def existing_repo_paths(repo_root: Path, rel_paths: Iterable[Path]) -> list[Path]:
    return unique_existing_paths(repo_root / rel_path for rel_path in rel_paths)


def rel_path_for_preview(repo_root: Path, path: Path) -> str:
    return str(path.relative_to(repo_root)) if path_is_under(path, repo_root) else path.name


def collect_catalogue_delete_cleanup(
    repo_root: Path,
    kind: str,
    record_id: str,
    affected: Mapping[str, Any],
) -> Dict[str, Any]:
    repo_artifacts: list[Path] = []
    repo_media: list[Path] = []
    staged_media: list[Path] = []
    public_json_updates: list[Path] = []
    studio_json_updates: list[Path] = []
    rebuild_search = False

    work_ids = [slug_id(value) for value in affected.get("works") or [] if str(value or "").strip()]
    detail_uids = [normalize_detail_uid_value(value) for value in affected.get("work_details") or [] if str(value or "").strip()]
    series_ids = [normalize_series_id(value) for value in affected.get("series") or [] if str(value or "").strip()]

    if kind == "work":
        repo_artifacts.extend(collect_work_repo_artifacts(repo_root, record_id))
        repo_media.extend(collect_work_repo_media_artifacts(repo_root, record_id))
        staged_media.extend(collect_work_staged_media_artifacts(repo_root, record_id))
        for detail_uid in detail_uids:
            repo_artifacts.extend(collect_detail_repo_artifacts(repo_root, detail_uid))
            repo_media.extend(collect_detail_repo_media_artifacts(repo_root, detail_uid))
            staged_media.extend(collect_detail_staged_media_artifacts(repo_root, detail_uid))
        public_json_updates.extend(
            existing_repo_paths(
                repo_root,
                [
                    Path("assets/data/works_index.json"),
                    Path("assets/data/series_index.json"),
                    Path("assets/data/recent_index.json"),
                ],
            )
        )
        public_json_updates.extend(
            existing_repo_paths(repo_root, [Path("assets/series/index") / f"{series_id}.json" for series_id in series_ids])
        )
        studio_json_updates.extend(
            existing_repo_paths(
                repo_root,
                [
                    Path("assets/studio/data/work_storage_index.json"),
                    Path("assets/studio/data/tag_assignments.json"),
                ],
            )
        )
        rebuild_search = True
    elif kind == "work_detail":
        repo_artifacts.extend(collect_detail_repo_artifacts(repo_root, record_id))
        repo_media.extend(collect_detail_repo_media_artifacts(repo_root, record_id))
        staged_media.extend(collect_detail_staged_media_artifacts(repo_root, record_id))
        public_json_updates.extend(existing_repo_paths(repo_root, [Path("assets/works/index") / f"{work_id}.json" for work_id in work_ids]))
    elif kind == "series":
        repo_artifacts.extend(collect_series_repo_artifacts(repo_root, record_id))
        public_json_updates.extend(
            existing_repo_paths(
                repo_root,
                [
                    Path("assets/data/series_index.json"),
                    Path("assets/data/works_index.json"),
                    Path("assets/data/recent_index.json"),
                ],
            )
        )
        public_json_updates.extend(
            existing_repo_paths(repo_root, [Path("assets/works/index") / f"{work_id}.json" for work_id in work_ids])
        )
        studio_json_updates.extend(existing_repo_paths(repo_root, [Path("assets/studio/data/tag_assignments.json")]))
        rebuild_search = True
    else:
        raise ValueError(f"unsupported catalogue cleanup kind: {kind}")

    return {
        "repo_artifacts": unique_existing_paths(repo_artifacts),
        "repo_media": unique_existing_paths(repo_media),
        "staged_media": unique_existing_paths(staged_media),
        "public_json_updates": unique_existing_paths(public_json_updates),
        "studio_json_updates": unique_existing_paths(studio_json_updates),
        "delete_paths": unique_existing_paths([*repo_artifacts, *repo_media, *staged_media]),
        "catalogue_search": rebuild_search,
    }


def ensure_moment_delete_cleanup_scope(repo_root: Path, cleanup: Mapping[str, Any]) -> None:
    roots = [
        repo_root / "_moments",
        repo_root / "assets" / "moments" / "index",
        repo_root / "assets" / "moments" / "img",
        repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "moments",
    ]
    for raw_path in cleanup.get("delete_paths") or []:
        path = Path(raw_path)
        if not any(path_is_under(path, root) for root in roots):
            raise ValueError(f"delete target is outside allowlisted moment cleanup roots: {path.name}")


def ensure_catalogue_delete_cleanup_scope(repo_root: Path, cleanup: Mapping[str, Any]) -> None:
    delete_roots = [
        repo_root / "_works",
        repo_root / "_work_details",
        repo_root / "_series",
        repo_root / "assets" / "works" / "index",
        repo_root / "assets" / "series" / "index",
        repo_root / "assets" / "works" / "img",
        repo_root / "assets" / "work_details" / "img",
        repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "works",
        repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "work_details",
    ]
    update_roots = [
        repo_root / "assets" / "works" / "index",
        repo_root / "assets" / "series" / "index",
    ]
    update_paths = {
        (repo_root / "assets" / "data" / "works_index.json").resolve(),
        (repo_root / "assets" / "data" / "series_index.json").resolve(),
        (repo_root / "assets" / "data" / "recent_index.json").resolve(),
        (repo_root / "assets" / "studio" / "data" / "work_storage_index.json").resolve(),
        (repo_root / "assets" / "studio" / "data" / "tag_assignments.json").resolve(),
    }
    for raw_path in cleanup.get("delete_paths") or []:
        path = Path(raw_path)
        if not any(path_is_under(path, root) for root in delete_roots):
            raise ValueError(f"delete target is outside allowlisted catalogue cleanup roots: {path.name}")
    for key in ("public_json_updates", "studio_json_updates"):
        for raw_path in cleanup.get(key) or []:
            path = Path(raw_path)
            if path.resolve() in update_paths:
                continue
            if not any(path_is_under(path, root) for root in update_roots):
                raise ValueError(f"update target is outside allowlisted catalogue cleanup roots: {path.name}")


def catalogue_delete_preview_cleanup(
    repo_root: Path,
    kind: str,
    record_id: str,
    affected: Mapping[str, Any],
) -> Dict[str, Any]:
    cleanup = collect_catalogue_delete_cleanup(repo_root, kind, record_id, affected)
    return {
        "repo_artifacts": len(cleanup["repo_artifacts"]),
        "repo_media": len(cleanup["repo_media"]),
        "staged_media": len(cleanup["staged_media"]),
        "public_json_updates": [rel_path_for_preview(repo_root, path) for path in cleanup["public_json_updates"]],
        "studio_json_updates": [rel_path_for_preview(repo_root, path) for path in cleanup["studio_json_updates"]],
        "delete_paths": [rel_path_for_preview(repo_root, path) for path in cleanup["delete_paths"]],
        "catalogue_search": "assets/data/search/catalogue/index.json" if cleanup["catalogue_search"] else "",
    }


def remove_detail_from_work_record_payload(payload: Dict[str, Any], detail_uid: str) -> bool:
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return False
    changed = False
    next_sections: list[Dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict):
            next_sections.append(section)
            continue
        details = section.get("details")
        if not isinstance(details, list):
            next_sections.append(section)
            continue
        next_details = [
            detail
            for detail in details
            if not (isinstance(detail, dict) and str(detail.get("detail_uid") or "") == detail_uid)
        ]
        if len(next_details) != len(details):
            changed = True
        if next_details:
            next_section = dict(section)
            next_section["details"] = next_details
            next_sections.append(next_section)
    if changed:
        payload["sections"] = next_sections
    return changed


def remove_work_from_series_record_payload(payload: Dict[str, Any], series_id: str, work_id: str) -> bool:
    series_record = payload.get("series")
    if not isinstance(series_record, dict):
        return False
    changed = False
    works = series_record.get("works")
    if isinstance(works, list):
        next_works = [str(value) for value in works if str(value) != work_id]
        if isinstance(payload.get("header"), dict):
            payload["header"]["count"] = len(next_works)
        series_record.pop("works", None)
        changed = True
    if "primary_work_id" in series_record:
        series_record.pop("primary_work_id", None)
        changed = True
    return changed


def remove_series_from_work_record_payload(payload: Dict[str, Any], work_id: str, series_id: str) -> bool:
    work_record = payload.get("work")
    if not isinstance(work_record, dict):
        return False
    series_ids = normalize_series_ids_value(work_record.get("series_ids"))
    if series_id not in series_ids:
        return False
    work_record["series_ids"] = [value for value in series_ids if value != series_id]
    return True


def update_recent_entries_for_work_delete(payload: Dict[str, Any], work_id: str, series_index_payload: Mapping[str, Any]) -> bool:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("recent_index.json must include an entries array")
    series_map = series_index_payload.get("series")
    if not isinstance(series_map, dict):
        series_map = {}
    changed = False
    next_entries: list[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            next_entries.append(entry)
            continue
        kind = str(entry.get("kind") or "")
        target_id = str(entry.get("target_id") or "")
        if kind == "work" and target_id == work_id:
            changed = True
            continue
        if kind == "series":
            series_record = series_map.get(target_id)
            if isinstance(series_record, dict):
                works = [str(value) for value in series_record.get("works") or [] if str(value)]
                next_entry = dict(entry)
                next_entry["caption"] = f"{len(works)} work" if len(works) == 1 else f"{len(works)} works"
                if str(next_entry.get("thumb_id") or "") == work_id:
                    next_entry["thumb_id"] = str(series_record.get("primary_work_id") or (works[0] if works else ""))
                if next_entry != entry:
                    changed = True
                next_entries.append(next_entry)
                continue
        next_entries.append(entry)
    if changed:
        payload["entries"] = next_entries
    return changed


def update_recent_entries_for_series_delete(payload: Dict[str, Any], series_id: str) -> bool:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("recent_index.json must include an entries array")
    next_entries = [
        entry
        for entry in entries
        if not (isinstance(entry, dict) and str(entry.get("kind") or "") == "series" and str(entry.get("target_id") or "") == series_id)
    ]
    if len(next_entries) == len(entries):
        return False
    payload["entries"] = next_entries
    return True


def remove_work_overrides_from_tag_assignments(payload: Dict[str, Any], work_id: str) -> bool:
    series_map = payload.get("series")
    if not isinstance(series_map, dict):
        raise ValueError("tag_assignments.json must include a series object")
    changed = False
    now_utc = activity.utc_now()
    for row in series_map.values():
        if not isinstance(row, dict):
            continue
        works = row.get("works")
        if not isinstance(works, dict) or work_id not in works:
            continue
        del works[work_id]
        row["updated_at_utc"] = now_utc
        changed = True
    if changed:
        payload["updated_at_utc"] = now_utc
    if "tag_assignments_version" not in payload:
        payload["tag_assignments_version"] = "tag_assignments_v1"
    return changed


def remove_series_from_tag_assignments(payload: Dict[str, Any], series_id: str) -> bool:
    series_map = payload.get("series")
    if not isinstance(series_map, dict):
        raise ValueError("tag_assignments.json must include a series object")
    if series_id not in series_map:
        return False
    del series_map[series_id]
    payload["updated_at_utc"] = activity.utc_now()
    if "tag_assignments_version" not in payload:
        payload["tag_assignments_version"] = "tag_assignments_v1"
    return True


def build_catalogue_delete_generated_payloads(
    repo_root: Path,
    kind: str,
    record_id: str,
    affected: Mapping[str, Any],
) -> Dict[Path, Dict[str, Any]]:
    payloads: Dict[Path, Dict[str, Any]] = {}

    def load_existing(rel_path: Path) -> tuple[Path, Dict[str, Any]] | None:
        path = (repo_root / rel_path).resolve()
        if not path.exists():
            return None
        return path, load_json_file(path)

    if kind == "work":
        works_index = load_existing(Path("assets/data/works_index.json"))
        if works_index is not None:
            path, payload = works_index
            works = payload.get("works")
            if isinstance(works, dict) and record_id in works:
                del works[record_id]
                payloads[path] = finalize_works_index_payload(payload)

        work_storage = load_existing(Path("assets/studio/data/work_storage_index.json"))
        if work_storage is not None:
            path, payload = work_storage
            works = payload.get("works")
            if isinstance(works, dict) and record_id in works:
                del works[record_id]
                payloads[path] = finalize_work_storage_index_payload(payload)

        series_index_payload: Dict[str, Any] | None = None
        series_index = load_existing(Path("assets/data/series_index.json"))
        if series_index is not None:
            path, payload = series_index
            series_map = payload.get("series")
            changed = False
            if isinstance(series_map, dict):
                for series_id in affected.get("series") or []:
                    series_record = series_map.get(str(series_id))
                    if not isinstance(series_record, dict):
                        continue
                    works = [str(value) for value in series_record.get("works") or [] if str(value) != record_id]
                    if works != series_record.get("works"):
                        series_record["works"] = works
                        changed = True
            if changed:
                payloads[path] = finalize_series_index_payload(payload)
            series_index_payload = payload

        for series_id in affected.get("series") or []:
            series_payload = load_existing(Path("assets/series/index") / f"{series_id}.json")
            if series_payload is None:
                continue
            path, payload = series_payload
            if remove_work_from_series_record_payload(payload, str(series_id), record_id):
                payloads[path] = finalize_series_record_payload(payload, str(series_id))

        recent_index = load_existing(Path("assets/data/recent_index.json"))
        if recent_index is not None:
            path, payload = recent_index
            if update_recent_entries_for_work_delete(payload, record_id, series_index_payload or {}):
                payloads[path] = finalize_recent_index_payload(payload)

        tag_assignments = load_existing(Path("assets/studio/data/tag_assignments.json"))
        if tag_assignments is not None:
            path, payload = tag_assignments
            if remove_work_overrides_from_tag_assignments(payload, record_id):
                payloads[path] = payload

    elif kind == "work_detail":
        for work_id in affected.get("works") or []:
            work_payload = load_existing(Path("assets/works/index") / f"{work_id}.json")
            if work_payload is None:
                continue
            path, payload = work_payload
            if remove_detail_from_work_record_payload(payload, record_id):
                payloads[path] = finalize_work_record_payload(payload, str(work_id))

    elif kind == "series":
        series_index = load_existing(Path("assets/data/series_index.json"))
        if series_index is not None:
            path, payload = series_index
            series_map = payload.get("series")
            if isinstance(series_map, dict) and record_id in series_map:
                del series_map[record_id]
                payloads[path] = finalize_series_index_payload(payload)

        works_index = load_existing(Path("assets/data/works_index.json"))
        if works_index is not None:
            path, payload = works_index
            works = payload.get("works")
            changed = False
            if isinstance(works, dict):
                for work_id in affected.get("works") or []:
                    work_record = works.get(str(work_id))
                    if not isinstance(work_record, dict):
                        continue
                    series_ids = normalize_series_ids_value(work_record.get("series_ids"))
                    if record_id in series_ids:
                        work_record["series_ids"] = [value for value in series_ids if value != record_id]
                        changed = True
            if changed:
                payloads[path] = finalize_works_index_payload(payload)

        for work_id in affected.get("works") or []:
            work_payload = load_existing(Path("assets/works/index") / f"{work_id}.json")
            if work_payload is None:
                continue
            path, payload = work_payload
            if remove_series_from_work_record_payload(payload, str(work_id), record_id):
                payloads[path] = finalize_work_record_payload(payload, str(work_id))

        recent_index = load_existing(Path("assets/data/recent_index.json"))
        if recent_index is not None:
            path, payload = recent_index
            if update_recent_entries_for_series_delete(payload, record_id):
                payloads[path] = finalize_recent_index_payload(payload)

        tag_assignments = load_existing(Path("assets/studio/data/tag_assignments.json"))
        if tag_assignments is not None:
            path, payload = tag_assignments
            if remove_series_from_tag_assignments(payload, record_id):
                payloads[path] = payload

    return payloads


def build_moment_delete_generated_payloads(repo_root: Path, moment_id: str) -> Dict[Path, Dict[str, Any]]:
    payloads: Dict[Path, Dict[str, Any]] = {}
    moments_index_path = (repo_root / "assets" / "data" / "moments_index.json").resolve()
    if not moments_index_path.exists():
        return payloads

    moments_index_payload = load_json_file(moments_index_path)
    moments_map = moments_index_payload.get("moments")
    if not isinstance(moments_map, dict):
        raise ValueError("moments_index.json must include a moments object")
    moments_map.pop(moment_id, None)
    payloads[moments_index_path] = finalize_moments_index_payload(moments_index_payload)
    return payloads


def moment_delete_preview_cleanup(repo_root: Path, moment_id: str) -> Dict[str, Any]:
    cleanup = collect_moment_delete_cleanup(repo_root, moment_id)
    return {
        "repo_artifacts": len(cleanup["repo_artifacts"]),
        "repo_media": len(cleanup["repo_media"]),
        "staged_media": len(cleanup["staged_media"]),
        "delete_paths": [str(path.relative_to(repo_root)) if path_is_under(path, repo_root) else path.name for path in cleanup["delete_paths"]],
        "moments_index": "assets/data/moments_index.json",
        "catalogue_search": "assets/data/search/catalogue/index.json",
    }


def delete_existing_files(paths: Iterable[Path]) -> int:
    deleted = 0
    for path in unique_existing_paths(paths):
        path.unlink()
        deleted += 1
    return deleted
