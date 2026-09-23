"""Read current generated Catalogue data for authoring, runtime and availability audits.

Reads are confined to the configured generated workspace. No document, canonical
Catalogue record, archive lookup or inferred media filename is a dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from pipeline_config import load_pipeline_config
from studio.services.catalogue.catalogue_output_paths import catalogue_output_workspace, output_path

CATALOGUE_THUMBNAIL_PREFIX = "/docs/catalogue-thumbnails/"


def _read_generated(repo_root: Path, relative: str) -> dict[str, Any]:
    try:
        workspace = catalogue_output_workspace(repo_root)
        payload = json.loads(output_path(workspace, relative).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Generated Catalogue data is unavailable") from exc
    if not isinstance(payload, dict):
        raise ValueError("Generated Catalogue data must be an object")
    return payload


def _work_identity(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{5}", value):
        raise ValueError("An exact five-digit Catalogue Work ID is required")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Generated Work {label} is unavailable")
    return value.strip()


def _positive_integer(value: Any) -> bool:
    return type(value) is int and value > 0


def _safe_media_url(value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        return ""
    if any(char == "\\" or ord(char) <= 32 or ord(char) == 127 for char in value):
        return ""
    if value.startswith("/") and not value.startswith("//"):
        return value
    try:
        parsed = urlsplit(value)
        if parsed.scheme == "https" and parsed.hostname and parsed.username is None and parsed.password is None:
            return value
    except ValueError:
        pass
    return ""


def read_catalogue_media_config(repo_root: Path) -> dict[str, Any]:
    """Read the producer's shared public policy without exposing private pipeline inputs."""
    payload = _read_generated(repo_root, "media-config.json")
    header = payload.get("header")
    if not isinstance(header, dict) or header.get("schema") != "catalogue_media_config_v1":
        raise ValueError("Generated Catalogue media configuration is unavailable")
    primary, thumbnails = payload.get("primary", {}), payload.get("thumbnails", {})
    if not isinstance(primary, dict) or not isinstance(thumbnails, dict):
        raise ValueError("Generated Catalogue rendition policy is unavailable")
    bases = primary.get("base_urls", {})
    if not isinstance(bases, dict) or any(not _safe_media_url(bases.get(family)) or not bases[family].endswith("/")
           or any(char in bases[family] for char in "?#,") for family in ("works", "work_details")):
        raise ValueError("Generated Catalogue image bases are unsafe")
    for settings, key in ((primary, "widths"), (thumbnails, "sizes")):
        values = settings.get(key)
        if not isinstance(values, list) or not values or any(not _positive_integer(value) for value in values):
            raise ValueError("Generated Catalogue rendition sizes are unavailable")
        if not isinstance(settings.get("suffix"), str) or not re.fullmatch(r"[a-z0-9-]+", settings["suffix"]):
            raise ValueError("Generated Catalogue rendition suffix is unavailable")
    if payload.get("format") not in ("webp", "avif", "png", "jpg") or primary.get("version_query_parameter") != "v":
        raise ValueError("Generated Catalogue media format or version policy is unsupported")
    return payload


def read_catalogue_work_index(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Read the generated Work inventory without loading Series or by-ID records."""
    payload = _read_generated(repo_root, "works/works_index.json")
    works = payload.get("works")
    if not isinstance(works, dict):
        raise ValueError("Generated Catalogue Work index is unavailable")
    for key, work in works.items():
        work_id = _work_identity(key)
        if not isinstance(work, dict) or work.get("work_id") != work_id:
            raise ValueError("Generated Work index identity is mismatched")
    return works


def read_catalogue_media_targets(repo_root: Path) -> dict[str, Any]:
    """Expose Work and Series search identities from generated indexes, without document filtering."""
    targets = []
    for work_id, work in read_catalogue_work_index(repo_root).items():
        year = work.get("year_display")
        targets.append({
            "family": "catalogue", "target_type": "work", "target_id": work_id,
            "title": _text(work.get("title"), "title"),
            "meta": [year] if isinstance(year, str) and year else [],
        })
    series = _read_generated(repo_root, "series/series_index.json").get("series")
    if not isinstance(series, dict):
        raise ValueError("Generated Catalogue Series index is unavailable")
    for series_id, record in series.items():
        if not re.fullmatch(r"[0-9]{3}", series_id) or not isinstance(record, dict) or record.get("series_id") != series_id:
            raise ValueError("Generated Series index identity is mismatched")
        title = record.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Generated Series title is unavailable")
        year = record.get("year_display")
        targets.append({
            "family": "catalogue", "target_type": "series", "target_id": series_id,
            "title": title.strip(), "meta": [year] if isinstance(year, str) and year else [],
        })
    return {"ok": True, "schema_version": "docs_semantic_token_target_lookup_v2", "targets": targets}


def read_catalogue_work(repo_root: Path, work_id: str) -> dict[str, Any]:
    """Return the generated consumer record; browser presentation belongs to the shared renderer."""
    work_id = _work_identity(work_id)
    payload = _read_generated(repo_root, f"works/index/{work_id}.json")
    work = payload.get("work")
    if not isinstance(work, dict) or work.get("work_id") != work_id:
        raise ValueError(f"Generated data does not match Work {work_id}")
    _text(work.get("title"), "title")
    return payload


def read_catalogue_series(repo_root: Path, series_id: str) -> dict[str, Any]:
    """Read exact ordered membership without requiring documents or member Work reads."""
    if not isinstance(series_id, str) or not re.fullmatch(r"[0-9]{3}", series_id):
        raise ValueError("An exact three-digit Catalogue Series ID is required")
    payload = _read_generated(repo_root, f"series/index/{series_id}.json")
    series = payload.get("series")
    if not isinstance(series, dict) or series.get("series_id") != series_id:
        raise ValueError("Generated Series data does not match the selected Series")
    if not isinstance(series.get("title"), str) or not series["title"].strip():
        raise ValueError("Generated Series title is unavailable")
    members = payload.get("member_works")
    if not isinstance(members, list):
        raise ValueError("Generated Series membership is unavailable")
    seen = set()
    for member in members:
        if not isinstance(member, dict):
            raise ValueError("Generated Series member must be an object")
        work_id = _work_identity(member.get("work_id"))
        if work_id in seen:
            raise ValueError("Generated Series has a duplicate Work")
        seen.add(work_id)
        _text(member.get("title"), "title")
    return payload


def catalogue_thumbnail_path(repo_root: Path, request_path: str) -> Path:
    """Serve only configured Work thumbnail variants within generated Catalogue output."""
    if not request_path.startswith(CATALOGUE_THUMBNAIL_PREFIX):
        raise ValueError("Unsupported Catalogue thumbnail path")
    filename = request_path[len(CATALOGUE_THUMBNAIL_PREFIX):]
    pipeline = load_pipeline_config(repo_root=repo_root)
    variant = pipeline["variants"]["thumb"]
    sizes = "|".join(re.escape(str(size)) for size in variant["sizes"])
    pattern = rf"[0-9]{{5}}-{re.escape(variant['suffix'])}-(?:{sizes})\.{re.escape(pipeline['encoding']['format'])}"
    if not re.fullmatch(pattern, filename):
        raise ValueError("An exact configured Work thumbnail is required")
    path = output_path(catalogue_output_workspace(repo_root), f"works/thumbs/{filename}")
    if not path.is_file():
        raise FileNotFoundError("Generated Catalogue thumbnail is unavailable")
    return path


def catalogue_media_record(payload: dict[str, Any], work_id: str, detail_id: str = "") -> dict[str, Any]:
    """Validate only the exact requested image; a Detail does not require a Work primary."""
    work_id = _work_identity(work_id)
    record = payload.get("work")
    if not isinstance(record, dict) or record.get("work_id") != work_id:
        raise ValueError(f"Generated data does not match Work {work_id}")
    if detail_id:
        if not re.fullmatch(r"(?:[0-9]{3}|[1-9][0-9]{3,})", detail_id) or not int(detail_id):
            raise ValueError("An exact Catalogue Detail ID is required")
        detail_uid = f"{work_id}-{detail_id}"
        sections = payload.get("sections")
        if not isinstance(sections, list) or any(
            not isinstance(section, dict) or not isinstance(section.get("details"), list) for section in sections
        ):
            raise ValueError("Generated Detail sections are unavailable")
        matches = [
            detail for section in sections
            for detail in section["details"] if isinstance(detail, dict) and detail.get("detail_uid") == detail_uid
        ]
        if len(matches) != 1 or matches[0].get("work_id") != work_id or matches[0].get("detail_id") != detail_id:
            raise ValueError(f"Generated Detail {detail_uid} is unavailable or mismatched")
        record = matches[0]
    _text(record.get("title"), "image title")
    if not all(_positive_integer(record.get(field)) for field in ("width_px", "height_px")):
        raise ValueError("Generated image dimensions are unavailable")
    if not _positive_integer(record.get("media_version")):
        raise ValueError(f"Generated media version for Work {work_id} is unavailable")
    return record
