#!/usr/bin/env python3
"""Refresh generated Catalogue document URLs after successful Docs publication."""

from __future__ import annotations

import copy
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from catalogue import catalogue_public_paths as public_paths
from catalogue.catalogue_generation_records import (
    SERIES_RECORD_SCHEMA_VERSION,
    WORK_RECORD_SCHEMA_VERSION,
    build_series_json_payload,
    build_work_json_payload,
    normalize_document_urls,
)


CatalogueDocumentUrls = Mapping[str, Mapping[str, Sequence[str]]]
CatalogueTarget = tuple[str, str]
WORK_ID_PATTERN = re.compile(r"\A\d{5}\Z")
SERIES_ID_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9-]*\Z")


@dataclass(frozen=True)
class CatalogueDocumentUrlRefreshPlan:
    """Exact generated payload writes required by one current projection."""

    affected_targets: tuple[CatalogueTarget, ...]
    payloads_by_path: Mapping[Path, dict[str, Any]]


@dataclass(frozen=True)
class CatalogueDocumentUrlRefreshResult:
    affected_targets: tuple[CatalogueTarget, ...]
    written_paths: tuple[Path, ...]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def target_spec(kind: str) -> tuple[Path, str, str, str]:
    if kind == "work":
        return public_paths.WORKS_JSON_DIR, "work", "work_id", WORK_RECORD_SCHEMA_VERSION
    if kind == "series":
        return public_paths.SERIES_JSON_DIR, "series", "series_id", SERIES_RECORD_SCHEMA_VERSION
    raise ValueError(f"unsupported Catalogue document URL target kind: {kind!r}")


def validate_target_key(kind: str, key: str) -> None:
    pattern = WORK_ID_PATTERN if kind == "work" else SERIES_ID_PATTERN
    if not pattern.fullmatch(key):
        raise ValueError(f"invalid exact {kind} document URL target: {key!r}")


def normalize_projection(projection: CatalogueDocumentUrls) -> dict[str, dict[str, list[str]]]:
    if not isinstance(projection, Mapping):
        raise ValueError("Catalogue document URL projection must be an object")
    unsupported = sorted(str(kind) for kind in projection if kind not in {"work", "series"})
    if unsupported:
        raise ValueError(
            "unsupported Catalogue document URL projection kinds: "
            + ", ".join(unsupported)
        )

    normalized: dict[str, dict[str, list[str]]] = {"work": {}, "series": {}}
    for kind in ("work", "series"):
        values_by_key = projection.get(kind, {})
        if not isinstance(values_by_key, Mapping):
            raise ValueError(f"Catalogue {kind} document URL projection must be an object")
        for raw_key, raw_urls in values_by_key.items():
            if not isinstance(raw_key, str):
                raise ValueError(f"Catalogue {kind} document URL target must be a string")
            validate_target_key(kind, raw_key)
            if not isinstance(raw_urls, Sequence) or isinstance(raw_urls, (str, bytes)):
                raise ValueError(f"Catalogue {kind} {raw_key} doc_url must be an array")
            normalized[kind][raw_key] = normalize_document_urls(raw_urls)
    return normalized


def load_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"generated Catalogue payload is missing: {path.name}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"generated Catalogue payload is unreadable: {path.name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"generated Catalogue payload must be an object: {path.name}")
    return payload


def validate_payload_identity(
    payload: Mapping[str, Any],
    *,
    path: Path,
    kind: str,
    key: str,
) -> tuple[dict[str, Any], int]:
    _directory, record_key, id_key, schema = target_spec(kind)
    header = payload.get("header")
    record = payload.get(record_key)
    if not isinstance(header, dict) or not isinstance(record, dict):
        raise ValueError(f"generated Catalogue {kind} payload has no header/{record_key}: {path.name}")
    if header.get("schema") != schema:
        raise ValueError(f"generated Catalogue {kind} payload has unsupported schema: {path.name}")
    if header.get(id_key) != key or record.get(id_key) != key or path.stem != key:
        raise ValueError(f"generated Catalogue {kind} payload identity mismatch: {path.name}")
    count = header.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError(f"generated Catalogue {kind} payload has invalid count: {path.name}")
    return record, count


def current_nonempty_targets(repo_root: Path) -> dict[CatalogueTarget, tuple[Path, dict[str, Any], list[str]]]:
    current: dict[CatalogueTarget, tuple[Path, dict[str, Any], list[str]]] = {}
    for kind in ("work", "series"):
        directory, record_key, _id_key, _schema = target_spec(kind)
        root = repo_root / directory
        if not root.exists():
            continue
        for path in sorted(root.glob("*.json")):
            payload = load_payload(path)
            record = payload.get(record_key)
            if not isinstance(record, dict):
                raise ValueError(f"generated Catalogue {kind} payload has no {record_key}: {path.name}")
            raw_urls = record.get("doc_url", [])
            if not isinstance(raw_urls, list):
                raise ValueError(f"generated Catalogue {kind} {path.stem} doc_url must be an array")
            urls = normalize_document_urls(raw_urls)
            if not urls:
                continue
            key = path.stem
            validate_target_key(kind, key)
            validate_payload_identity(payload, path=path, kind=kind, key=key)
            current[(kind, key)] = (path, payload, urls)
    return current


def target_payload_path(repo_root: Path, kind: str, key: str) -> Path:
    directory, _record_key, _id_key, _schema = target_spec(kind)
    return repo_root / directory / f"{key}.json"


def updated_payload(
    payload: Mapping[str, Any],
    *,
    path: Path,
    kind: str,
    key: str,
    urls: Sequence[str],
    generated_at_utc: str,
) -> dict[str, Any]:
    result = copy.deepcopy(dict(payload))
    record, count = validate_payload_identity(result, path=path, kind=kind, key=key)
    record["doc_url"] = normalize_document_urls(urls)

    if kind == "work":
        sections = result.get("sections")
        if not isinstance(sections, list):
            raise ValueError(f"generated Catalogue work payload has invalid sections: {path.name}")
        return build_work_json_payload(
            work_id=key,
            work_record=record,
            sections=sections,
            generated_at_utc=generated_at_utc,
            count=count,
        )
    member_works = result.get("member_works")
    if not isinstance(member_works, list):
        raise ValueError(f"generated Catalogue series payload has invalid member_works: {path.name}")
    return build_series_json_payload(
        series_id=key,
        series_record=record,
        member_works=member_works,
        generated_at_utc=generated_at_utc,
    )


def build_catalogue_document_url_refresh_plan(
    repo_root: Path,
    projection: CatalogueDocumentUrls,
    *,
    generated_at_utc: str | None = None,
) -> CatalogueDocumentUrlRefreshPlan:
    """Compare complete desired URLs with current generated non-empty URLs."""

    repo_root = repo_root.resolve()
    desired = normalize_projection(projection)
    current = current_nonempty_targets(repo_root)
    candidate_targets = set(current)
    candidate_targets.update(
        (kind, key)
        for kind in ("work", "series")
        for key in desired[kind]
    )

    affected_targets: list[CatalogueTarget] = []
    payloads_by_path: dict[Path, dict[str, Any]] = {}
    timestamp = generated_at_utc or utc_now()
    for kind, key in sorted(candidate_targets):
        desired_urls = desired[kind].get(key, [])
        current_entry = current.get((kind, key))
        if current_entry is None:
            path = target_payload_path(repo_root, kind, key)
            payload = load_payload(path)
            record_key = target_spec(kind)[1]
            record = payload.get(record_key)
            if not isinstance(record, dict):
                raise ValueError(f"generated Catalogue {kind} payload has no {record_key}: {path.name}")
            raw_current_urls = record.get("doc_url", [])
            if not isinstance(raw_current_urls, list):
                raise ValueError(f"generated Catalogue {kind} {key} doc_url must be an array")
            current_urls = normalize_document_urls(raw_current_urls)
        else:
            path, payload, current_urls = current_entry
        if current_urls == desired_urls:
            continue
        affected_targets.append((kind, key))
        payloads_by_path[path] = updated_payload(
            payload,
            path=path,
            kind=kind,
            key=key,
            urls=desired_urls,
            generated_at_utc=timestamp,
        )

    return CatalogueDocumentUrlRefreshPlan(
        affected_targets=tuple(affected_targets),
        payloads_by_path=payloads_by_path,
    )


def apply_catalogue_document_url_refresh_plan(
    plan: CatalogueDocumentUrlRefreshPlan,
) -> CatalogueDocumentUrlRefreshResult:
    from catalogue import catalogue_transactions as transactions

    written_paths: tuple[Path, ...] = ()
    if plan.payloads_by_path:
        written_paths = tuple(transactions.atomic_write_many(dict(plan.payloads_by_path)))
    return CatalogueDocumentUrlRefreshResult(
        affected_targets=plan.affected_targets,
        written_paths=written_paths,
    )


def refresh_catalogue_document_urls(
    repo_root: Path,
    projection: CatalogueDocumentUrls,
) -> CatalogueDocumentUrlRefreshResult:
    plan = build_catalogue_document_url_refresh_plan(repo_root, projection)
    return apply_catalogue_document_url_refresh_plan(plan)


__all__ = [
    "CatalogueDocumentUrlRefreshPlan",
    "CatalogueDocumentUrlRefreshResult",
    "apply_catalogue_document_url_refresh_plan",
    "build_catalogue_document_url_refresh_plan",
    "refresh_catalogue_document_urls",
]
