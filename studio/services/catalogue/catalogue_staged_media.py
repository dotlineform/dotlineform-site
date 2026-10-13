"""Studio-owned prepared media and exact Work rendition identities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from catalogue_media_paths import CATALOGUE_MEDIA_ROUTE_PREFIX, configured_catalogue_media_root
from docs_artifact_locations import ArtifactLocation, EXTERNAL_LOCAL_PROVIDER
from docs_workspace_config import location_child
from pipeline_config import load_pipeline_config, media_work_files_subdir, media_mode_output_subdir


@dataclass(frozen=True)
class CatalogueStagingAssets:
    """Studio-prepared bytes; Refresh reads only the queued handoff selection."""

    root: ArtifactLocation
    work_primary: ArtifactLocation
    work_thumbnails: ArtifactLocation
    work_files: ArtifactLocation

    def url(self, location: ArtifactLocation) -> str:
        return CATALOGUE_MEDIA_ROUTE_PREFIX + location.path.relative_to(self.root.path).as_posix()


def catalogue_staging_assets(
    repo_root: Path, *, config: Mapping[str, Any] | None = None,
) -> CatalogueStagingAssets:
    """Resolve checked Projects staging using the operation's loaded policy."""
    config = load_pipeline_config(repo_root=repo_root) if config is None else config
    root = ArtifactLocation(EXTERNAL_LOCAL_PROVIDER, configured_catalogue_media_root(repo_root, config=config))
    output = media_mode_output_subdir(config, "work")
    return CatalogueStagingAssets(
        root,
        location_child(root, output / str(config["variants"]["primary"]["output_subdir"])),
        location_child(root, output / str(config["variants"]["thumb"]["output_subdir"])),
        location_child(root, media_work_files_subdir(config)),
    )


def work_image_paths(
    repo_root: Path, work_id: str, assets: Any, *, config: Mapping[str, Any] | None = None,
) -> list[Path]:
    """Derive confined exact-Work renditions, reusing the supplied operation policy."""
    if len(work_id) != 5 or not work_id.isascii() or not work_id.isdigit():
        raise ValueError("Work rendition identity must be exactly five digits")
    config = load_pipeline_config(repo_root=repo_root) if config is None else config
    return work_rendition_paths(work_id, assets, config=config)


def work_rendition_paths(work_id: str, assets: Any, *, config: Mapping[str, Any]) -> list[Path]:
    """Derive confined paths using the supplied identity and operation's media policy."""
    return [
        location_child(family, Path(f"{work_id}-{policy['suffix']}-{size}.{config['encoding']['format']}")).path
        for family, policy, sizes in (
            (assets.work_primary, config["variants"]["primary"], "widths"),
            (assets.work_thumbnails, config["variants"]["thumb"], "sizes"),
        )
        for size in policy[sizes]
    ]


def clear_staged_works(repo_root: Path, selections: Mapping[str, Mapping[str, Any]]) -> None:
    """Remove selected owned staging bytes with one policy/root resolution.

    Empty descriptors require no staging setup. Queue persistence precedes this
    cleanup; absent bytes succeed and completed removals remain on failure.
    """
    media_selections = {wid: entry for wid, entry in selections.items() if entry["image"] or entry["file_names"]}
    if not media_selections:
        return
    config = load_pipeline_config(repo_root=repo_root)
    staging = catalogue_staging_assets(repo_root, config=config)
    for work_id, selection in media_selections.items():
        if selection["image"]:
            for path in work_image_paths(repo_root, work_id, staging, config=config):
                path.unlink(missing_ok=True)
        for name in selection["file_names"]:
            location_child(staging.work_files, Path(name)).path.unlink(missing_ok=True)
