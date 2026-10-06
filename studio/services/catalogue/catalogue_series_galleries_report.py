"""Own the private saved Series–Gallery report projection and read contract."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .catalogue_generation_common import compute_payload_version


METADATA_PATH = "reports/series-galleries/metadata.json"
REPORT_SCHEMA = "catalogue_series_galleries_report_v1"


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
        label = {"series_id": series_id, "title": series[series_id]["title"]}
        related = series_galleries[series_id]
        if not related:
            rows.append({"series": label, "gallery": None})
        for gallery in related:
            rows.append({"series": label, "gallery": dict(gallery)})
            associated_gallery_ids.add(gallery["gallery_id"])
    for gallery_id in sorted(galleries.keys() - associated_gallery_ids):
        rows.append({"series": None, "gallery": dict(galleries[gallery_id])})
    return {
        "header": {
            "schema": REPORT_SCHEMA,
            "version": compute_payload_version({"schema": REPORT_SCHEMA, "rows": rows}),
            "generated_at_utc": timestamp, "count": len(rows),
        },
        "rows": rows,
    }


def validate_series_galleries_report(payload: Any) -> dict[str, Any]:
    """Validate only the saved report, without reading canonical records or indexes."""
    if not isinstance(payload, dict) or set(payload) != {"header", "rows"}:
        raise ValueError("Invalid saved Series–Gallery report")
    header, rows = payload["header"], payload["rows"]
    if (not isinstance(header, dict) or set(header) != {"schema", "version", "generated_at_utc", "count"}
            or header["schema"] != REPORT_SCHEMA or not isinstance(rows, list)
            or type(header["count"]) is not int or header["count"] != len(rows)
            or not isinstance(header["version"], str) or not re.fullmatch(r"blake2b-[0-9a-f]{32}", header["version"])
            or not isinstance(header["generated_at_utc"], str) or not header["generated_at_utc"]):
        raise ValueError("Invalid saved Series–Gallery report header")
    identities = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"series", "gallery"} or not any(row.values()):
            raise ValueError("Invalid saved Series–Gallery report row")
        pair = []
        for kind, pattern in (("series", r"[0-9]{3}"), ("gallery", r"(?:[0-9]{3}|[1-9][0-9]{3,})")):
            cell = row[kind]
            if cell is None:
                pair.append(None)
                continue
            key = f"{kind}_id"
            if (not isinstance(cell, dict) or set(cell) != {key, "title"}
                    or not isinstance(cell[key], str) or not re.fullmatch(pattern, cell[key])
                    or not isinstance(cell["title"], str) or not cell["title"].strip()):
                raise ValueError(f"Invalid saved Series–Gallery report {kind}")
            pair.append(cell[key])
        identity = tuple(pair)
        if identity in identities:
            raise ValueError("Duplicate saved Series–Gallery report row")
        identities.add(identity)
    return payload
