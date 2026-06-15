#!/usr/bin/env python3
"""Verify catalogue staged prose and draft moment import helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_prose_import as prose_import  # noqa: E402
from catalogue.catalogue_source import SOURCE_FILES, payload_for_map  # noqa: E402
from catalogue.moment_sources import MOMENT_METADATA_FILENAME, moment_metadata_payload  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_source_baseline(root: Path) -> Path:
    source_dir = root / "studio/data/canonical/catalogue"
    write_json(
        source_dir / SOURCE_FILES["works"],
        payload_for_map("works", {"00008": {"work_id": "00008", "title": "Work Eight", "status": "draft"}}),
    )
    write_json(source_dir / SOURCE_FILES["work_details"], payload_for_map("work_details", {}))
    write_json(
        source_dir / SOURCE_FILES["series"],
        payload_for_map("series", {"067": {"series_id": "067", "title": "Series 67", "status": "draft"}}),
    )
    write_json(
        source_dir / MOMENT_METADATA_FILENAME,
        moment_metadata_payload(
            {
                "keys": {
                    "moment_id": "keys",
                    "title": "Keys",
                    "status": "draft",
                    "date": "2024-01-01",
                }
            }
        ),
    )
    return source_dir


def test_moment_import_apply_writes_body_and_metadata() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = write_source_baseline(root)
        write_text(root / "var/docs/catalogue/import-staging/moments/keys.md", "Moment body")

        result = prose_import.apply_moment_import(
            root,
            source_dir,
            {
                "moment_file": "keys.md",
                "metadata": {
                    "title": "Keys updated",
                    "status": "published",
                    "published_date": "2024-02-01",
                    "date": "2024-01-02",
                    "image_alt": "keys on a table",
                },
            },
            allowed_write_roots={(root / "studio/data/canonical/catalogue-markdown/moments").resolve()},
            dry_run=False,
        )

        assert result.moment_id == "keys"
        assert (root / "studio/data/canonical/catalogue-markdown/moments/keys.md").read_text(encoding="utf-8") == "Moment body\n"
        payload = json.loads((source_dir / MOMENT_METADATA_FILENAME).read_text(encoding="utf-8"))
        record = payload["moments"]["keys"]
        assert record["title"] == "Keys updated"
        assert record["status"] == "draft"
        assert record["date"] == "2024-01-02"


if __name__ == "__main__":
    test_moment_import_apply_writes_body_and_metadata()
    print("catalogue prose import tests passed")
