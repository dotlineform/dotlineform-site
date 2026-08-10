#!/usr/bin/env python3
"""Verify the guarded one-time tag-document bootstrap."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
DOCS_VIEWER_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for import_dir in (STUDIO_SERVICES_DIR, DOCS_VIEWER_SERVICES_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from docs_document_identity import (  # noqa: E402
    doc_id_matches_added_date,
    is_immutable_doc_id,
)
from tags import tag_document_bootstrap as bootstrap  # noqa: E402


ADDED_DATE = "2026-07-27 23:15:00"
CREATED_AT_UTC = "2026-07-27T22:15:00Z"


def assert_raises_contains(
    fn: Callable[[], Any],
    expected: str,
) -> None:
    try:
        fn()
    except ValueError as exc:
        assert expected in str(exc)
        return
    raise AssertionError("expected ValueError")


def registry_payload() -> dict[str, Any]:
    return {
        "tag_registry_version": "tag_registry_v3",
        "updated_at_utc": "2026-07-27T16:31:07Z",
        "policy": {"allowed_groups": ["subject", "theme"]},
        "tags": [
            {
                "tag_id": "flower",
                "group": "subject",
                "description": "Depicted flower.",
                "updated_at_utc": "2026-07-27T15:39:06Z",
            },
            {
                "tag_id": "renewal",
                "group": "theme",
                "description": "",
                "updated_at_utc": "2026-07-27T15:40:00Z",
            },
        ],
    }


def aliases_payload() -> dict[str, Any]:
    return {
        "tag_aliases_version": "tag_aliases_v2",
        "updated_at_utc": "2026-07-27T16:00:00Z",
        "aliases": {},
    }


def assignments_payload() -> dict[str, Any]:
    return {
        "tag_assignments_version": "tag_assignments_v2",
        "updated_at_utc": "2026-07-27T16:00:00Z",
        "series": {},
    }


def existing_source_text() -> str:
    return (
        "---\n"
        "doc_id: d-20260624-204534-0d6ae2\n"
        'title: "bird"\n'
        'added_date: "2026-06-24 20:45:34"\n'
        'last_updated: "2026-06-24"\n'
        'parent_id: ""\n'
        "---\n"
        "# bird\n"
    )


def existing_documents() -> list[dict[str, str]]:
    source = existing_source_text()
    return [
        {
            "doc_id": "d-20260624-204534-0d6ae2",
            "relative_path": (
                "docs-viewer/scopes/analysis/source/sub-scopes/tags/"
                "documents/d-20260624-204534-0d6ae2.md"
            ),
            "source_sha256": bootstrap.sha256_text(source),
        }
    ]


def fingerprints(
    documents: list[dict[str, str]] | None = None,
) -> dict[str, str]:
    inventory = documents if documents is not None else existing_documents()
    return {
        "registry_sha256": "a" * 64,
        "aliases_sha256": "b" * 64,
        "assignments_sha256": "c" * 64,
        "documents_sha256": bootstrap.document_inventory_sha256(inventory),
    }


def deterministic_allocator() -> Callable[[str, Any], str]:
    suffixes = iter(("000001", "000002"))

    def allocate(added_date: str, _existing: Any) -> str:
        date_part = added_date.replace("-", "").replace(":", "").replace(" ", "-")
        return f"d-{date_part}-{next(suffixes)}"

    return allocate


def build_plan() -> dict[str, Any]:
    return bootstrap.build_tag_document_bootstrap_plan(
        registry_payload(),
        aliases_payload(),
        assignments_payload(),
        existing_documents(),
        added_date=ADDED_DATE,
        created_at_utc=CREATED_AT_UTC,
        input_fingerprints=fingerprints(),
        allocate_document_id=deterministic_allocator(),
        is_immutable_doc_id=is_immutable_doc_id,
        doc_id_matches_added_date=doc_id_matches_added_date,
    )


def test_plan_adds_only_doc_ids_and_fixed_sources() -> None:
    registry = registry_payload()
    original = copy.deepcopy(registry)
    plan = build_plan()

    assert registry == original
    assert plan["output"]["registry_version"] == "tag_registry_v4"
    assert plan["output"]["new_document_count"] == 2
    assert plan["output"]["final_document_count"] == 3
    assert [row["tag_id"] for row in plan["projected_registry"]["tags"]] == [
        "flower",
        "renewal",
    ]
    assert [
        row["updated_at_utc"] for row in plan["projected_registry"]["tags"]
    ] == [
        "2026-07-27T15:39:06Z",
        "2026-07-27T15:40:00Z",
    ]
    assert plan["documents"][0]["source_text"] == (
        "---\n"
        "doc_id: d-20260727-231500-000001\n"
        'title: "flower"\n'
        'added_date: "2026-07-27 23:15:00"\n'
        'last_updated: "2026-07-27"\n'
        'parent_id: ""\n'
        "---\n"
        "# flower\n\n"
        "**subject**\n\n"
        "Depicted flower.\n"
    )
    assert plan["documents"][1]["source_text"].endswith(
        "# renewal\n\n**theme**\n"
    )


def test_plan_rejects_partial_registry_or_changed_inputs() -> None:
    partial = registry_payload()
    partial["tags"][0]["doc_id"] = "d-20260727-231500-000001"
    assert_raises_contains(
        lambda: bootstrap.build_tag_document_bootstrap_plan(
            partial,
            aliases_payload(),
            assignments_payload(),
            existing_documents(),
            added_date=ADDED_DATE,
            created_at_utc=CREATED_AT_UTC,
            input_fingerprints=fingerprints(),
            allocate_document_id=deterministic_allocator(),
            is_immutable_doc_id=is_immutable_doc_id,
            doc_id_matches_added_date=doc_id_matches_added_date,
        ),
        "already contains doc_id",
    )

    plan = build_plan()
    changed_fingerprints = fingerprints()
    changed_fingerprints["registry_sha256"] = "d" * 64
    assert_raises_contains(
        lambda: bootstrap.validate_tag_document_bootstrap_plan(
            plan,
            registry_payload(),
            aliases_payload(),
            assignments_payload(),
            existing_documents(),
            input_fingerprints=changed_fingerprints,
            is_immutable_doc_id=is_immutable_doc_id,
            doc_id_matches_added_date=doc_id_matches_added_date,
        ),
        "fingerprints do not match",
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bootstrap.canonical_json_text(payload), encoding="utf-8")


def fixture_repo(tmp_path: Path) -> tuple[Path, Path]:
    write_json(
        tmp_path / "studio/data/canonical/tags/tag-registry.json",
        registry_payload(),
    )
    write_json(
        tmp_path / "studio/data/canonical/tags/tag-aliases.json",
        aliases_payload(),
    )
    write_json(
        tmp_path / "studio/data/canonical/tags/tag-assignments.json",
        assignments_payload(),
    )
    existing_path = (
        tmp_path
        / bootstrap.DEFAULT_DOCUMENTS_ROOT
        / "d-20260624-204534-0d6ae2.md"
    )
    existing_path.parent.mkdir(parents=True, exist_ok=True)
    existing_path.write_text(existing_source_text(), encoding="utf-8")
    return (
        tmp_path,
        tmp_path / "var/studio/tag-document-bootstrap/test-plan.json",
    )


def run_command(*args: str) -> dict[str, Any]:
    command = [
        sys.executable,
        str(REPO_ROOT / "studio/commands/bootstrap_tag_documents.py"),
        *args,
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert isinstance(payload, dict)
    return payload


def test_command_preview_write_and_validate_are_plan_locked(
    tmp_path: Path,
) -> None:
    repo_root, plan_path = fixture_repo(tmp_path)
    registry_path = repo_root / "studio/data/canonical/tags/tag-registry.json"
    registry_before = registry_path.read_bytes()

    preview = run_command(
        "--repo-root",
        str(repo_root),
        "--plan-file",
        str(plan_path),
        "--added-date",
        ADDED_DATE,
        "--created-at-utc",
        CREATED_AT_UTC,
    )
    assert preview["mode"] == "preview"
    assert preview["tag_count"] == 2
    assert preview["new_document_count"] == 2
    assert registry_path.read_bytes() == registry_before
    assert len(
        list((repo_root / bootstrap.DEFAULT_DOCUMENTS_ROOT).glob("*.md"))
    ) == 1

    written = run_command(
        "--repo-root",
        str(repo_root),
        "--plan-file",
        str(plan_path),
        "--write",
    )
    assert written["mode"] == "write"
    assert written["linked_document_count"] == 2
    registry_after = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry_after["tag_registry_version"] == "tag_registry_v4"
    assert len(
        list((repo_root / bootstrap.DEFAULT_DOCUMENTS_ROOT).glob("*.md"))
    ) == 3

    validated = run_command(
        "--repo-root",
        str(repo_root),
        "--plan-file",
        str(plan_path),
        "--validate",
    )
    assert validated["mode"] == "validate"
    assert validated["final_document_count"] == 3
