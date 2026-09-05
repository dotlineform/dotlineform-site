"""Read generated Series membership for one exact managed document's subject."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping

from docs_document_subjects import normalize_authoring_subject
from docs_management_document_target import resolve_managed_document_target
from studio.shared.python.projects_directories import configured_projects_base


REPORT_SCHEMA = "docs_series_works_report_v1"


def series_work_rows(payload: Mapping[str, Any], series_id: str) -> dict[str, Any]:
    """Project the generated member order and identifying fields, without status filtering."""

    series = payload.get("series", {})
    if not isinstance(series, dict) or series.get("series_id") != series_id:
        raise ValueError("Generated Series data does not match the document subject")
    title = series.get("title")
    members = payload.get("member_works")
    if not isinstance(title, str) or not title.strip() or not isinstance(members, list):
        raise ValueError("Generated Series title or member list is unavailable")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for member in members:
        if not isinstance(member, dict):
            raise ValueError("Generated Series member is invalid")
        work_id = member.get("work_id")
        work_title = member.get("title")
        year = member.get("year_display")
        if (
            not isinstance(work_id, str)
            or not re.fullmatch(r"[0-9]{5}", work_id)
            or work_id in seen
            or not isinstance(work_title, str)
            or not work_title.strip()
            or not isinstance(year, str)
        ):
            raise ValueError("Generated Series member identity, title or year is invalid")
        seen.add(work_id)
        rows.append({"work_id": work_id, "title": work_title, "year_display": year})
    return {"series_id": series_id, "title": title, "works": rows}


def build_series_works_report(repo_root: Path, target: Mapping[str, Any]) -> dict[str, Any]:
    """Use the document's sole Series subject to read current generated consumer JSON.

    This local report reads the prepared Catalogue workspace, not canonical records
    or the archive. Accepted public Catalogue distribution is a separate workflow.
    """

    resolved = resolve_managed_document_target(repo_root, target)
    subject = normalize_authoring_subject(resolved.document.front_matter, folder_supported=False)
    if subject["state"] != "valid" or subject["kind"] != "series":
        raise ValueError("Works in Series requires a document with a Series subject")
    series_id = subject["key"]
    if not re.fullmatch(r"[0-9]{3}", series_id):
        raise ValueError("Works in Series requires an exact three-digit Series ID")
    generated_root = configured_projects_base() / "catalogue" / "generated"
    source = generated_root / "series" / "index" / f"{series_id}.json"
    try:
        source.resolve().relative_to(generated_root.resolve())
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Generated data for Series {series_id} is unavailable") from exc
    if not isinstance(payload, dict):
        raise ValueError("Generated Series data must be an object")
    return {
        "ok": True,
        "schema": REPORT_SCHEMA,
        "target": resolved.request_target(),
        **series_work_rows(payload, series_id),
    }


def build_series_work_media(repo_root: Path, target: Mapping[str, Any], work_id: str) -> dict[str, Any]:
    """Read one current member on demand and supply the existing Media View contract."""

    report = build_series_works_report(repo_root, target)
    if not any(row["work_id"] == work_id for row in report["works"]):
        raise ValueError("Work is not a member of the document's Series")
    generated_root = configured_projects_base() / "catalogue" / "generated"
    source = generated_root / "works" / "index" / f"{work_id}.json"
    try:
        source.resolve().relative_to(generated_root.resolve())
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Generated data for Work {work_id} is unavailable") from exc
    work = payload.get("work") if isinstance(payload, dict) else None
    if not isinstance(work, dict) or work.get("work_id") != work_id:
        raise ValueError("Generated Work data does not match the selected Work")
    title = work.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Generated Work title is unavailable")
    for field in ("width_px", "height_px", "media_version"):
        if type(work.get(field)) is not int or work[field] <= 0:
            raise ValueError(f"Generated Work {field} must be a positive integer")

    # Existing Catalogue media convention is projected here, not guessed by the browser.
    media = json.loads((repo_root / "site-tools/config/site-tools.json").read_text())["media"]
    pipeline = json.loads((repo_root / "_data/pipeline.json").read_text())
    primary = pipeline["variants"]["primary"]
    filename = f"{work_id}-{primary['suffix']}-{primary['preferred_width']}.{pipeline['encoding']['format']}"
    image_url = f"{media['base'].rstrip('/')}/{media['image_works'].strip('/')}/{filename}?v={work['media_version']}"
    metadata = []
    for label, field in (("Year", "year_display"), ("Medium", "medium_caption")):
        if work.get(field):
            metadata.append({"label": label, "value": str(work[field])})
    dimensions = [work.get(field) for field in ("height_cm", "width_cm", "depth_cm")]
    if dimensions[0] and dimensions[1]:
        metadata.append({"label": "Dimensions", "value": " × ".join(f"{value:g}" for value in dimensions if value) + " cm"})
    metadata.append({"label": "Catalogue number", "value": work_id})
    return {
        "ok": True,
        "target": report["target"],
        "presentation": {
            "schema_version": "docs_media_view_v1",
            "target": {"kind": "catalogue-work", "id": work_id},
            "label": title,
            "image": {"src": image_url, "alt": title, "width_px": work["width_px"], "height_px": work["height_px"]},
            "metadata": metadata,
            "new_tab_target": image_url,
        },
    }
