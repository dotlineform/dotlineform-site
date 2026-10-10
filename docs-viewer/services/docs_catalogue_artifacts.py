"""One design-time selection of Catalogue JSON for preparation and distribution.

Selection reads exact configured artifacts from an explicit stage and preserves
their bytes. It neither joins canonical data nor discovers queue membership.
Missing or malformed selected JSON fails; complete snapshots require system files.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from docs_workspace_config import DocsCatalogueConfig, location_child, safe_relative_path
from docs_catalogue_media import (
    validate_catalogue_series_galleries_index,
)


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
    catalogue: DocsCatalogueConfig, inventory: CatalogueArtifactInventory, *, stage: str, identities: Iterable[Path],
) -> dict[str, bytes]:
    """Read selected JSON unchanged, keyed by its Catalogue-relative identity.

    The caller owns the snapshot/plan revision over these bytes. Asset bytes and
    their versions are outside this inventory. Reads never create missing roots
    or fall back to another stage; symlinks cannot redirect an artifact.
    """
    root = catalogue.stage_location(stage)
    selected = set(identities)
    if any(path not in inventory.system_files and not (
        path.parent in inventory.by_id_directories and path.suffix == ".json"
    ) for path in selected):
        raise ValueError("Catalogue selection is outside the public artifact inventory")
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
        if identity == "series-galleries-index.json":
            validate_catalogue_series_galleries_index(payload)
        if relative.parent == Path("galleries/index") and (
            not isinstance(payload.get("gallery"), dict) or not isinstance(payload.get("header"), dict)
            or payload["gallery"].get("gallery_id") != relative.stem or payload["header"].get("gallery_id") != relative.stem
        ):
            raise ValueError(f"Catalogue Gallery identity does not match {identity}")
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
