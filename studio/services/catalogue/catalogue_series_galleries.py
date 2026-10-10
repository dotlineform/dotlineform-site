"""Exact canonical Series-Gallery relevance, independent of Work membership."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_galleries import validate_gallery_id
from catalogue.series_ids import normalize_series_id


SERIES_GALLERIES_FILE = "series-galleries.json"
SERIES_GALLERIES_SCHEMA = "catalogue_source_series_galleries_v1"


@dataclass(frozen=True)
class CatalogueSeriesGalleries:
    pairs_by_series: dict[str, tuple[str, ...]]

    def payload(self) -> dict[str, Any]:
        return {
            "header": {
                "schema": SERIES_GALLERIES_SCHEMA,
                "count": sum(len(ids) for ids in self.pairs_by_series.values()),
            },
            "pairs_by_series": {sid: list(ids) for sid, ids in sorted(self.pairs_by_series.items())},
        }


def related_series_ids(data: CatalogueSeriesGalleries, gallery_id: str) -> list[str]:
    return [sid for sid, ids in data.pairs_by_series.items() if gallery_id in ids]


def with_gallery_relation(
    data: CatalogueSeriesGalleries, series_id: str, gallery_id: str, related: bool,
) -> CatalogueSeriesGalleries:
    pairs = dict(data.pairs_by_series)
    gallery_ids = set(pairs.get(series_id, ()))
    if related:
        gallery_ids.add(gallery_id)
    else:
        gallery_ids.discard(gallery_id)
    if gallery_ids:
        pairs[series_id] = tuple(sorted(gallery_ids))
    else:
        pairs.pop(series_id, None)
    return CatalogueSeriesGalleries(dict(sorted(pairs.items())))


def without_gallery(data: CatalogueSeriesGalleries, gallery_id: str) -> CatalogueSeriesGalleries:
    pairs = {
        sid: remaining for sid, ids in data.pairs_by_series.items()
        if (remaining := tuple(gid for gid in ids if gid != gallery_id))
    }
    return CatalogueSeriesGalleries(pairs)


def without_series(data: CatalogueSeriesGalleries, series_id: str) -> CatalogueSeriesGalleries:
    return CatalogueSeriesGalleries({sid: ids for sid, ids in data.pairs_by_series.items() if sid != series_id})


def validate_series_galleries(
    data: CatalogueSeriesGalleries,
    series: Mapping[str, Any],
    galleries: Mapping[str, Any],
) -> None:
    """Require sorted, unique pairs with current exact definition identities."""
    if list(data.pairs_by_series) != sorted(data.pairs_by_series):
        raise ValueError("Canonical Series-Gallery Series IDs must be sorted")
    for series_id, gallery_ids in data.pairs_by_series.items():
        if not isinstance(series_id, str) or normalize_series_id(series_id) != series_id:
            raise ValueError(f"Invalid exact Series-Gallery Series ID: {series_id!r}")
        series_record = series.get(series_id)
        if not isinstance(series_record, dict) or series_record.get("series_id") != series_id:
            raise ValueError(f"Series-Gallery pair references unknown Series {series_id!r}")
        if not isinstance(gallery_ids, tuple) or not gallery_ids:
            raise ValueError(f"Series {series_id} must have one or more Gallery pairs")
        if any(not isinstance(gallery_id, str) for gallery_id in gallery_ids):
            raise ValueError(f"Series {series_id} Gallery IDs must be strings")
        if list(gallery_ids) != sorted(set(gallery_ids)):
            raise ValueError(f"Series {series_id} Gallery IDs must be sorted and unique")
        for gallery_id in gallery_ids:
            validate_gallery_id(gallery_id)
            gallery_record = galleries.get(gallery_id)
            if not isinstance(gallery_record, dict) or gallery_record.get("gallery_id") != gallery_id:
                raise ValueError(f"Series-Gallery pair references unknown Gallery {gallery_id!r}")


def _unique_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate canonical Series-Gallery JSON key: {key}")
        result[key] = value
    return result


def read_series_galleries(source_dir: Path) -> CatalogueSeriesGalleries:
    """Load the pair authority without auditing every canonical relationship."""
    payload = json.loads(
        (source_dir / SERIES_GALLERIES_FILE).read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object_keys,
    )
    if not isinstance(payload, dict) or set(payload) != {"header", "pairs_by_series"}:
        raise ValueError("Invalid canonical Series-Gallery payload")
    header, pairs = payload["header"], payload["pairs_by_series"]
    if not isinstance(header, dict) or set(header) != {"schema", "count"} or not isinstance(pairs, dict):
        raise ValueError("Invalid canonical Series-Gallery objects")
    if header["schema"] != SERIES_GALLERIES_SCHEMA or type(header["count"]) is not int:
        raise ValueError("Invalid canonical Series-Gallery header")
    pair_map = {}
    count = 0
    for sid, ids in pairs.items():
        if not isinstance(ids, list):
            raise ValueError("Series-Gallery pairs must be arrays of exact Gallery IDs")
        pair_map[sid] = tuple(ids)
        count += len(ids)
    if header["count"] != count:
        raise ValueError("Canonical Series-Gallery pair count does not match header")
    return CatalogueSeriesGalleries(pair_map)
