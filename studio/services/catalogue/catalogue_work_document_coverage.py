"""Own Refresh's private Series/member-Work input for documentation coverage."""

from __future__ import annotations

import re
from typing import Any, Mapping


MANIFEST_PATH = "reports/work-document-coverage/manifest.json"
MANIFEST_SCHEMA = "catalogue_work_document_coverage_v1"


def work_document_coverage_manifest(
    series: Mapping[str, Any], works: Mapping[str, Any], *, timestamp: str,
) -> dict[str, Any]:
    """Project validated Catalogue inputs, including Series without member Works.

    Only Series labels and membership are persisted. Context document coverage
    remains a browser join against its independently generated management manifest.
    """
    rows = {
        series_id: {"series_id": series_id, "title": record["title"], "work_ids": []}
        for series_id, record in sorted(series.items())
    }
    for work_id, record in sorted(works.items()):
        if series_id := record.get("series_id"):
            rows[series_id]["work_ids"].append(work_id)
    return {
        "header": {"schema": MANIFEST_SCHEMA, "generated_at_utc": timestamp},
        "series": list(rows.values()),
    }


def validate_work_document_coverage_manifest(payload: Any) -> dict[str, Any]:
    """Validate saved minimal input without consulting canonical or public data."""
    if not isinstance(payload, dict) or set(payload) != {"header", "series"}:
        raise ValueError("Invalid saved Work Document Coverage manifest")
    header, rows = payload["header"], payload["series"]
    if (not isinstance(header, dict) or set(header) != {"schema", "generated_at_utc"}
            or header["schema"] != MANIFEST_SCHEMA or not isinstance(rows, list)
            or not isinstance(header["generated_at_utc"], str) or not header["generated_at_utc"]):
        raise ValueError("Invalid saved Work Document Coverage manifest header")
    previous_series = ""
    seen_works = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"series_id", "title", "work_ids"}
                or not isinstance(row["series_id"], str) or not re.fullmatch(r"[0-9]{3}", row["series_id"])
                or row["series_id"] <= previous_series
                or not isinstance(row["title"], str) or not row["title"].strip()
                or not isinstance(row["work_ids"], list)):
            raise ValueError("Invalid saved Work Document Coverage Series")
        previous_series = row["series_id"]
        previous_work = ""
        for work_id in row["work_ids"]:
            if (not isinstance(work_id, str) or not re.fullmatch(r"[0-9]{5}", work_id)
                    or work_id <= previous_work or work_id in seen_works):
                raise ValueError("Invalid saved Work Document Coverage membership")
            previous_work = work_id
            seen_works.add(work_id)
    return payload
