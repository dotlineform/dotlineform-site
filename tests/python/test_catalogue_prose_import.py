#!/usr/bin/env python3
"""Verify catalogue staged prose and draft moment import helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import catalogue_prose_import as prose_import  # noqa: E402
from catalogue_source import SOURCE_FILES, payload_for_map  # noqa: E402
from moment_sources import MOMENT_METADATA_FILENAME, moment_metadata_payload  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_source_baseline(root: Path) -> Path:
    source_dir = root / "assets/studio/data/catalogue"
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


def test_prose_import_preview_reports_overwrite_and_hashes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = write_source_baseline(root)
        write_text(root / "var/docs/catalogue/import-staging/works/00008.md", "new prose\n")
        write_text(root / "_docs_src_catalogue/works/00008.md", "old prose\n")

        preview = prose_import.build_prose_import_preview(root, source_dir, {"target_kind": "work", "work_id": "8"})

        assert preview["valid"] is True
        assert preview["target_id"] == "00008"
        assert preview["staging_path"] == "var/docs/catalogue/import-staging/works/00008.md"
        assert preview["target_path"] == "_docs_src_catalogue/works/00008.md"
        assert preview["overwrite_required"] is True
        assert preview["changed"] is True
        assert preview["content_sha256"]
        assert preview["target_sha256"]


def test_prose_import_apply_enforces_allowlisted_target_root() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = write_source_baseline(root)
        write_text(root / "var/docs/catalogue/import-staging/series/067.md", "series prose\n")

        try:
            prose_import.apply_prose_import(
                root,
                source_dir,
                {"target_kind": "series", "series_id": "67"},
                allowed_write_roots=set(),
                dry_run=False,
            )
        except ValueError as exc:
            assert "prose source root is not allowlisted" in str(exc)
        else:
            raise AssertionError("expected allowlist rejection")


def test_prose_import_apply_writes_changed_source_without_backup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = write_source_baseline(root)
        write_text(root / "var/docs/catalogue/import-staging/series/067.md", "series prose\n")

        result = prose_import.apply_prose_import(
            root,
            source_dir,
            {"target_kind": "series", "series_id": "67"},
            allowed_write_roots={(root / "_docs_src_catalogue/series").resolve()},
            dry_run=False,
        )

        assert result.changed is True
        assert result.target.target_id == "067"
        assert (root / "_docs_src_catalogue/series/067.md").read_text(encoding="utf-8") == "series prose\n"
        assert not (root / "var/studio/catalogue/backups").exists()


def test_moment_import_apply_writes_body_and_metadata_backup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = write_source_baseline(root)
        backups_dir = root / "var/studio/catalogue/backups"
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
            allowed_write_roots={(root / "_docs_src_catalogue/moments").resolve()},
            backups_dir=backups_dir,
            dry_run=False,
        )

        assert result.moment_id == "keys"
        assert (root / "_docs_src_catalogue/moments/keys.md").read_text(encoding="utf-8") == "Moment body\n"
        payload = json.loads((source_dir / MOMENT_METADATA_FILENAME).read_text(encoding="utf-8"))
        record = payload["moments"]["keys"]
        assert record["title"] == "Keys updated"
        assert record["status"] == "draft"
        assert record["date"] == "2024-01-02"
        assert result.backup_paths


if __name__ == "__main__":
    test_prose_import_preview_reports_overwrite_and_hashes()
    test_prose_import_apply_enforces_allowlisted_target_root()
    test_prose_import_apply_writes_changed_source_without_backup()
    test_moment_import_apply_writes_body_and_metadata_backup()
    print("catalogue prose import tests passed")
