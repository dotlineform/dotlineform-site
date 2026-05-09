#!/usr/bin/env python3
"""Verify generated catalogue moment artifact builders."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_generation_moments as moments  # noqa: E402


def test_source_records_are_sorted_and_path_defaults_are_bound() -> None:
    source_records = moments.build_moment_source_records(
        {
            "zeta": {"title": "Zeta"},
            "alpha": {
                "title": "Alpha",
                "date": "2026-5-9",
                "date_display": "May 2026",
                "image_alt": "",
                "source_image_file": "custom.jpg",
            },
        },
        moments_prose_root=Path("/repo/_docs_catalogue/moments"),
        moments_images_root=Path("/projects/moments/images"),
    )

    assert [record["moment_id"] for record in source_records] == ["alpha", "zeta"]
    assert source_records[0]["date"] == "2026-05-09"
    assert source_records[0]["source_image_file"] == "custom.jpg"
    assert source_records[0]["source_prose_path"] == Path("/repo/_docs_catalogue/moments/alpha.md")
    assert source_records[0]["source_image_path"] == Path("/projects/moments/images/custom.jpg")
    assert source_records[1]["source_image_file"] == "zeta.jpg"


def test_moment_artifact_decision_pins_selection_status_slug_and_prose() -> None:
    selected = {"blue-sky"}

    assert moments.decide_moment_artifact(
        {"moment_id": "blue-sky", "status": "draft"},
        selected_moment_ids=selected,
        refresh_published=False,
        prose_exists=True,
    ).should_generate

    missing_prose = moments.decide_moment_artifact(
        {"moment_id": "blue-sky", "status": "draft"},
        selected_moment_ids=selected,
        refresh_published=False,
        prose_exists=False,
    )
    assert missing_prose.skip_reason == moments.MISSING_PROSE

    invalid_slug = moments.decide_moment_artifact(
        {"moment_id": "Blue Sky", "status": "draft"},
        selected_moment_ids=None,
        refresh_published=False,
        prose_exists=True,
    )
    assert invalid_slug.slug_safe is False
    assert invalid_slug.skip_reason == moments.INVALID_SLUG

    published_without_refresh = moments.decide_moment_artifact(
        {"moment_id": "blue-sky", "status": "published"},
        selected_moment_ids=selected,
        refresh_published=False,
        prose_exists=True,
    )
    assert published_without_refresh.skip_reason == moments.NOT_ACTIONABLE_STATUS

    assert moments.decide_moment_artifact(
        {"moment_id": "blue-sky", "status": "published"},
        selected_moment_ids=selected,
        refresh_published=True,
        prose_exists=True,
    ).should_generate


def test_runtime_record_uses_alt_fallback_and_omits_missing_images() -> None:
    record = moments.build_moment_runtime_record(
        {
            "moment_id": "blue-sky",
            "title": "Blue Sky",
            "date": "2026-5-9",
            "date_display": "",
            "image_alt": "",
            "image_file": "",
        },
        source_image_exists=True,
        width_px=1200,
        height_px=800,
        include_layout=True,
    )

    assert record == {
        "moment_id": "blue-sky",
        "title": "Blue Sky",
        "date": "2026-05-09",
        "date_display": None,
        "images": [{"file": "blue-sky.jpg", "alt": "Blue Sky"}],
        "width_px": 1200,
        "height_px": 800,
        "layout": "moment",
    }

    no_image = moments.build_moment_runtime_record(
        {"moment_id": "blue-sky", "title": "Blue Sky"},
        source_image_exists=False,
    )
    assert no_image["images"] == []
    assert no_image["width_px"] is None
    assert "layout" not in no_image


def test_moment_record_payload_shape() -> None:
    payload = moments.build_moment_record_payload(
        {
            "moment_id": "blue-sky",
            "title": "Blue Sky",
            "date": "2026-05-09",
            "date_display": None,
            "images": [{"file": "blue-sky.jpg", "alt": "Blue Sky"}],
            "width_px": 1200,
            "height_px": 800,
            "layout": "moment",
        },
        content_html="<p>Body</p>\n",
        generated_at_utc="2026-05-09T12:00:00Z",
    )

    assert payload["header"]["schema"] == "moment_record_v1"
    assert payload["header"]["moment_id"] == "blue-sky"
    assert payload["header"]["generated_at_utc"] == "2026-05-09T12:00:00Z"
    assert payload["header"]["version"].startswith("blake2b-")
    assert payload["moment"] == {
        "moment_id": "blue-sky",
        "title": "Blue Sky",
        "date": "2026-05-09",
        "images": [{"file": "blue-sky.jpg", "alt": "Blue Sky"}],
        "width_px": 1200,
        "height_px": 800,
    }
    assert payload["content_html"] == "<p>Body</p>\n"


def test_moments_index_payload_shape_is_sorted_and_thumb_aware() -> None:
    payload = moments.build_moments_index_payload(
        [
            {"moment_id": "zeta", "title": "Zeta", "date": "2025-01-01", "images": []},
            {
                "moment_id": "alpha",
                "title": "Alpha",
                "date": "2026-05-09",
                "date_display": "May 2026",
                "images": [{"file": "alpha.jpg", "alt": "Alpha"}],
            },
        ],
        generated_at_utc="2026-05-09T12:00:00Z",
    )

    assert payload["header"]["schema"] == "moments_index_v1"
    assert payload["header"]["count"] == 2
    assert payload["header"]["generated_at_utc"] == "2026-05-09T12:00:00Z"
    assert list(payload["moments"].keys()) == ["alpha", "zeta"]
    assert payload["moments"]["alpha"] == {
        "moment_id": "alpha",
        "title": "Alpha",
        "date": "2026-05-09",
        "date_display": "May 2026",
        "thumb_id": "alpha",
    }
    assert payload["moments"]["zeta"] == {
        "moment_id": "zeta",
        "title": "Zeta",
        "date": "2025-01-01",
    }


def main() -> None:
    test_source_records_are_sorted_and_path_defaults_are_bound()
    test_moment_artifact_decision_pins_selection_status_slug_and_prose()
    test_runtime_record_uses_alt_fallback_and_omits_missing_images()
    test_moment_record_payload_shape()
    test_moments_index_payload_shape_is_sorted_and_thumb_aware()
    print("Catalogue generation moment tests OK")


if __name__ == "__main__":
    main()
