"""Data-oriented fixtures for Studio tag tests."""

from __future__ import annotations


def tag_row(tag_id: str, group: str, description: str = "") -> dict[str, object]:
    del description
    return {
        "tag_id": tag_id,
        "group": group,
        "updated_at_utc": "2026-05-01T00:00:00Z",
    }


def alias_mutation_registry_payload() -> dict[str, object]:
    return {
        "policy": {
            "allowed_groups": [
                "subject",
                "domain",
                "form",
                "theme",
                "mood",
                "material",
            ]
        },
        "tags": [
            {"tag_id": "trees", "group": "subject"},
            {"tag_id": "canopy", "group": "subject"},
            {"tag_id": "growth", "group": "theme"},
            {"tag_id": "studio", "group": "domain"},
            {"tag_id": "quiet", "group": "mood"},
            {"tag_id": "paper", "group": "material"},
        ]
    }


def promotion_registry_payload() -> dict[str, object]:
    return {
        "tag_registry_version": "tag_registry_v6",
        "updated_at_utc": "2026-05-01T00:00:00Z",
        "policy": {"allowed_groups": ["subject", "theme", "domain"]},
        "tags": [
            tag_row("trees", "subject"),
            tag_row("canopy", "subject"),
            tag_row("growth", "theme"),
            tag_row("studio", "domain"),
        ],
    }


def promotion_aliases_payload() -> dict[str, object]:
    return {
        "aliases": {
            "foliage": {"description": "Leaf forms", "tags": ["trees"]},
            "combo": {"description": "", "tags": ["trees", "growth"]},
            "workspace": {"description": "", "tags": ["studio"]},
        }
    }


def promotion_assignments_payload() -> dict[str, object]:
    return {
        "series": {
            "001": {
                "tags": [
                    {"tag_id": "trees", "w_manual": 0.9},
                    {"tag_id": "studio", "w_manual": 0.3},
                ],
                "works": {
                    "00001": {
                        "tags": [
                            {"tag_id": "trees", "w_manual": 0.6},
                            {"tag_id": "growth", "w_manual": 0.3},
                        ]
                    }
                },
            }
        }
    }
