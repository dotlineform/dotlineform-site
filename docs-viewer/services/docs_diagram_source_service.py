#!/usr/bin/env python3
"""Logical Mermaid source discovery and opening for rendered Document Info."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import docs_source_model as source_model
from docs_artifact_locations import (
    ArtifactLocation,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
    local_artifact_path,
    normalize_artifact_identity,
)
from docs_import_common import humanize
from docs_management_context import log_event
from docs_management_source_service import resolve_scope_doc
from docs_media_inventory import MEDIA_REFERENCE_PATTERN
from docs_scope_config import load_docs_scope_configs


def _request_doc_id(value: Any) -> str:
    doc_id = str(value or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")
    return doc_id


def _verified_diagram_sources(repo_root: Path, scope: str, doc_id: str) -> list[dict[str, str]]:
    config = load_docs_scope_configs(repo_root)[scope]
    build = config.source.build_media.get("mermaid")
    published_media = config.published.media.get("svg")
    if (
        build is None
        or build.producer != "mermaid"
        or build.publishes_to != "svg"
        or published_media is None
        or "mermaid" not in published_media.build_inputs
    ):
        return []

    target = resolve_scope_doc(repo_root, scope, doc_id)
    source_text = target.path.read_text(encoding="utf-8")
    reference_prefix = published_media.reference_prefix.as_posix().rstrip("/")
    published_identities: set[str] = set()
    for match in MEDIA_REFERENCE_PATTERN.finditer(source_text):
        logical_path = match.group("path").lstrip("/")
        prefix = f"{reference_prefix}/"
        if not logical_path.startswith(prefix):
            continue
        identity = normalize_artifact_identity(logical_path.removeprefix(prefix))
        if Path(identity).suffix.lower() == ".svg":
            published_identities.add(identity)

    source_adapter = artifact_location_adapter(
        repo_root,
        ArtifactLocation(
            provider=config.source.location.provider,
            path=config.source.location.path / build.path,
        ),
    )
    remote_client = authenticated_remote_client_for_locations(repo_root, [published_media.location])
    published_adapter = artifact_location_adapter(
        repo_root,
        published_media.location,
        served_path_prefix=published_media.served_path_prefix,
        remote_client=remote_client,
    )
    records: list[dict[str, str]] = []
    for published_identity in sorted(published_identities):
        source_identity = Path(published_identity).with_suffix(".mmd").as_posix()
        try:
            source_bytes = source_adapter.read(source_identity)
            published_bytes = published_adapter.read(published_identity)
        except FileNotFoundError:
            continue
        if not source_adapter.verify_bytes(source_identity, source_bytes):
            continue
        if not published_adapter.verify_bytes(published_identity, published_bytes):
            continue
        records.append(
            {
                "label": humanize(Path(source_identity).stem),
                "media_identity": f"{reference_prefix}/{published_identity}",
                "source_identity": source_identity,
            }
        )
    return records


def list_diagram_sources(repo_root: Path, params: dict[str, list[str]]) -> dict[str, object]:
    scope = source_model.normalize_scope((params.get("scope") or [""])[0])
    doc_id = _request_doc_id((params.get("doc_id") or params.get("doc") or [""])[0])
    target = resolve_scope_doc(repo_root, scope, doc_id)
    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "sources": _verified_diagram_sources(repo_root, scope, target.doc_id),
    }


def open_diagram_source(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
) -> dict[str, object]:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = _request_doc_id(body.get("doc_id"))
    media_identity = normalize_artifact_identity(str(body.get("media_identity") or "").strip())
    editor = str(body.get("editor") or "vscode").strip().lower()
    if editor != "vscode":
        raise ValueError("editor must be `vscode`")

    records = _verified_diagram_sources(repo_root, scope, doc_id)
    target_record = next(
        (record for record in records if record["media_identity"] == media_identity),
        None,
    )
    if target_record is None:
        raise FileNotFoundError("verified Mermaid source is not registered by this document")

    config = load_docs_scope_configs(repo_root)[scope]
    build = config.source.build_media["mermaid"]
    source_location = ArtifactLocation(
        provider=config.source.location.provider,
        path=config.source.location.path / build.path,
    )
    source_path = local_artifact_path(repo_root, source_location, target_record["source_identity"])
    if source_path is None or not source_path.is_file():
        raise FileNotFoundError("verified Mermaid source is not locally openable")

    if not dry_run:
        command = ["open", "-a", "Visual Studio Code", str(source_path)]
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("VS Code could not open the verified Mermaid source")
        log_event(
            repo_root,
            "docs-open-diagram-source",
            {
                "scope": scope,
                "doc_id": doc_id,
                "media_identity": target_record["media_identity"],
                "source_identity": target_record["source_identity"],
                "editor": editor,
            },
        )

    return {
        "ok": True,
        "scope": scope,
        "doc_id": doc_id,
        "media_identity": target_record["media_identity"],
        "source_identity": target_record["source_identity"],
        "editor": editor,
        "summary_text": f"Opened {target_record['source_identity']} in VS Code.",
        "dry_run": dry_run,
    }


__all__ = ["list_diagram_sources", "open_diagram_source"]
