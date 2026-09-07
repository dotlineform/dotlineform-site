#!/usr/bin/env python3
"""Focused checks for Catalogue site-consistency source resolution."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "studio" / "tests" / "audits" / "catalogue_site_consistency.py"
SPEC = importlib.util.spec_from_file_location("catalogue_site_consistency", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generated_route_contracts_use_exact_records_without_works_aggregate(tmp_path: Path) -> None:
    write_json(
        tmp_path / "assets/works/index/00001.json",
        {
            "work": {
                "work_id": "00001",
                "series_ids": ["009"],
            }
        },
    )
    write_json(
        tmp_path / "assets/series/index/009.json",
        {
            "series": {
                "series_id": "009",
                "sort_fields": "work_id",
            },
            "member_works": [
                {"work_id": "00001", "title": "One", "year": 2025, "year_display": "2025"},
            ],
        },
    )

    works, series, work_details = audit.load_generated_route_contracts(tmp_path)

    assert works == {
        "00001": {
            "path": str(tmp_path / "assets/works/index/00001.json"),
            "fm": {
                "work_id": "00001",
                "series_ids": ["009"],
                "series_id": "009",
            },
        }
    }
    assert series == {
        "009": {
            "path": str(tmp_path / "assets/series/index/009.json"),
            "fm": {
                "series_id": "009",
                "sort_fields": "work_id",
            },
        }
    }
    assert work_details == {}
    assert audit.load_exact_series_member_ids(tmp_path) == {"009": ["00001"]}
