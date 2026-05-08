#!/usr/bin/env python3
"""Catalogue staged prose and draft moment import helpers."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

from catalogue_json_build import preview_moment_source
from catalogue_source import records_from_json_source, slug_id
import catalogue_transactions as transactions
from moment_sources import (
    CATALOGUE_MOMENT_PROSE_REL_DIR,
    MOMENT_METADATA_FILENAME,
    load_moment_metadata_records,
    moment_metadata_payload,
    normalize_moment_filename,
    normalize_moment_metadata_record,
)
from series_ids import normalize_series_id


CATALOGUE_PROSE_STAGING_REL_DIR = Path("var/docs/catalogue/import-staging")
CATALOGUE_PROSE_SOURCE_REL_DIR = Path("_docs_src_catalogue")
MAX_PROSE_MARKDOWN_BYTES = 1024 * 1024


@dataclass(frozen=True)
class ProseImportTarget:
    target_kind: str
    target_id: str
    collection: str
    staging_path: Path
    target_path: Path

    @property
    def staging_rel_path(self) -> str:
        return str((CATALOGUE_PROSE_STAGING_REL_DIR / self.collection / f"{self.target_id}.md")).replace(os.sep, "/")

    @property
    def target_rel_path(self) -> str:
        return str((CATALOGUE_PROSE_SOURCE_REL_DIR / self.collection / f"{self.target_id}.md")).replace(os.sep, "/")


@dataclass(frozen=True)
class ProseImportApplyResult:
    target: ProseImportTarget
    preview: Dict[str, Any]
    changed: bool


@dataclass(frozen=True)
class MomentImportRequest:
    moment_file: str
    metadata: Dict[str, Any]
    force: bool


@dataclass(frozen=True)
class MomentImportApplyResult:
    moment_file: str
    moment_id: str
    preview: Dict[str, Any]
    metadata_path: Path
    target_path: Path
    backup_paths: list[Path]


def normalize_moment_id_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("moment_id is required")
    return normalize_moment_filename(text if text.endswith(".md") else f"{text}.md")[:-3]


def extract_moment_import_request(body: Mapping[str, Any]) -> MomentImportRequest:
    moment_file = str(body.get("moment_file") or body.get("file") or "").strip()
    if not moment_file:
        raise ValueError("moment_file is required")
    metadata_value = body.get("metadata")
    metadata: Dict[str, Any] = dict(metadata_value) if isinstance(metadata_value, Mapping) else {}
    for key in ["title", "status", "published_date", "date", "date_display", "source_image_file", "image_file", "image_alt"]:
        if key in body and key not in metadata:
            metadata[key] = body.get(key)
    metadata["status"] = "draft"
    return MomentImportRequest(moment_file=moment_file, metadata=metadata, force=bool(body.get("force")))


def normalize_prose_import_target(body: Mapping[str, Any]) -> tuple[str, str, str]:
    target_kind = str(body.get("target_kind") or body.get("kind") or "").strip().lower()
    if target_kind not in {"work", "series", "moment"}:
        raise ValueError("target_kind must be work, series, or moment")
    raw_id = body.get("target_id")
    if raw_id is None:
        raw_id = body.get("work_id") if target_kind == "work" else body.get("series_id") if target_kind == "series" else body.get("moment_id")
    target_id = slug_id(raw_id) if target_kind == "work" else normalize_series_id(raw_id) if target_kind == "series" else normalize_moment_id_value(raw_id)
    collection = "works" if target_kind == "work" else "series" if target_kind == "series" else "moments"
    return target_kind, target_id, collection


def resolve_prose_import_target(repo_root: Path, body: Mapping[str, Any]) -> ProseImportTarget:
    target_kind, target_id, collection = normalize_prose_import_target(body)
    return ProseImportTarget(
        target_kind=target_kind,
        target_id=target_id,
        collection=collection,
        staging_path=repo_root / CATALOGUE_PROSE_STAGING_REL_DIR / collection / f"{target_id}.md",
        target_path=repo_root / CATALOGUE_PROSE_SOURCE_REL_DIR / collection / f"{target_id}.md",
    )


def ensure_direct_child(path: Path, allowed_parent: Path) -> None:
    if path.resolve().parent != allowed_parent.resolve():
        raise ValueError("write target is outside the allowlisted prose source root")


def validate_prose_import_target_exists(source_dir: Path, target_kind: str, target_id: str) -> None:
    records = records_from_json_source(source_dir)
    if target_kind == "work" and target_id not in records.works:
        raise ValueError(f"work_id not found: {target_id}")
    if target_kind == "series" and target_id not in records.series:
        raise ValueError(f"series_id not found: {target_id}")
    if target_kind == "moment":
        moments = load_moment_metadata_records(source_dir)
        if target_id not in moments:
            raise ValueError(f"moment_id not found: {target_id}")


def read_staged_prose_markdown(staging_path: Path) -> tuple[str, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not staging_path.exists():
        return "", [f"Missing staged Markdown file: {staging_path.name}"], warnings
    if not staging_path.is_file():
        return "", [f"Staged Markdown path is not a file: {staging_path.name}"], warnings
    try:
        size = staging_path.stat().st_size
    except OSError as exc:
        return "", [f"Could not stat staged Markdown file: {exc}"], warnings
    if size > MAX_PROSE_MARKDOWN_BYTES:
        errors.append(f"Staged Markdown file is larger than {MAX_PROSE_MARKDOWN_BYTES} bytes.")
    try:
        text = staging_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "", ["Staged Markdown file must be UTF-8 text."], warnings
    except OSError as exc:
        return "", [f"Could not read staged Markdown file: {exc}"], warnings
    if "\x00" in text:
        errors.append("Staged Markdown file contains a null byte.")
    if not text.strip():
        warnings.append("Staged Markdown file is blank; importing it will publish blank optional prose after the generator lookup is updated.")
    return text, errors, warnings


def build_prose_import_preview(
    repo_root: Path,
    source_dir: Path,
    body: Mapping[str, Any],
) -> Dict[str, Any]:
    target = resolve_prose_import_target(repo_root, body)
    validate_prose_import_target_exists(source_dir, target.target_kind, target.target_id)
    text, errors, warnings = read_staged_prose_markdown(target.staging_path)
    target_exists = target.target_path.exists()
    target_text = ""
    if target_exists:
        try:
            target_text = target.target_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            warnings.append("Existing permanent prose file could not be read for content comparison.")
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest() if not errors else ""
    target_hash = hashlib.sha256(target_text.encode("utf-8")).hexdigest() if target_text else ""
    changed = not target_exists or text != target_text
    return {
        "ok": True,
        "valid": not errors,
        "target_kind": target.target_kind,
        "target_id": target.target_id,
        "staging_path": target.staging_rel_path,
        "target_path": target.target_rel_path,
        "staging_exists": target.staging_path.exists(),
        "target_exists": target_exists,
        "overwrite_required": bool(target_exists and changed),
        "changed": changed,
        "byte_count": len(text.encode("utf-8")) if not errors else 0,
        "line_count": len(text.splitlines()) if not errors else 0,
        "content_sha256": content_hash,
        "target_sha256": target_hash,
        "errors": errors,
        "warnings": warnings,
    }


def apply_prose_import(
    repo_root: Path,
    source_dir: Path,
    body: Mapping[str, Any],
    *,
    allowed_write_roots: set[Path],
    dry_run: bool,
    preview: Mapping[str, Any] | None = None,
) -> ProseImportApplyResult:
    preview_payload = dict(preview) if preview is not None else build_prose_import_preview(repo_root, source_dir, body)
    if not preview_payload.get("valid"):
        errors = preview_payload.get("errors") if isinstance(preview_payload.get("errors"), list) else []
        raise ValueError("; ".join(str(error) for error in errors) or "prose import preview failed")

    target = resolve_prose_import_target(repo_root, body)
    target_root = (repo_root / CATALOGUE_PROSE_SOURCE_REL_DIR / target.collection).resolve()
    if target_root not in allowed_write_roots:
        raise ValueError("prose source root is not allowlisted")
    ensure_direct_child(target.target_path, target_root)
    text, errors, _warnings = read_staged_prose_markdown(target.staging_path)
    if errors:
        raise ValueError("; ".join(errors))

    changed = bool(preview_payload.get("changed"))
    if changed and not dry_run:
        transactions.atomic_write_text_no_backup(target.target_path, text)
    return ProseImportApplyResult(target=target, preview=preview_payload, changed=changed)


def build_moment_import_preview(repo_root: Path, body: Mapping[str, Any]) -> Dict[str, Any]:
    request = extract_moment_import_request(body)
    preview = preview_moment_source(repo_root, request.moment_file, metadata=request.metadata, staged=True)
    return {
        "ok": True,
        "moment_file": preview.get("moment_file") or request.moment_file,
        "preview": preview,
        "build": {},
        "steps": [],
        "published": False,
    }


def apply_moment_import(
    repo_root: Path,
    source_dir: Path,
    body: Mapping[str, Any],
    *,
    allowed_write_roots: set[Path],
    backups_dir: Path,
    dry_run: bool,
) -> MomentImportApplyResult:
    request = extract_moment_import_request(body)
    preview = preview_moment_source(repo_root, request.moment_file, metadata=request.metadata, staged=True)
    if not preview.get("valid"):
        errors = preview.get("errors") or []
        raise ValueError("; ".join(str(error) for error in errors) or "moment import preview failed")

    moment_filename = normalize_moment_filename(request.moment_file)
    moment_id_for_write = moment_filename[:-3]
    staging_path = repo_root / CATALOGUE_PROSE_STAGING_REL_DIR / "moments" / moment_filename
    target_path = repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR / moment_filename
    target_root = (repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR).resolve()
    if target_root not in allowed_write_roots:
        raise ValueError("moment prose source root is not allowlisted")
    ensure_direct_child(target_path, target_root)
    text = staging_path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"

    metadata_records = load_moment_metadata_records(source_dir)
    merged_metadata = normalize_moment_metadata_record(
        moment_id_for_write,
        {**metadata_records.get(moment_id_for_write, {}), **request.metadata, "moment_id": moment_id_for_write},
    )
    metadata_records[moment_id_for_write] = merged_metadata
    metadata_path = source_dir / MOMENT_METADATA_FILENAME
    target_payloads: Dict[Path, Dict[str, Any]] = {
        metadata_path: moment_metadata_payload(metadata_records),
    }
    moment_id = str(preview.get("moment_id") or moment_id_for_write).strip().lower()
    backup_paths: list[Path] = []
    if not dry_run:
        transactions.atomic_write_text_no_backup(target_path, text)
        backup_paths = transactions.atomic_write_many(target_payloads, backups_dir)

    return MomentImportApplyResult(
        moment_file=str(preview.get("moment_file") or request.moment_file),
        moment_id=moment_id,
        preview=preview,
        metadata_path=metadata_path,
        target_path=target_path,
        backup_paths=backup_paths,
    )
