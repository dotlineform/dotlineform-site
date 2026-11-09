"""Read selected Studio Catalogue outputs and adopted authoring choices.

Regenerate owns raw Work reads. Gallery and policy consumers use Studio's
completed outputs. The picker uses the adopted Catalogue document manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit
from docs_artifact_locations import ArtifactLocation
from docs_publication_paths import confined, working_owner
from docs_workspace_config import generated_documents_path

from studio.services.catalogue.catalogue_output_paths import catalogue_workspace_config, catalogue_output_workspace, output_path
from studio.services.catalogue.catalogue_shared_changes import GALLERY_REPORT_SEARCH


def _read_generated(repo_root: Path, relative: str, *, workspace: ArtifactLocation | None = None) -> dict[str, Any]:
    try:
        location = catalogue_output_workspace(repo_root) if workspace is None else workspace
        data = output_path(location, relative).read_bytes()
        payload = json.loads(data)
    except (OSError, ValueError) as exc:
        raise ValueError("Generated Catalogue data is unavailable") from exc
    return payload


def _work_identity(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{5}", value):
        raise ValueError("An exact five-digit Catalogue Work ID is required")
    return value


def _gallery_identity(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9]{3}|[1-9][0-9]{3,})", value):
        raise ValueError("An exact Catalogue Gallery ID is required")
    return value


def _positive_integer(value: Any) -> bool:
    return type(value) is int and value > 0


def _safe_media_url(value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        return ""
    if any(char == "\\" or ord(char) <= 32 or ord(char) == 127 for char in value):
        return ""
    if value.startswith("/") and not value.startswith("//"):
        return value
    try:
        parsed = urlsplit(value)
        if parsed.scheme == "https" and parsed.hostname and parsed.username is None and parsed.password is None:
            return value
    except ValueError:
        pass
    return ""


def read_catalogue_media_config(repo_root: Path, *, workspace: ArtifactLocation | None = None) -> dict[str, Any]:
    """Read the producer's shared public policy without exposing private pipeline inputs."""
    return validate_catalogue_media_config(_read_generated(repo_root, "media-config.json", workspace=workspace))


def validate_catalogue_media_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate captured policy without reading another stage or canonical data."""
    header = payload.get("header")
    if not isinstance(header, dict) or header.get("schema") != "catalogue_media_config_v1":
        raise ValueError("Generated Catalogue media configuration is unavailable")
    primary, thumbnails = payload.get("primary", {}), payload.get("thumbnails", {})
    if not isinstance(primary, dict) or not isinstance(thumbnails, dict):
        raise ValueError("Generated Catalogue rendition policy is unavailable")
    bases = primary.get("base_urls", {})
    if not isinstance(bases, dict) or any(not _safe_media_url(bases.get(family)) or not bases[family].endswith("/")
           or any(char in bases[family] for char in "?#,") for family in ("works",)):
        raise ValueError("Generated Catalogue image bases are unsafe")
    for settings, key in ((primary, "widths"), (thumbnails, "sizes")):
        values = settings.get(key)
        if not isinstance(values, list) or not values or any(not _positive_integer(value) for value in values):
            raise ValueError("Generated Catalogue rendition sizes are unavailable")
        if not isinstance(settings.get("suffix"), str) or not re.fullmatch(r"[a-z0-9-]+", settings["suffix"]):
            raise ValueError("Generated Catalogue rendition suffix is unavailable")
    if payload.get("format") not in ("webp", "avif", "png", "jpg") or primary.get("version_query_parameter") != "v":
        raise ValueError("Generated Catalogue media format or version policy is unsupported")
    return payload


def read_catalogue_work_index(repo_root: Path, *, workspace: ArtifactLocation | None = None) -> dict[str, dict[str, Any]]:
    """Read the generated Work inventory without loading Series or by-ID records."""
    return _read_generated(repo_root, "works/works_index.json", workspace=workspace)["works"]


def read_catalogue_series_galleries_index(
    repo_root: Path, *, workspace: ArtifactLocation | None = None,
) -> dict[str, Any]:
    """Read the exact generated Series relevance map, including empty Series."""
    return _read_generated(repo_root, "series-galleries-index.json", workspace=workspace)


def read_catalogue_gallery_report_search(repo_root: Path) -> dict[str, Any]:
    return _read_generated(repo_root, GALLERY_REPORT_SEARCH)


def read_catalogue_media_targets(repo_root: Path) -> dict[str, Any]:
    """Expose the adopted Work and Studio-owned Gallery search identities."""
    workspace = catalogue_workspace_config(repo_root)
    catalogue_documents = generated_documents_path(working_owner(workspace, "catalogue"))
    manifest = json.loads(confined(catalogue_documents, "manage-manifest.json").read_bytes())
    targets = []
    for work in manifest["docs"]:
        targets.append({
            "family": "catalogue", "target_type": "work", "target_id": work["doc_id"],
            "title": work["title"],
            "meta": [],
        })
    galleries = _read_generated(repo_root, "galleries/galleries_index.json", workspace=workspace.catalogue.working)["galleries"]
    for gallery_id, record in galleries.items():
        targets.append({
            "family": "catalogue", "target_type": "gallery", "target_id": gallery_id,
            "title": record["title"], "meta": [],
        })
    return {"ok": True, "schema_version": "docs_semantic_token_target_lookup_v2", "targets": targets}


def read_catalogue_work(repo_root: Path, work_id: str, *, workspace: ArtifactLocation | None = None) -> dict[str, Any]:
    """Read one selected Studio Work for Regenerate."""
    return _read_generated(repo_root, f"works/index/{work_id}.json", workspace=workspace)


def read_catalogue_gallery(repo_root: Path, gallery_id: str, *, workspace: ArtifactLocation | None = None) -> dict[str, Any]:
    """Read one exact Gallery and its ordered Work references without member reads."""
    gallery_id = _gallery_identity(gallery_id)
    return _read_generated(repo_root, f"galleries/index/{gallery_id}.json", workspace=workspace)
