#!/usr/bin/env python3
"""Validated returned-package reads, builds, and temporary source writes."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import docs_source_model as source_model
from docs_management_source_service import (
    normalize_source_body,
    source_revision_for_text,
    split_source_exact,
)
from docs_review_build import build_review_package
from services.paths import configured_workspace_paths, marker_path

PACKAGE_SCHEMA_VERSION = "docs_review_validated_package_v1"
PACKAGES_SCHEMA_VERSION = "docs_review_packages_v1"
SAFE_PACKAGE_ID_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SAFE_DOC_ID_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")
INVENTORY_FILENAMES = (
    "assets.json",
    "links.json",
    "embedded-content.json",
)


def _workspace_paths(repo_root: Path):
    return configured_workspace_paths(repo_root)


def package_root(repo_root: Path) -> Path:
    return _workspace_paths(repo_root).import_preview.resolve()


def validate_package_id(value: Any) -> str:
    package_id = str(value or "").strip()
    if not package_id:
        raise ValueError("package_id is required")
    if not SAFE_PACKAGE_ID_PATTERN.fullmatch(package_id):
        raise ValueError("package_id contains unsupported characters")
    return package_id


def validate_doc_id(value: Any) -> str:
    doc_id = str(value or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")
    if not SAFE_DOC_ID_PATTERN.fullmatch(doc_id):
        raise ValueError("doc_id contains unsupported characters")
    return doc_id


def resolve_package_path(repo_root: Path, package_id: Any) -> Path:
    normalized = validate_package_id(package_id)
    root = package_root(repo_root)
    candidate = root / normalized
    if candidate.is_symlink():
        raise ValueError("review package folders must not be symlinks")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("package_id resolves outside the review package root") from error
    return resolved


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} is not valid JSON: {path.name}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object: {path.name}")
    return payload


def _validated_manifest(package_path: Path) -> dict[str, Any]:
    manifest = _read_json_object(package_path / "manifest.json", "review package manifest")
    if manifest.get("schema_version") != PACKAGE_SCHEMA_VERSION:
        raise ValueError(f"review package manifest schema_version must be {PACKAGE_SCHEMA_VERSION}")
    if str(manifest.get("package_id") or "").strip() != package_path.name:
        raise ValueError("review package manifest package_id does not match its folder")
    if str(manifest.get("status") or "").strip().lower() != "validated":
        raise ValueError("review package manifest status must be validated")
    source_scope = str(manifest.get("source_scope") or "").strip()
    if not source_scope:
        raise ValueError("review package manifest source_scope is required")
    return manifest


def _source_files(package_path: Path) -> list[Path]:
    source_root = package_path / "source"
    if source_root.is_symlink():
        raise ValueError("review package source folder must not be a symlink")
    if not source_root.is_dir():
        raise FileNotFoundError("review package source folder not found")
    nested = [path for path in source_root.rglob("*.md") if path.parent != source_root]
    if nested:
        raise ValueError("review package source Markdown files must be direct children of source/")
    files = sorted(source_root.glob("*.md"), key=lambda path: path.name.lower())
    if not files:
        raise ValueError("review package must contain at least one source Markdown file")
    if any(path.is_symlink() for path in files):
        raise ValueError("review package source files must not be symlinks")
    return files


def _source_record(path: Path) -> dict[str, Any]:
    source_text = path.read_text(encoding="utf-8")
    _front_matter_source, front_matter, source_body = split_source_exact(source_text)
    doc_id = validate_doc_id(front_matter.get("doc_id"))
    if path.stem != doc_id:
        raise ValueError(f"review source filename must match doc_id: {path.name}")
    return {
        "doc_id": doc_id,
        "path": path,
        "front_matter": front_matter,
        "source_text": source_text,
        "source_body": source_body,
    }


def _source_records(package_path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in _source_files(package_path):
        record = _source_record(path)
        doc_id = record["doc_id"]
        if doc_id in records:
            raise ValueError(f"duplicate review source doc_id: {doc_id}")
        records[doc_id] = record
    return records


def _package_context(repo_root: Path, package_id: Any) -> tuple[Path, dict[str, Any], dict[str, dict[str, Any]]]:
    package_path = resolve_package_path(repo_root, package_id)
    if not package_path.is_dir():
        raise FileNotFoundError(f"review package not found: {validate_package_id(package_id)}")
    manifest = _validated_manifest(package_path)
    records = _source_records(package_path)
    default_doc_id = str(manifest.get("default_doc_id") or "").strip()
    if default_doc_id and default_doc_id not in records:
        raise ValueError("review package default_doc_id does not identify a source document")
    return package_path, manifest, records


def _package_marker(repo_root: Path, path: Path) -> str:
    paths = _workspace_paths(repo_root)
    return marker_path(path, workspace_root=paths.root)


def _generated_payload_count(package_path: Path) -> int:
    root = package_path / "generated" / "by-id"
    return sum(1 for path in root.glob("*.json") if path.is_file()) if root.is_dir() else 0


def _safe_package_asset_path(package_path: Path, value: Any) -> Path:
    text = str(value or "").strip()
    relative = Path(text)
    if not text or relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "assets":
        raise ValueError("review package asset path must be a safe path under assets/")
    assets_root = package_path / "assets"
    candidate = package_path / relative
    current = candidate
    while current != package_path:
        if current.is_symlink():
            raise ValueError("review package asset paths must not contain symlinks")
        current = current.parent
    resolved = candidate.resolve()
    try:
        resolved.relative_to(assets_root.resolve())
    except ValueError as error:
        raise ValueError("review package asset path escapes assets/") from error
    if not resolved.is_file():
        raise FileNotFoundError(f"review package asset not found: {text}")
    return resolved


def _asset_records(package_path: Path) -> list[dict[str, Any]]:
    path = package_path / "inventories" / "assets.json"
    if not path.exists():
        return []
    payload = _read_json_object(path, "review package asset inventory")
    raw_records = payload.get("assets")
    if not isinstance(raw_records, list):
        raise ValueError("review package asset inventory assets must be an array")
    records: list[dict[str, Any]] = []
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            raise ValueError("review package asset inventory records must be objects")
        kind = str(raw_record.get("kind") or "").strip().lower()
        if kind not in {"media", "interactive"}:
            raise ValueError("review package asset kind must be media or interactive")
        token_path = str(raw_record.get("token_path") or "").strip()
        if not token_path:
            raise ValueError("review package asset token_path is required")
        package_asset_path = str(raw_record.get("package_path") or "").strip()
        _safe_package_asset_path(package_path, package_asset_path)
        records.append({**raw_record, "kind": kind, "token_path": token_path, "package_path": package_asset_path})
    return records


def package_record(repo_root: Path, package_path: Path) -> dict[str, Any]:
    manifest = _validated_manifest(package_path)
    records = _source_records(package_path)
    generated_count = _generated_payload_count(package_path)
    return {
        "package_id": package_path.name,
        "title": str(manifest.get("title") or package_path.name),
        "source_scope": str(manifest.get("source_scope") or ""),
        "default_doc_id": str(manifest.get("default_doc_id") or ""),
        "path": _package_marker(repo_root, package_path),
        "document_count": len(records),
        "generated_document_count": generated_count,
        "built": (package_path / "generated" / "index-tree.json").is_file() and generated_count == len(records),
    }


def list_packages(repo_root: Path) -> dict[str, Any]:
    root = package_root(repo_root)
    if not root.exists():
        return {
            "ok": True,
            "schema_version": PACKAGES_SCHEMA_VERSION,
            "root": _package_marker(repo_root, root),
            "packages": [],
            "rejected": [],
        }
    if not root.is_dir():
        raise ValueError("review package root is not a directory")
    packages = []
    rejected = []
    for candidate in sorted(root.iterdir(), key=lambda path: path.name.lower()):
        if candidate.is_symlink() or not candidate.is_dir() or not SAFE_PACKAGE_ID_PATTERN.fullmatch(candidate.name):
            continue
        try:
            packages.append(package_record(repo_root, candidate.resolve()))
        except (FileNotFoundError, ValueError) as error:
            rejected.append({
                "package_id": candidate.name,
                "path": _package_marker(repo_root, candidate),
                "error": str(error),
            })
    return {
        "ok": True,
        "schema_version": PACKAGES_SCHEMA_VERSION,
        "root": _package_marker(repo_root, root),
        "packages": packages,
        "rejected": rejected,
    }


def read_manifest(repo_root: Path, package_id: Any) -> dict[str, Any]:
    package_path, manifest, records = _package_context(repo_root, package_id)
    return {
        "ok": True,
        "package_id": package_path.name,
        "manifest": manifest,
        "document_count": len(records),
    }


def read_asset_inventories(repo_root: Path, package_id: Any) -> dict[str, Any]:
    package_path, _manifest, _records = _package_context(repo_root, package_id)
    inventory_root = package_path / "inventories"
    if inventory_root.is_symlink():
        raise ValueError("review package inventories folder must not be a symlink")
    inventories: dict[str, dict[str, Any]] = {}
    for filename in INVENTORY_FILENAMES:
        path = inventory_root / filename
        if path.is_symlink():
            raise ValueError("review package inventory files must not be symlinks")
        if path.exists():
            inventories[filename.removesuffix(".json")] = _read_json_object(path, "review package inventory")
    return {
        "ok": True,
        "package_id": package_path.name,
        "inventories": inventories,
    }


def resolve_asset_file(repo_root: Path, package_id: Any, asset_path: Any) -> Path:
    package_path, _manifest, _records = _package_context(repo_root, package_id)
    inventoried = _asset_records(package_path)
    requested = str(asset_path or "").strip()
    if requested not in {str(record.get("package_path") or "") for record in inventoried}:
        raise FileNotFoundError("review package asset is not inventoried")
    return _safe_package_asset_path(package_path, requested)


def read_index_tree(repo_root: Path, package_id: Any) -> dict[str, Any]:
    package_path, _manifest, _records = _package_context(repo_root, package_id)
    payload = _read_json_object(package_path / "generated" / "index-tree.json", "review package index tree")
    return {"ok": True, "package_id": package_path.name, "index_tree": payload}


def read_payload(repo_root: Path, package_id: Any, doc_id: Any) -> dict[str, Any]:
    package_path, _manifest, records = _package_context(repo_root, package_id)
    normalized_doc_id = validate_doc_id(doc_id)
    if normalized_doc_id not in records:
        raise FileNotFoundError(f"review package document not found: {normalized_doc_id}")
    payload = _read_json_object(
        package_path / "generated" / "by-id" / f"{normalized_doc_id}.json",
        "review package document payload",
    )
    return {
        "ok": True,
        "package_id": package_path.name,
        "doc_id": normalized_doc_id,
        "payload": payload,
    }


def read_source(repo_root: Path, package_id: Any, doc_id: Any) -> dict[str, Any]:
    package_path, _manifest, records = _package_context(repo_root, package_id)
    normalized_doc_id = validate_doc_id(doc_id)
    record = records.get(normalized_doc_id)
    if record is None:
        raise FileNotFoundError(f"review package document not found: {normalized_doc_id}")
    return {
        "ok": True,
        "package_id": package_path.name,
        "doc_id": normalized_doc_id,
        "source_body": normalize_source_body(record["source_body"]),
        "source_revision": source_revision_for_text(record["source_text"]),
        "path": _package_marker(repo_root, record["path"]),
    }


def build_package(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    package_path, manifest, records = _package_context(repo_root, body.get("package_id"))
    default_doc_id = str(manifest.get("default_doc_id") or "").strip() or next(iter(records))
    build = build_review_package(
        repo_root,
        package_id=package_path.name,
        source_dir=package_path / "source",
        generated_dir=package_path / "generated",
        default_doc_id=default_doc_id,
        asset_records=_asset_records(package_path),
    )
    return {
        "ok": True,
        "package_id": package_path.name,
        "generated_path": _package_marker(repo_root, package_path / "generated"),
        **build,
        "summary_text": f"Built {build['document_count']} review documents for {package_path.name}.",
    }


def write_source(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    package_path, manifest, records = _package_context(repo_root, body.get("package_id"))
    doc_id = validate_doc_id(body.get("doc_id"))
    source_revision = str(body.get("source_revision") or "").strip()
    if not source_revision:
        raise ValueError("source_revision is required")
    if "parent_id" in body:
        raise ValueError("Docs Review does not support parent updates")
    if "source_body" not in body:
        raise ValueError("source_body is required")
    record = records.get(doc_id)
    if record is None:
        raise FileNotFoundError(f"review package document not found: {doc_id}")
    if source_revision != source_revision_for_text(record["source_text"]):
        raise ValueError("source revision is stale; reload source before rebuilding")
    front_matter_source, front_matter, _source_body = split_source_exact(record["source_text"])
    if str(front_matter.get("doc_id") or "").strip() != doc_id:
        raise ValueError("existing review source doc_id does not match requested document")
    next_source_body = normalize_source_body(body.get("source_body"))
    next_source_text = front_matter_source + next_source_body
    source_model.write_text_atomic(record["path"], next_source_text)
    try:
        default_doc_id = str(manifest.get("default_doc_id") or "").strip() or next(iter(records))
        build = build_review_package(
            repo_root,
            package_id=package_path.name,
            source_dir=package_path / "source",
            generated_dir=package_path / "generated",
            default_doc_id=default_doc_id,
            asset_records=_asset_records(package_path),
        )
    except Exception:
        source_model.write_text_atomic(record["path"], record["source_text"])
        raise
    return {
        "ok": True,
        "package_id": package_path.name,
        "doc_id": doc_id,
        "source_revision": source_revision_for_text(next_source_text),
        "rebuild": build,
        "summary_text": f"Saved and rebuilt {doc_id} inside review package {package_path.name}.",
    }
