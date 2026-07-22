#!/usr/bin/env python3
"""Atomic publication of persistent Docs Review packages."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable

from docs_management_source_service import split_source_exact
from docs_review_build import build_review_package


REVIEW_PACKAGE_IDENTITY_FIELDS = (
    "schema_version",
    "package_id",
    "status",
    "data_domain",
    "source_scope",
    "default_doc_id",
    "profile_id",
    "source_projection",
    "source_export_id",
    "package_id_source",
    "content_format",
    "content_mapping",
    "generated_at",
    "source_files",
)


def _safe_source_filename(value: Any) -> str:
    filename = str(value or "").strip()
    if not filename or Path(filename).name != filename or not filename.endswith(".md"):
        raise ValueError("review source filename must be a direct-child Markdown filename")
    return filename


def _read_manifest(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("existing review package manifest is unavailable")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("existing review package manifest is invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("existing review package manifest must be an object")
    return payload


def _source_identity(source_text: str) -> tuple[dict[str, Any], str]:
    try:
        _front_matter_source, front_matter, body = split_source_exact(source_text)
    except ValueError as exc:
        raise ValueError("existing review package source is invalid") from exc
    identity_front_matter = dict(front_matter)
    identity_front_matter.pop("added_date", None)
    identity_front_matter.pop("last_updated", None)
    return identity_front_matter, body


def match_existing_review_package(
    *,
    package_path: Path,
    package_id: str,
    source_records: Iterable[dict[str, Any]],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Accept only an existing validated package with the same identity and source set."""

    if package_path.is_symlink() or not package_path.is_dir():
        raise ValueError("existing review package folder is invalid")
    existing_manifest = _read_manifest(package_path / "manifest.json")
    for field in REVIEW_PACKAGE_IDENTITY_FIELDS:
        if existing_manifest.get(field) != manifest.get(field):
            raise ValueError(f"existing review package manifest differs at {field}")
    if str(existing_manifest.get("package_id") or "").strip() != package_id:
        raise ValueError("existing review package id does not match its folder")

    expected_sources: dict[str, str] = {}
    for record in source_records:
        filename = _safe_source_filename(record.get("filename"))
        source_text = record.get("source_text")
        if not isinstance(source_text, str):
            raise ValueError("review source_text must be a string")
        if filename in expected_sources:
            raise ValueError(f"duplicate review source filename: {filename}")
        expected_sources[filename] = source_text

    source_root = package_path / "source"
    if source_root.is_symlink() or not source_root.is_dir():
        raise ValueError("existing review package source folder is invalid")
    existing_paths = list(source_root.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in existing_paths):
        raise ValueError("existing review package source set contains an invalid entry")
    if {path.name for path in existing_paths} != set(expected_sources):
        raise ValueError("existing review package source filenames differ")
    for filename, expected_source in expected_sources.items():
        try:
            existing_source = (source_root / filename).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"existing review package source is unreadable: {filename}") from exc
        if _source_identity(existing_source) != _source_identity(expected_source):
            raise ValueError(f"existing review package source differs: {filename}")
    return {"document_count": len(expected_sources)}


def publish_review_package(
    repo_root: Path,
    *,
    package_path: Path,
    package_id: str,
    default_doc_id: str,
    source_records: Iterable[dict[str, Any]],
    manifest: dict[str, Any],
    asset_records: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Build a complete package beside its final path, then publish it once."""

    if package_path.exists() or package_path.is_symlink():
        raise FileExistsError(f"review package already exists: {package_id}")
    package_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = Path(
        tempfile.mkdtemp(
            prefix=f".{package_id}.publishing-",
            dir=package_path.parent,
        )
    )
    try:
        sources = [dict(record) for record in source_records]
        source_dir = temporary_path / "source"
        source_dir.mkdir()
        for record in sources:
            filename = _safe_source_filename(record.get("filename"))
            source_text = record.get("source_text")
            if not isinstance(source_text, str):
                raise ValueError("review source_text must be a string")
            (source_dir / filename).write_text(source_text, encoding="utf-8")

        assets = [dict(record) for record in asset_records]
        build = build_review_package(
            repo_root,
            package_id=package_id,
            source_dir=source_dir,
            generated_dir=temporary_path / "generated",
            default_doc_id=default_doc_id,
            asset_records=assets,
        )
        if int(build.get("document_count") or 0) != len(sources):
            raise RuntimeError("review package generated document count does not match its source set")
        (temporary_path / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.rename(package_path)
        return build
    finally:
        if temporary_path.exists():
            shutil.rmtree(temporary_path)


__all__ = ["match_existing_review_package", "publish_review_package"]
