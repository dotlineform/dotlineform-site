#!/usr/bin/env python3
"""Focused checks for catalogue local media staging cleanup."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_build_media as build_media  # noqa: E402


def test_successful_thumbnail_copy_removes_staged_thumbnail_but_keeps_primary() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "source.jpg"
        staged_source = root / "var/catalogue/media/works/make_srcset_images/00001.jpg"
        staged_thumb = root / "var/catalogue/media/works/srcset_images/thumb/00001-thumb-96.webp"
        staged_primary = root / "var/catalogue/media/works/srcset_images/primary/00001-primary-800.webp"
        asset_thumb = root / "assets/works/img/00001-thumb-96.webp"
        source.write_bytes(b"source-image")

        plan = {
            "tasks": [
                {
                    "kind": "work",
                    "id": "00001",
                    "status": "pending",
                    "source_abs_path": str(source),
                    "staged_source_abs_path": str(staged_source),
                    "pending_staged_source": True,
                    "pending_thumb_outputs": [
                        {
                            "size": 96,
                            "absolute_path": str(staged_thumb),
                        }
                    ],
                    "pending_primary_outputs": [
                        {
                            "width": 800,
                            "absolute_path": str(staged_primary),
                        }
                    ],
                    "pending_asset_thumbs": [
                        {
                            "absolute_path": str(asset_thumb),
                            "staged_absolute_path": str(staged_thumb),
                        }
                    ],
                }
            ],
            "counts": {"pending": 1, "current": 0, "blocked": 0, "unavailable": 0},
        }

        def fake_thumb(src: Path, size: int, dest: Path) -> tuple[int, str]:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(f"thumb:{size}".encode("utf-8"))
            return 0, ""

        def fake_primary(src: Path, width: int, dest: Path) -> tuple[int, str]:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(f"primary:{width}".encode("utf-8"))
            return 0, ""

        result = build_media.execute_local_media_plan(
            root,
            scope={},
            write=True,
            plan_builder=lambda *args, **kwargs: plan,
            thumb_runner=fake_thumb,
            primary_runner=fake_primary,
        )

        assert result["status"] == "completed"
        assert asset_thumb.read_bytes() == b"thumb:96"
        assert staged_source.exists()
        assert staged_primary.read_bytes() == b"primary:800"
        assert not staged_thumb.exists()
        assert result["cleaned_staged_thumbs"] == {
            "work": ["var/catalogue/media/works/srcset_images/thumb/00001-thumb-96.webp"],
            "work_details": [],
        }


if __name__ == "__main__":
    test_successful_thumbnail_copy_removes_staged_thumbnail_but_keeps_primary()
    print("catalogue media cleanup checks passed")
