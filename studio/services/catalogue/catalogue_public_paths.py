"""Catalogue public filesystem path contract."""

from __future__ import annotations

from pathlib import Path


PUBLIC_SITE_ROOT = Path("site")
PUBLIC_ASSETS_ROOT = PUBLIC_SITE_ROOT / "assets"
PUBLIC_DATA_ROOT = PUBLIC_ASSETS_ROOT / "data"

WORKS_JSON_DIR = PUBLIC_ASSETS_ROOT / "works" / "index"
RECENT_INDEX_JSON_PATH = PUBLIC_DATA_ROOT / "recent_index.json"
CATALOGUE_SEARCH_INDEX_JSON_PATH = PUBLIC_DATA_ROOT / "search" / "catalogue" / "index.json"


def thumb_output_dir(kind: str) -> Path:
    if kind == "work":
        return PUBLIC_ASSETS_ROOT / "works" / "img"
    raise ValueError(f"unsupported local media kind: {kind}")


def work_record_path(work_id: str) -> Path:
    return WORKS_JSON_DIR / f"{work_id}.json"
