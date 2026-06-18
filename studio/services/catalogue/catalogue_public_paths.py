"""Catalogue public filesystem path contract."""

from __future__ import annotations

from pathlib import Path


PUBLIC_SITE_ROOT = Path("site")
PUBLIC_ASSETS_ROOT = PUBLIC_SITE_ROOT / "assets"
PUBLIC_DATA_ROOT = PUBLIC_ASSETS_ROOT / "data"

SERIES_JSON_DIR = PUBLIC_ASSETS_ROOT / "series" / "index"
SERIES_INDEX_JSON_PATH = PUBLIC_DATA_ROOT / "series_index.json"
WORKS_JSON_DIR = PUBLIC_ASSETS_ROOT / "works" / "index"
WORKS_INDEX_JSON_PATH = PUBLIC_DATA_ROOT / "works_index.json"
RECENT_INDEX_JSON_PATH = PUBLIC_DATA_ROOT / "recent_index.json"
CATALOGUE_SEARCH_INDEX_JSON_PATH = PUBLIC_DATA_ROOT / "search" / "catalogue" / "index.json"


def thumb_output_dir(kind: str) -> Path:
    if kind == "work":
        return PUBLIC_ASSETS_ROOT / "works" / "img"
    if kind == "work_details":
        return PUBLIC_ASSETS_ROOT / "work_details" / "img"
    raise ValueError(f"unsupported local media kind: {kind}")


def work_record_path(work_id: str) -> Path:
    return WORKS_JSON_DIR / f"{work_id}.json"


def series_record_path(series_id: str) -> Path:
    return SERIES_JSON_DIR / f"{series_id}.json"
