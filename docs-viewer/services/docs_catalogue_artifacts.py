"""One design-time selection of Catalogue JSON for preparation and distribution.

Selection reads an explicit stage and preserves its bytes. It neither joins
canonical data nor filters by document eligibility. Unknown files are excluded;
required directories/system files and malformed selected JSON fail visibly.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from docs_workspace_config import DocsCatalogueConfig, DocsWorkspaceConfig, location_child, safe_relative_path
from docs_catalogue_media import catalogue_media_record, validate_catalogue_media_config


CONFIG_REL_PATH = Path("docs-viewer/config/workspace/catalogue-artifacts.json")
SCHEMA_VERSION = "docs_catalogue_artifacts_v1"


@dataclass(frozen=True)
class CatalogueArtifactInventory:
    by_id_directories: tuple[Path, ...]
    system_files: tuple[Path, ...]


def load_catalogue_artifact_inventory(repo_root: Path) -> CatalogueArtifactInventory:
    """Read the explicit allowlist; no runtime directory discovery expands it."""
    payload = json.loads((repo_root / CONFIG_REL_PATH).read_bytes())
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "by_id_directories", "system_files"}:
        raise ValueError("Catalogue inventory must declare schema_version, by_id_directories and system_files")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"Catalogue inventory schema_version must be {SCHEMA_VERSION}")
    paths = {}
    for key in ("by_id_directories", "system_files"):
        entries = payload[key]
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"Catalogue inventory {key} must be a non-empty array")
        paths[key] = tuple(safe_relative_path(entry, field=f"Catalogue inventory {key}") for entry in entries)
    all_paths = (*paths["by_id_directories"], *paths["system_files"])
    for index, path in enumerate(all_paths):
        if any(path.is_relative_to(other) or other.is_relative_to(path) for other in all_paths[index + 1:]):
            raise ValueError("Catalogue inventory entries must not overlap or repeat")
    if any(path.suffix != ".json" for path in paths["system_files"]):
        raise ValueError("Catalogue inventory system files must be JSON")
    return CatalogueArtifactInventory(**paths)


def read_catalogue_artifacts(
    catalogue: DocsCatalogueConfig, inventory: CatalogueArtifactInventory, *, stage: str,
) -> dict[str, bytes]:
    """Read selected JSON unchanged, keyed by its Catalogue-relative identity.

    The caller owns the snapshot/plan revision over these bytes. Asset bytes and
    their versions are outside this inventory. Reads never create missing roots
    or fall back to another stage; symlinks cannot redirect an artifact.
    """
    root = catalogue.stage_location(stage)
    selected = list(inventory.system_files)
    for relative in inventory.by_id_directories:
        directory = location_child(root, relative).path
        if not directory.is_dir():
            raise ValueError(f"Catalogue {stage} directory is unavailable: {relative.as_posix()}")
        selected.extend(relative / entry.name for entry in sorted(directory.iterdir()) if entry.suffix == ".json")
    result = {}
    for relative in sorted(selected):
        identity = relative.as_posix()
        path = location_child(root, relative).path
        try:
            data = path.read_bytes()
            payload = json.loads(data)
        except (OSError, ValueError) as exc:
            raise ValueError(f"Catalogue {stage} JSON is unavailable or invalid: {identity}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Catalogue {stage} JSON must be an object: {identity}")
        result[identity] = data
    return result


def select_catalogue_artifacts(
    files: dict[str, bytes], inventory: CatalogueArtifactInventory,
) -> dict[str, bytes]:
    """Select declared snapshot/repository JSON without expanding its ownership."""
    selected = {
        identity: data for identity, data in files.items()
        if Path(identity) in inventory.system_files
        or Path(identity).parent in inventory.by_id_directories and Path(identity).suffix == ".json"
    }
    missing = set(path.as_posix() for path in inventory.system_files) - selected.keys()
    if missing:
        raise ValueError("Required Catalogue JSON is missing: " + ", ".join(sorted(missing)))
    return selected


def catalogue_asset_references(workspace: DocsWorkspaceConfig, files: dict[str, bytes]) -> list[str]:
    """Derive exact current asset identities solely from captured Catalogue JSON."""
    policy = validate_catalogue_media_config(json.loads(files["media-config.json"]))
    assets = workspace.assets
    references = set()
    for identity, data in files.items():
        path = Path(identity)
        if path.parent != Path("works/index") or path.suffix != ".json":
            continue
        payload = json.loads(data)
        work = payload.get("work")
        if not isinstance(work, dict) or work.get("work_id") != path.stem:
            raise ValueError(f"Catalogue Work identity does not match {identity}")
        image_fields = ("width_px", "height_px", "media_version")
        if any(field in work for field in image_fields):
            catalogue_media_record(payload, path.stem)
            for family, settings, size_key in (
                (assets.work_primary, policy["primary"], "widths"),
                (assets.work_thumbnails, policy["thumbnails"], "sizes"),
            ):
                prefix = family.path.relative_to(assets.root.path)
                for size in settings[size_key]:
                    references.add((prefix / f"{path.stem}-{settings['suffix']}-{size}.{policy['format']}").as_posix())
        for download in work.get("downloads", []):
            filename = safe_relative_path(download["filename"], field="Catalogue download filename")
            if len(filename.parts) != 1:
                raise ValueError(f"Catalogue download filename must be a direct file: {identity}")
            references.add((assets.work_files.path.relative_to(assets.root.path) / filename).as_posix())
    for identity in sorted(references):
        if not assets.resolve_reference(identity).path.is_file():
            raise FileNotFoundError(f"Required Catalogue asset is missing: {identity}")
    return sorted(references)
