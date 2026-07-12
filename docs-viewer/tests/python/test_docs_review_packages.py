#!/usr/bin/env python3
"""Fixture-backed returned-package service contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import docs_review_packages
import docs_review_routes
import docs_review_service
from services.paths import workspace_paths


REPO_ROOT = Path(__file__).resolve().parents[3]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_package(package_id: str = "fixture-review") -> Path:
    package = workspace_paths().import_preview / package_id
    write_json(
        package / "manifest.json",
        {
            "schema_version": "docs_review_validated_package_v1",
            "package_id": package_id,
            "status": "validated",
            "title": "Fixture review",
            "source_scope": "library",
            "default_doc_id": "fixture-root",
        },
    )
    source = """---
doc_id: fixture-root
title: Fixture root
added_date: 2026-07-11
last_updated: 2026-07-11
viewable: true
---
# Fixture root

Original review text.
"""
    (package / "source").mkdir(parents=True, exist_ok=True)
    (package / "source/fixture-root.md").write_text(source, encoding="utf-8")
    write_json(package / "inventories/assets.json", {"schema_version": "asset_inventory_v1", "assets": []})
    return package


def test_fixture_package_lists_builds_and_reads_generated_payload() -> None:
    package = write_package()

    listed = docs_review_packages.list_packages(REPO_ROOT)
    built = docs_review_packages.build_package(REPO_ROOT, {"package_id": package.name})
    already_built = docs_review_packages.build_package(REPO_ROOT, {"package_id": package.name})
    tree = docs_review_packages.read_index_tree(REPO_ROOT, package.name)
    document = docs_review_packages.read_payload(REPO_ROOT, package.name, "fixture-root")
    assets = docs_review_packages.read_asset_inventories(REPO_ROOT, package.name)

    assert listed["packages"][0]["package_id"] == package.name
    assert listed["packages"][0]["built"] is False
    assert built["document_count"] == 1
    assert built["repaired"] is True
    assert already_built["repaired"] is False
    assert built["generated_path"].endswith(f"/import-preview/{package.name}/generated")
    assert tree["index_tree"]["docs"][0]["doc_id"] == "fixture-root"
    assert document["payload"]["doc_id"] == "fixture-root"
    assert document["payload"]["viewer_url"].startswith(f"/docs-review/?package={package.name}&doc=")
    assert assets["inventories"]["assets"]["assets"] == []


def test_missing_or_damaged_generated_output_repairs_once_then_stays_persistent() -> None:
    package = write_package("repair-review")

    first_tree = docs_review_packages.read_index_tree(REPO_ROOT, package.name)
    second_tree = docs_review_packages.read_index_tree(REPO_ROOT, package.name)
    payload_path = package / "generated/by-id/fixture-root.json"
    payload_path.write_text("{damaged", encoding="utf-8")
    repaired_payload = docs_review_packages.read_payload(REPO_ROOT, package.name, "fixture-root")
    persistent_payload = docs_review_packages.read_payload(REPO_ROOT, package.name, "fixture-root")
    listed = docs_review_packages.list_packages(REPO_ROOT)

    assert first_tree["generated_repaired"] is True
    assert second_tree["generated_repaired"] is False
    assert repaired_payload["generated_repaired"] is True
    assert persistent_payload["generated_repaired"] is False
    assert persistent_payload["payload"]["doc_id"] == "fixture-root"
    assert listed["packages"][0]["built"] is True


def test_source_write_is_revision_checked_package_local_and_rebuilds() -> None:
    package = write_package()
    docs_review_packages.build_package(REPO_ROOT, {"package_id": package.name})
    source = docs_review_packages.read_source(REPO_ROOT, package.name, "fixture-root")

    written = docs_review_packages.write_source(
        REPO_ROOT,
        {
            "package_id": package.name,
            "doc_id": "fixture-root",
            "source_revision": source["source_revision"],
            "source_body": "# Fixture root\n\nEdited review text.\n",
        },
    )

    assert written["source_revision"] != source["source_revision"]
    assert "Edited review text." in (package / "source/fixture-root.md").read_text(encoding="utf-8")
    assert "Edited review text." in docs_review_packages.read_payload(
        REPO_ROOT,
        package.name,
        "fixture-root",
    )["payload"]["content_html"]
    with pytest.raises(ValueError, match="stale"):
        docs_review_packages.write_source(
            REPO_ROOT,
            {
                "package_id": package.name,
                "doc_id": "fixture-root",
                "source_revision": source["source_revision"],
                "source_body": "stale",
            },
        )


def test_source_write_rejects_parent_updates() -> None:
    package = write_package("parent-review")
    (package / "source/fixture-child.md").write_text(
        """---
doc_id: fixture-child
title: Fixture child
parent_id: fixture-root
added_date: 2026-07-11
last_updated: 2026-07-11
---
# Fixture child
""",
        encoding="utf-8",
    )
    source = docs_review_packages.read_source(REPO_ROOT, package.name, "fixture-child")

    with pytest.raises(ValueError, match="does not support parent updates"):
        docs_review_packages.write_source(
            REPO_ROOT,
            {
                "package_id": package.name,
                "doc_id": "fixture-child",
                "source_revision": source["source_revision"],
                "parent_id": "",
            },
        )

    assert "parent_id: fixture-root" in (package / "source/fixture-child.md").read_text(encoding="utf-8")


def test_package_asset_inventory_drives_media_and_sandboxed_interactive_rendering() -> None:
    package = write_package("asset-review")
    source_path = package / "source/fixture-root.md"
    source_path.write_text(
        source_path.read_text(encoding="utf-8")
        + "\n![Preview]([[media:docs/library/img/preview.png]])\n\n"
        + "[[interactive-html:demo.html height=320]]\n",
        encoding="utf-8",
    )
    media = package / "assets/media/preview.png"
    media.parent.mkdir(parents=True)
    media.write_bytes(b"fixture-png")
    interactive = package / "assets/interactive/demo.html"
    interactive.parent.mkdir(parents=True)
    interactive.write_text("<!doctype html><title>Demo</title>", encoding="utf-8")
    write_json(
        package / "inventories/assets.json",
        {
            "schema_version": "asset_inventory_v1",
            "assets": [
                {
                    "kind": "media",
                    "token_path": "docs/library/img/preview.png",
                    "package_path": "assets/media/preview.png",
                },
                {
                    "kind": "interactive",
                    "token_path": "demo.html",
                    "package_path": "assets/interactive/demo.html",
                },
            ],
        },
    )

    built = docs_review_packages.build_package(REPO_ROOT, {"package_id": package.name})
    payload = docs_review_packages.read_payload(REPO_ROOT, package.name, "fixture-root")["payload"]

    assert built["asset_count"] == 2
    assert "/docs-review/packages/assets-content/asset-review/assets/media/preview.png" in payload["content_html"]
    assert "/docs-review/packages/assets-content/asset-review/assets/interactive/demo.html" in payload["content_html"]
    assert 'sandbox="allow-scripts"' in payload["content_html"]
    assert docs_review_packages.resolve_asset_file(
        REPO_ROOT,
        package.name,
        "assets/media/preview.png",
    ) == media


def test_package_contract_rejects_unvalidated_nested_and_symlink_sources() -> None:
    package = write_package("invalid-review")
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    manifest["status"] = "pending"
    write_json(package / "manifest.json", manifest)
    with pytest.raises(ValueError, match="validated"):
        docs_review_packages.read_manifest(REPO_ROOT, package.name)

    manifest["status"] = "validated"
    write_json(package / "manifest.json", manifest)
    nested = package / "source/nested/extra.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("---\ndoc_id: extra\ntitle: Extra\n---\n# Extra\n", encoding="utf-8")
    with pytest.raises(ValueError, match="direct children"):
        docs_review_packages.read_manifest(REPO_ROOT, package.name)

    nested.unlink()
    link = package / "source/link.md"
    link.symlink_to(package / "source/fixture-root.md")
    with pytest.raises(ValueError, match="symlinks"):
        docs_review_packages.read_manifest(REPO_ROOT, package.name)


def test_package_listing_reports_rejection_diagnostics_for_empty_state() -> None:
    package = write_package("rejected-review")
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    manifest["schema_version"] = "data_sharing_import_review_source_v1"
    write_json(package / "manifest.json", manifest)

    listed = docs_review_packages.list_packages(REPO_ROOT)

    assert listed["packages"] == []
    assert listed["rejected"] == [
        {
            "package_id": package.name,
            "path": f"$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/{package.name}",
            "error": "review package manifest schema_version must be docs_review_validated_package_v1",
        }
    ]


def test_review_dispatcher_keeps_routes_outside_management_dispatch() -> None:
    package = write_package()

    listed = docs_review_service.docs_review_get_payload(REPO_ROOT, docs_review_routes.PACKAGES_PATH, {})
    capabilities = docs_review_service.docs_review_get_payload(
        REPO_ROOT,
        docs_review_routes.CAPABILITIES_PATH,
        {},
    )
    status, built = docs_review_service.docs_review_post_response(
        REPO_ROOT,
        docs_review_routes.BUILD_PATH,
        {"package_id": package.name},
    )

    assert listed["packages"][0]["package_id"] == package.name
    assert capabilities["capabilities"]["review_source_write"] is True
    assert capabilities["capabilities"]["canonical_write"] is False
    assert status.value == 200
    assert built["ok"] is True


def test_review_capabilities_disable_cleanly_when_external_workspace_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path / "missing-projects"))

    payload = docs_review_service.docs_review_get_payload(
        REPO_ROOT,
        docs_review_routes.CAPABILITIES_PATH,
        {},
    )

    assert payload["available"] is False
    assert payload["capabilities"]["review_packages_list"] is False
    assert payload["capabilities"]["review_source_write"] is False
    assert "does not exist" in payload["workspace"]["message"]
