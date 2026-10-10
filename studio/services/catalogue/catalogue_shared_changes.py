"""Known Gallery/Series effects and explicit shared Catalogue output selection."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from docs_catalogue_artifacts import load_catalogue_artifact_inventory
from studio.services.catalogue.catalogue_galleries import validate_gallery_id
from studio.services.catalogue.series_ids import normalize_series_id


SHARED_FIELDS = ("current_galleries", "deleted_galleries", "current_series", "deleted_series", "shared_outputs")
WORK_INDEX = "works/works_index.json"
GALLERY_INDEX = "galleries/galleries_index.json"
RELATIONSHIP_INDEX = "series-galleries-index.json"
RELATIONSHIP_REPORT = "reports/series-galleries/metadata.json"


def empty_shared_changes() -> dict[str, list[str]]:
    return {field: [] for field in SHARED_FIELDS}


def shared_changes(pending: Mapping[str, Any]) -> dict[str, list[str]]:
    return {field: list(pending[field]) for field in SHARED_FIELDS}


def public_shared_outputs(repo_root: Path) -> set[str]:
    return {path.as_posix() for path in load_catalogue_artifact_inventory(repo_root).system_files}


def validate_shared_changes(repo_root: Path, changes: Any, *, publishing: bool) -> None:
    if not isinstance(changes, dict) or set(changes) != set(SHARED_FIELDS):
        raise ValueError("Catalogue shared selection requires Gallery/Series identities and shared_outputs")
    allowed = public_shared_outputs(repo_root) | (set() if publishing else {RELATIONSHIP_REPORT})
    for field in SHARED_FIELDS:
        values = changes[field]
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError(f"Catalogue {field} must be an array of strings")
        if values != sorted(set(values)):
            raise ValueError(f"Catalogue {field} must be sorted and distinct")
        for value in values:
            if field.endswith("galleries"):
                validate_gallery_id(value)
            elif field.endswith("series"):
                if normalize_series_id(value) != value:
                    raise ValueError("Catalogue shared selection requires exact Series identities")
            elif value not in allowed:
                raise ValueError(f"Unknown Catalogue shared output: {value}")
    for family in ("galleries", "series"):
        if set(changes[f"current_{family}"]) & set(changes[f"deleted_{family}"]):
            raise ValueError(f"A queued {family} identity cannot be current and deleted")


def merge_shared_changes(pending: dict[str, Any], changes: Mapping[str, list[str]]) -> None:
    for family in ("galleries", "series"):
        current, deleted = f"current_{family}", f"deleted_{family}"
        pending[current] = sorted((set(pending[current]) | set(changes[current])) - set(changes[deleted]))
        pending[deleted] = sorted((set(pending[deleted]) | set(changes[deleted])) - set(changes[current]))
    pending["shared_outputs"] = sorted(set(pending["shared_outputs"]) | set(changes["shared_outputs"]))


def work_shared_changes(
    previous: Mapping[str, Mapping[str, Any]], current: Mapping[str, Mapping[str, Any]],
    previous_memberships: Mapping[str, list[str]], current_memberships: Mapping[str, list[str]],
    work_ids: Iterable[str],
) -> dict[str, list[str]]:
    """Select from the mutation's exact candidates and already loaded relationships."""
    galleries, series, outputs = set(), set(), set()
    for work_id in work_ids:
        old, new = previous.get(work_id), current.get(work_id)
        before, after = set(previous_memberships.get(work_id, [])), set(current_memberships.get(work_id, []))
        identity_changed = old is None or new is None
        member_changed = identity_changed or any(
            (old or {}).get(field) != (new or {}).get(field) for field in ("title", "year", "year_display")
        )
        if before != after or member_changed:
            galleries.update(before | after)
        if identity_changed or (old or {}).get("title") != (new or {}).get("title"):
            outputs.add(WORK_INDEX)
        if identity_changed or (old or {}).get("series_id") != (new or {}).get("series_id"):
            series.update(record["series_id"] for record in (old, new) if record and record.get("series_id"))
    return {**empty_shared_changes(), "current_galleries": sorted(galleries),
            "current_series": sorted(series), "shared_outputs": sorted(outputs)}
