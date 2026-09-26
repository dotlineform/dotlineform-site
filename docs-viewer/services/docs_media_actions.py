"""Local actions for exact configured Docs media targets."""

from pathlib import Path
from typing import Any

from docs_artifact_locations import local_artifact_path
from docs_local_files import open_in_finder
from docs_workspace_config import DocsStageConfig, DocsCollectionConfig, load_docs_media_owner


def _source_path(
    repo_root: Path, config: DocsStageConfig | DocsCollectionConfig,
    role: str, media_type: str, identity: str,
) -> Path:
    if role == "build-source":
        media = config.media.build_sources.get(media_type)
        location = media.location if media is not None else None
    elif role == "source":
        media = config.media.types.get(media_type)
        location = media.asset_location if media is not None else None
    else:
        raise ValueError(f"unsupported Docs media inventory role: {role}")
    if location is None:
        raise ValueError("Docs media type is not configured for this collection and role")
    path = local_artifact_path(repo_root, location, identity)
    if path is None or not path.is_file():
        raise FileNotFoundError("Docs media source file is unavailable")
    return path


def open_media_source(
    repo_root: Path, body: dict[str, Any], *, dry_run: bool = False,
) -> dict[str, object]:
    """Reveal one exact configured Docs media file without accepting a filesystem path."""
    if set(body) != {"stage", "collection", "role", "media_type", "identity"} or any(
        not isinstance(value, str) or value != value.strip() or (not value and key != "collection")
        for key, value in body.items()
    ):
        raise ValueError("Docs media requires an exact stage, collection, role, media type and identity")
    config = load_docs_media_owner(repo_root, body["stage"], body["collection"])
    path = _source_path(repo_root, config, body["role"], body["media_type"], body["identity"])
    open_in_finder(
        repo_root, path, reveal=True, dry_run=dry_run,
        failure_message="Docs media source could not be revealed in Finder",
    )
    return {"ok": True, **body, "dry_run": dry_run,
            "summary_text": "Docs media source validated." if dry_run else "Docs media source revealed in Finder."}
