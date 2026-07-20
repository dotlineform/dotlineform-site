"""Data-oriented fixtures for Analytics tag tests."""

from __future__ import annotations


def tag_row(tag_id: str, description: str = "") -> dict[str, str]:
    group, slug = tag_id.split(":", 1)
    return {
        "tag_id": tag_id,
        "group": group,
        "label": slug,
        "description": description,
    }


def alias_mutation_registry_payload() -> dict[str, object]:
    return {
        "tags": [
            {"tag_id": "subject:trees", "group": "subject"},
            {"tag_id": "subject:canopy", "group": "subject"},
            {"tag_id": "theme:growth", "group": "theme"},
            {"tag_id": "domain:studio", "group": "domain"},
            {"tag_id": "mood:quiet", "group": "mood"},
            {"tag_id": "material:paper", "group": "material"},
        ]
    }


def promotion_registry_payload() -> dict[str, object]:
    return {
        "policy": {"allowed_groups": ["subject", "theme", "domain"]},
        "tags": [
            tag_row("subject:trees"),
            tag_row("subject:canopy"),
            tag_row("theme:growth"),
            tag_row("domain:studio"),
        ],
    }


def promotion_aliases_payload() -> dict[str, object]:
    return {
        "aliases": {
            "foliage": {"description": "Leaf forms", "tags": ["subject:trees"]},
            "combo": {"description": "", "tags": ["subject:trees", "theme:growth"]},
            "studio": {"description": "", "tags": ["domain:studio"]},
        }
    }


def promotion_assignments_payload() -> dict[str, object]:
    return {
        "series": {
            "001": {
                "tags": [
                    {"tag_id": "subject:trees", "w_manual": 0.9},
                    {"tag_id": "domain:studio", "w_manual": 0.3},
                ],
                "works": {
                    "00001": {
                        "tags": [
                            {"tag_id": "subject:trees", "w_manual": 0.6},
                            {"tag_id": "theme:growth", "w_manual": 0.3},
                        ]
                    }
                },
            }
        }
    }
