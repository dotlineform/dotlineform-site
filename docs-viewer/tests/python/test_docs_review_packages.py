#!/usr/bin/env python3
"""Fixture-backed returned-package service contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import docs_review_packages
import docs_review_routes
import docs_review_service
from docs_document_packages.workspace import workspace_paths


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
            "supports_docs_review": True,
            "supports_return_import": True,
            "selected_doc_ids": ["fixture-root"],
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
    source_path = package / "source/fixture-root.md"
    source_path.write_text(
        source_path.read_text(encoding="utf-8").replace(
            "Original review text.",
            "Edited review text.",
        ),
        encoding="utf-8",
    )
    edited_source = source_path.read_bytes()
    canonical_path = (
        package.parents[2]
        / "docs-viewer/scopes/library/source/documents/fixture-root.md"
    )
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text(
        "---\ndoc_id: fixture-root\nlast_updated: 2026-07-10\n---\nCanonical sentinel.\n",
        encoding="utf-8",
    )
    canonical_source = canonical_path.read_bytes()
    rebuilt = docs_review_packages.build_package(REPO_ROOT, {"package_id": package.name})
    tree = docs_review_packages.read_index_tree(REPO_ROOT, package.name)
    document = docs_review_packages.read_payload(REPO_ROOT, package.name, "fixture-root")
    assets = docs_review_packages.read_asset_inventories(REPO_ROOT, package.name)

    assert listed["packages"][0]["package_id"] == package.name
    assert listed["packages"][0]["built"] is False
    assert built["document_count"] == 1
    assert built["built"] is True
    assert rebuilt["built"] is True
    assert rebuilt["summary_text"] == f"Built 1 review documents for {package.name}."
    assert built["generated_path"].endswith(f"/import-preview/{package.name}/generated")
    assert tree["index_tree"]["docs"][0]["doc_id"] == "fixture-root"
    assert document["payload"]["doc_id"] == "fixture-root"
    assert "Edited review text." in document["payload"]["content_html"]
    assert document["payload"]["viewer_url"].startswith(f"/docs-review/?package={package.name}&doc=")
    assert assets["inventories"]["assets"]["assets"] == []
    assert source_path.read_bytes() == edited_source
    assert canonical_path.read_bytes() == canonical_source


def test_explicit_build_accepts_only_the_exact_package_identity() -> None:
    package = write_package("exact-build")

    with pytest.raises(ValueError, match="requires exactly package_id"):
        docs_review_packages.build_package(
            REPO_ROOT,
            {
                "package_id": package.name,
                "scope": "library",
            },
        )


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


def test_package_asset_inventory_drives_media_and_sandboxed_interactive_rendering() -> None:
    package = write_package("asset-review")
    source_path = package / "source/fixture-root.md"
    source_path.write_text(
        source_path.read_text(encoding="utf-8")
        + "\n![Preview]([[media:docs/library/img/preview.png]])\n\n"
        + "[[html-media:docs/library/html/demo.html height=320]]\n",
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
                    "token_path": "docs/library/html/demo.html",
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
    assert "review_source_read" not in capabilities["capabilities"]
    assert "review_source_write" not in capabilities["capabilities"]
    assert capabilities["capabilities"]["review_source_open"] is True
    assert capabilities["capabilities"]["canonical_write"] is False
    assert status.value == 200
    assert built["ok"] is True


def test_review_open_source_uses_exact_validated_package_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = write_package()
    calls: list[dict[str, object]] = []

    def fake_open_source_path(
        repo_root: Path,
        source_path: Path,
        *,
        editor: str,
        dry_run: bool,
    ) -> None:
        calls.append(
            {
                "repo_root": repo_root,
                "source_path": source_path,
                "editor": editor,
                "dry_run": dry_run,
            }
        )

    monkeypatch.setattr(docs_review_packages, "open_source_path", fake_open_source_path)
    monkeypatch.setattr(docs_review_packages, "log_event", lambda *_args: None)

    status, payload = docs_review_service.docs_review_post_response(
        REPO_ROOT,
        docs_review_routes.OPEN_SOURCE_PATH,
        {
            "package_id": package.name,
            "doc_id": "fixture-root",
        },
    )

    assert status.value == 200
    assert calls == [
        {
            "repo_root": REPO_ROOT,
            "source_path": package / "source/fixture-root.md",
            "editor": "vscode",
            "dry_run": False,
        }
    ]
    assert payload == {
        "ok": True,
        "package_id": package.name,
        "doc_id": "fixture-root",
        "editor": "vscode",
        "path": (
            "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-preview/"
            f"{package.name}/source/fixture-root.md"
        ),
        "summary_text": "Opened fixture-root source.",
    }

    with pytest.raises(FileNotFoundError, match="document not found"):
        docs_review_service.docs_review_post_response(
            REPO_ROOT,
            docs_review_routes.OPEN_SOURCE_PATH,
            {
                "package_id": package.name,
                "doc_id": "another-document",
            },
        )
    assert len(calls) == 1


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
    assert payload["capabilities"]["review_source_open"] is False
    assert "review_source_read" not in payload["capabilities"]
    assert "review_source_write" not in payload["capabilities"]
    assert "does not exist" in payload["workspace"]["message"]


def test_review_source_routes_and_package_methods_are_absent() -> None:
    assert not hasattr(docs_review_routes, "SOURCE_PATH")
    assert not hasattr(docs_review_packages, "read_source")
    assert not hasattr(docs_review_packages, "write_source")
    with pytest.raises(FileNotFoundError, match="Not found"):
        docs_review_service.docs_review_get_payload(
            REPO_ROOT,
            "/docs-review/packages/source",
            {"package_id": ["fixture-review"], "doc_id": ["fixture-root"]},
        )
    with pytest.raises(FileNotFoundError, match="Not found"):
        docs_review_service.docs_review_post_response(
            REPO_ROOT,
            "/docs-review/packages/source",
            {"package_id": "fixture-review"},
        )
