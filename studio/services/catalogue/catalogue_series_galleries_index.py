"""Own saved Series–Gallery links and selected Series-row merging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from studio.services.catalogue.catalogue_galleries import validate_gallery_id
from studio.services.catalogue.catalogue_series_galleries import CatalogueSeriesGalleries
from studio.services.catalogue.series_ids import normalize_series_id


INDEX_SCHEMA = "catalogue_series_galleries_index_v2"


def exact_series_id(value: Any) -> str:
    if not isinstance(value, str) or normalize_series_id(value) != value:
        raise ValueError("Series–Gallery output requires an exact Series identity")
    return value


def definition_cell(kind: str, identity: str, definitions: Mapping[str, Any]) -> dict[str, str]:
    """Project the ID/title facts shared by relationship links and report cells."""
    field = f"{kind}_id"
    source = definitions[identity]
    return {field: identity, "title": source["title"]}


def series_gallery_links(
    series_id: str, galleries: Mapping[str, Any],
    pairs: CatalogueSeriesGalleries,
) -> list[dict[str, str]]:
    return [definition_cell("gallery", gallery_id, galleries)
            for gallery_id in pairs.pairs_by_series.get(series_id, ())]


def series_galleries_index_payload(mapping: Mapping[str, Any], *, timestamp: str) -> dict[str, Any]:
    return {"header": {"schema": INDEX_SCHEMA, "generated_at_utc": timestamp},
            "series_galleries": dict(sorted(mapping.items()))}


def validate_catalogue_series_galleries_index(payload: Any) -> dict[str, Any]:
    """Validate saved identities/links without a hash or canonical join."""
    if not isinstance(payload, dict) or set(payload) != {"header", "series_galleries"}:
        raise ValueError("Invalid saved Series–Gallery index envelope")
    header, mapping = payload["header"], payload["series_galleries"]
    if (not isinstance(header, dict) or set(header) != {"schema", "generated_at_utc"}
            or header["schema"] != INDEX_SCHEMA or not isinstance(mapping, dict)
            or not isinstance(header["generated_at_utc"], str) or not header["generated_at_utc"].strip()):
        raise ValueError("Invalid saved Series–Gallery index header; run explicit relationship maintenance")
    previous_series = ""
    for series_id, links in mapping.items():
        exact_series_id(series_id)
        if series_id <= previous_series or not isinstance(links, list):
            raise ValueError("Series–Gallery index Series entries must be distinct and ordered")
        previous_series = series_id
        previous_gallery = ""
        for link in links:
            if not isinstance(link, dict) or set(link) != {"gallery_id", "title"}:
                raise ValueError("Invalid saved Series–Gallery link")
            validate_gallery_id(link["gallery_id"])
            if (link["gallery_id"] <= previous_gallery
                    or not isinstance(link["title"], str) or not link["title"].strip()):
                raise ValueError("Series–Gallery links need titles and distinct ascending identities")
            previous_gallery = link["gallery_id"]
    return payload


def merge_series_galleries_index(
    path: Path, galleries: Mapping[str, Any], pairs: CatalogueSeriesGalleries,
    *, current_ids: Iterable[str], deleted_ids: Iterable[str], timestamp: str,
) -> dict[str, Any] | None:
    current, deleted = set(current_ids), set(deleted_ids)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Series–Gallery index is unavailable; run explicit relationship maintenance: {error}") from error
    mapping = payload["series_galleries"]
    changed = False
    for series_id in sorted(current):
        links = series_gallery_links(series_id, galleries, pairs)
        if mapping.get(series_id) != links:
            mapping[series_id] = links
            changed = True
    for series_id in sorted(deleted):
        if series_id in mapping:
            del mapping[series_id]
            changed = True
    return series_galleries_index_payload(mapping, timestamp=timestamp) if changed else None
