#!/usr/bin/env python3
"""Verify the reviewed Registry-v5 Tag document-link migration plan."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
for path in (
    REPO_ROOT / "studio" / "services",
    REPO_ROOT / "docs-viewer" / "services",
):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from tags import tag_document_link_migration as migration  # noqa: E402


NOW = "2026-08-11T12:00:00Z"
DOC_ONE = "d-20260811-000001-000001"
DOC_TWO = "d-20260811-000002-000002"
DOC_THREE = "d-20260811-000003-000003"


def source_text(doc_id: str, title: str, *, tag_line: str = "") -> str:
    declaration = f"tag_id: {tag_line}\n" if tag_line else ""
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"title: {title}\n"
        "group: subject\n"
        f"{declaration}"
        "status: public\n"
        "---\n"
        f"\n# {title}\n\nBody stays exact.\n"
    )


def document(doc_id: str, title: str, *, tag_line: str = "") -> dict[str, str]:
    source = source_text(doc_id, title, tag_line=tag_line)
    return {
        "doc_id": doc_id,
        "relative_path": f"analysis-tags/{doc_id}.md",
        "source_sha256": migration.sha256_text(source),
        "source_text": source,
        "title": title,
    }


def location(doc_id: str, url: str, title: str) -> dict[str, str]:
    return {
        "scope_id": "analysis",
        "sub_scope": "tags",
        "doc_id": doc_id,
        "document_title": title,
        "url": url,
    }


def registry_row(tag_id: str, urls: list[str]) -> dict[str, object]:
    return {
        "tag_id": tag_id,
        "group": "subject",
        "doc_url": urls,
        "updated_at_utc": "2026-08-01T00:00:00Z",
    }


def registry(*rows: dict[str, object]) -> dict[str, object]:
    return {
        "tag_registry_version": "tag_registry_v5",
        "updated_at_utc": "2026-08-01T00:00:00Z",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": list(rows),
    }


def build_plan(
    registry_payload: dict[str, object],
    documents: list[dict[str, str]],
    locations: list[dict[str, str]],
) -> dict[str, object]:
    return migration.build_migration_plan(
        registry_payload,
        documents,
        locations,
        created_at_utc=NOW,
        input_fingerprints={
            "registry_sha256": "registry",
            "documents_sha256": "documents",
            "locations_sha256": "locations",
        },
    )


def test_plan_moves_exact_legacy_links_to_source_declarations() -> None:
    first_url = f"/analysis/?doc={DOC_ONE}"
    second_url = f"/analysis/?doc={DOC_TWO}"
    docs = [document(DOC_TWO, "Second"), document(DOC_ONE, "First")]
    locations = [
        location(DOC_TWO, second_url, "Second"),
        location(DOC_ONE, first_url, "First"),
    ]

    plan = build_plan(
        registry(
            registry_row("trees", [first_url]),
            registry_row("growth", [second_url]),
        ),
        docs,
        locations,
    )

    assert plan["output"]["source_edit_count"] == 2
    assert plan["output"]["resolved_legacy_url_count"] == 2
    assert plan["output"]["unresolved_legacy_url_count"] == 0
    assert plan["output"]["primary_document_count"] == 0
    assert plan["expected_associations"] == [
        {
            "tag_id": "growth",
            "documents": [
                {"scope": "analysis", "sub_scope": "tags", "doc_id": DOC_TWO}
            ],
        },
        {
            "tag_id": "trees",
            "documents": [
                {"scope": "analysis", "sub_scope": "tags", "doc_id": DOC_ONE}
            ],
        },
    ]
    projected = plan["projected_registry"]
    assert projected["tag_registry_version"] == "tag_registry_v6"
    assert all("doc_url" not in row for row in projected["tags"])
    assert all("primary_document" not in row for row in projected["tags"])

    edits = {row["doc_id"]: row for row in plan["source_edits"]}
    assert edits[DOC_ONE]["source_text"] == source_text(DOC_ONE, "First").replace(
        "group: subject\n",
        "group: subject\ntag_id: trees\n",
        1,
    )
    assert edits[DOC_TWO]["source_text"] == source_text(DOC_TWO, "Second").replace(
        "group: subject\n",
        "group: subject\ntag_id: growth\n",
        1,
    )


def test_plan_uses_legacy_first_document_only_for_supported_primary() -> None:
    first_url = f"/analysis/?doc={DOC_TWO}"
    second_url = f"/analysis/?doc={DOC_ONE}"
    docs = [
        document(DOC_ONE, "First", tag_line="trees"),
        document(DOC_TWO, "Second"),
    ]

    plan = build_plan(
        registry(registry_row("trees", [first_url, second_url])),
        docs,
        [
            location(DOC_ONE, second_url, "First"),
            location(DOC_TWO, first_url, "Second"),
        ],
    )

    assert plan["expected_associations"] == [
        {
            "tag_id": "trees",
            "documents": [
                {"scope": "analysis", "sub_scope": "tags", "doc_id": DOC_ONE},
                {"scope": "analysis", "sub_scope": "tags", "doc_id": DOC_TWO},
            ],
        }
    ]
    assert plan["source_edits"][0]["doc_id"] == DOC_TWO
    assert plan["projected_registry"]["tags"][0]["primary_document"] == {
        "scope": "analysis",
        "sub_scope": "tags",
        "doc_id": DOC_TWO,
    }


def test_plan_reports_unresolved_and_unassociated_without_inference() -> None:
    stale_url = "/analysis/?doc=d-20260811-999999-999999"
    docs = [
        document(DOC_ONE, "Bird nerve"),
        document(DOC_TWO, "Similar title"),
    ]

    plan = build_plan(
        registry(registry_row("bird-nerve", [stale_url]), registry_row("aaa", [])),
        docs,
        [],
    )

    assert plan["resolved_legacy"] == []
    assert plan["unresolved_legacy"] == [
        {"tag_id": "bird-nerve", "url": stale_url}
    ]
    assert plan["source_edits"] == []
    assert plan["expected_associations"] == []
    assert [row["doc_id"] for row in plan["unassociated_documents"]] == [
        DOC_ONE,
        DOC_TWO,
    ]


def test_plan_blocks_conflicting_existing_declaration() -> None:
    url = f"/analysis/?doc={DOC_ONE}"
    docs = [document(DOC_ONE, "First", tag_line="growth")]
    registry_payload = registry(registry_row("trees", [url]))
    locations = [location(DOC_ONE, url, "First")]
    fingerprints = {
        "registry_sha256": "registry",
        "documents_sha256": "documents",
        "locations_sha256": "locations",
    }
    plan = migration.build_migration_plan(
        registry_payload,
        docs,
        locations,
        created_at_utc=NOW,
        input_fingerprints=fingerprints,
    )

    assert plan["source_edits"] == []
    assert plan["blocking_conflicts"][0]["reason"] == (
        "existing_declaration_conflicts"
    )
    with pytest.raises(ValueError, match="blocking document conflicts"):
        migration.validate_migration_plan(
            plan,
            registry_payload,
            docs,
            locations,
            input_fingerprints=fingerprints,
        )


def test_reviewed_plan_rejects_changed_input_fingerprint() -> None:
    url = f"/analysis/?doc={DOC_ONE}"
    docs = [document(DOC_ONE, "First")]
    registry_payload = registry(registry_row("trees", [url]))
    locations = [location(DOC_ONE, url, "First")]
    plan = build_plan(registry_payload, docs, locations)

    with pytest.raises(ValueError, match="does not match current canonical input"):
        migration.validate_migration_plan(
            plan,
            registry_payload,
            docs,
            locations,
            input_fingerprints={
                "registry_sha256": "changed",
                "documents_sha256": "documents",
                "locations_sha256": "locations",
            },
        )
