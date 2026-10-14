"""Own the private Series–Gallery report projection saved by Refresh."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from studio.services.catalogue.catalogue_series_galleries import CatalogueSeriesGalleries
from studio.services.catalogue.catalogue_series_galleries_index import definition_cell


METADATA_PATH = "reports/series-galleries/metadata.json"
REPORT_SCHEMA = "catalogue_series_galleries_report_v2"


def _row_key(row: dict[str, Any]) -> tuple[str | None, str | None]:
    return (row["series"]["series_id"] if row["series"] else None,
            row["gallery"]["gallery_id"] if row["gallery"] else None)


def _sort_key(identity: tuple[str | None, str | None]) -> tuple[bool, str, str]:
    return identity[0] is None, identity[0] or "", identity[1] or ""


def _payload(rows: Mapping[tuple[str | None, str | None], Any], timestamp: str) -> dict[str, Any]:
    return {"header": {"schema": REPORT_SCHEMA, "generated_at_utc": timestamp},
            "rows": [rows[key] for key in sorted(rows, key=_sort_key)]}


def series_galleries_report_payload(
    series: Mapping[str, Any], galleries: Mapping[str, Any],
    series_galleries: Mapping[str, list[dict[str, str]]], *, timestamp: str,
) -> dict[str, Any]:
    """Project validated definitions and the same relationships as the public index.

    Every pair has one row. Empty Series and unassociated Galleries have one
    row with a null opposite cell; no Work-membership relationship is inferred.
    """
    rows = []
    associated_gallery_ids = set()
    for series_id in sorted(series):
        label = definition_cell("series", series_id, series)
        related = series_galleries[series_id]
        if not related:
            rows.append({"series": label, "gallery": None})
        for gallery in related:
            rows.append({"series": label, "gallery": dict(gallery)})
            associated_gallery_ids.add(gallery["gallery_id"])
    for gallery_id in sorted(galleries.keys() - associated_gallery_ids):
        rows.append({"series": None, "gallery": definition_cell("gallery", gallery_id, galleries)})
    return _payload({_row_key(row): row for row in rows}, timestamp)


def merge_series_galleries_report(
    path: Path, series: Mapping[str, Any], galleries: Mapping[str, Any], pairs: CatalogueSeriesGalleries,
    *, current_series: Iterable[str], deleted_series: Iterable[str], current_galleries: Iterable[str],
    deleted_galleries: Iterable[str], timestamp: str,
) -> dict[str, Any] | None:
    """Replace rows touching supplied endpoints, preserving unrelated pair rows.

    Current empty Series and unassociated Galleries get explicit placeholders.
    One relationship pass looks up only the selected current Gallery endpoints.
    Parse saved rows without auditing their contents or the queued endpoints.
    Unreadable output stops without invoking full generation.
    """
    current_s, deleted_s = set(current_series), set(deleted_series)
    current_g, deleted_g = set(current_galleries), set(deleted_galleries)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = {_row_key(row): row for row in payload["rows"]}
    except (OSError, ValueError) as error:
        raise ValueError(f"Series–Gallery report is unavailable; run explicit relationship maintenance: {error}") from error
    selected_s, selected_g = current_s | deleted_s, current_g | deleted_g
    previous = {key: row for key, row in rows.items() if key[0] in selected_s or key[1] in selected_g}
    replacements = {}
    for series_id in sorted(current_s):
        label = definition_cell("series", series_id, series)
        gallery_ids = pairs.pairs_by_series.get(series_id, ())
        if not gallery_ids:
            replacements[(series_id, None)] = {"series": label, "gallery": None}
        for gallery_id in gallery_ids:
            replacements[(series_id, gallery_id)] = {"series": label,
                                                    "gallery": definition_cell("gallery", gallery_id, galleries)}
    related = {gallery_id: [] for gallery_id in current_g}
    if related:
        for series_id, gallery_ids in pairs.pairs_by_series.items():
            for gallery_id in gallery_ids:
                if gallery_id in related:
                    related[gallery_id].append(series_id)
    for gallery_id, series_ids in related.items():
        label = definition_cell("gallery", gallery_id, galleries)
        if not series_ids:
            replacements[(None, gallery_id)] = {"series": None, "gallery": label}
        for series_id in series_ids:
            key = (series_id, gallery_id)
            if key not in replacements:
                replacements[key] = {"series": definition_cell("series", series_id, series), "gallery": label}
    if previous == replacements:
        return None
    for key in previous:
        del rows[key]
    rows.update(replacements)
    return _payload(rows, timestamp)
