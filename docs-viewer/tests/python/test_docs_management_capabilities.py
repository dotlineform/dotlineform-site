#!/usr/bin/env python3
"""Docs Management capability and source report tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from docs_management_test_support import (
    docs_management_service,
    make_repo,
    write_docs_scope_config,
    write_docs_viewer_browser_config,
    write_generated_docs,
)
from docs_management_capabilities_service import (
    capability_scope_root_label,
)
import docs_local_links
from repo_factory import docs_sub_scope_record

def test_capabilities_advertise_generated_data_reads() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.capabilities_payload(repo_root)

    assert payload["capabilities"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_data_reads"] is True
    assert payload["capabilities"]["scopes"]["studio"]["generated_search_reads"] is True


def test_capabilities_expose_exact_local_folder_link_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as repo_name:
        repo_root = Path(repo_name)
        base = tmp_path / "projects"
        base.mkdir()
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(base))
        monkeypatch.setattr(docs_local_links.sys, "platform", "darwin")

        payload = docs_management_service.capabilities_payload(repo_root)

    assert payload["capabilities"]["local_folder_links"] == {
        "authoring": True,
        "activation": True,
        "base_path": str(base.resolve()),
    }


def test_static_snapshot_export_capability_projects_preview_and_apply() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.capabilities_payload(repo_root)

    capabilities = payload["capabilities"]
    assert capabilities["static_html_export"] == {
        "preview": True,
        "apply": True,
        "error": "",
    }
    assert capabilities["scopes"]["studio"]["static_html_export"] == {
        "preview": True,
        "apply": True,
        "document_count": 2,
        "default_doc_id": "child",
        "error": "",
    }


def test_capabilities_advertise_source_config_reads() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        payload = docs_management_service.capabilities_payload(repo_root)

    assert payload["capabilities"]["source_config_reads"] is True
    assert payload["capabilities"]["source_config_settings_reads"] is True
    assert payload["capabilities"]["source_config_settings_writes"] is True
    assert payload["capabilities"]["document_transfer"] == {
        "preview": True,
        "apply": True,
    }
    assert payload["capabilities"]["document_delete"] == {
        "preview": True,
        "apply": True,
        "sub_scope_detail": True,
    }
    assert "review_sessions" not in payload["capabilities"]["docs_review"]
    assert payload["capabilities"]["scope_lifecycle"]["manifest"] is True
    assert payload["capabilities"]["scope_lifecycle"]["create_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["create_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["rename_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["rename_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["delete_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["delete_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_create_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_create_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_delete_preview"] is True
    assert payload["capabilities"]["scope_lifecycle"]["sub_scope_delete_apply"] is True
    assert payload["capabilities"]["scope_lifecycle"]["publishing_modes"] == [
        "public_readonly",
        "local_external",
        "local_committed",
    ]
    assert payload["capabilities"]["scopes"]["studio"]["sub_scope_lifecycle"]["create_eligible"] is True
    assert payload["capabilities"]["scopes"]["studio"]["sub_scope_lifecycle"]["sub_scopes"] == []
    assert payload["capabilities"]["scopes"]["studio"]["scope_lifecycle"]["rename_eligible"] is False
    assert payload["capabilities"]["scopes"]["studio"]["scope_type"] == "local"
    assert payload["capabilities"]["scopes"]["studio"]["document_transfer"] == {
        "copy_source": True,
        "move_source": True,
        "target": True,
        "collections": [
            {
                "target": {"scope": "studio"},
                "label": "studio",
                "copy_source": True,
                "move_source": True,
                "copy_target": True,
                "move_target": True,
            },
        ],
    }


def test_public_scope_is_copy_source_and_target_but_not_move_source_or_target() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = config_path.read_text(encoding="utf-8").replace(
            '"scope_type": "local"',
            '"scope_type": "public"',
            1,
        )
        config_path.write_text(config, encoding="utf-8")
        payload = docs_management_service.capabilities_payload(repo_root)

    assert payload["capabilities"]["scopes"]["studio"]["document_transfer"] == {
        "copy_source": True,
        "move_source": False,
        "target": True,
        "collections": [
            {
                "target": {"scope": "studio"},
                "label": "studio",
                "copy_source": True,
                "move_source": False,
                "copy_target": True,
                "move_target": False,
            },
        ],
    }


def test_capabilities_list_exact_parent_and_child_transfer_collections() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["scopes"][0]["sub_scopes"] = [
            docs_sub_scope_record("studio", "works", title="Works"),
        ]
        config_path.write_text(
            json.dumps(config, indent=2) + "\n",
            encoding="utf-8",
        )
        (
            repo_root
            / "docs-viewer/scopes/studio/source/sub-scopes/works/documents"
        ).mkdir(parents=True)
        payload = docs_management_service.capabilities_payload(repo_root)

    collections = payload["capabilities"]["scopes"]["studio"][
        "document_transfer"
    ]["collections"]
    assert collections == [
        {
            "target": {"scope": "studio"},
            "label": "studio",
            "copy_source": True,
            "move_source": True,
            "copy_target": True,
            "move_target": True,
        },
        {
            "target": {"scope": "studio", "sub_scope": "works"},
            "label": "studio / Works",
            "copy_source": True,
            "move_source": False,
            "copy_target": True,
            "move_target": False,
        },
    ]


def test_external_scope_capability_uses_portable_root_label() -> None:
    config = SimpleNamespace(
        scope_type="local_external",
        scope_root=SimpleNamespace(path=Path("/Users/example/external/docs-viewer/scopes/research")),
    )

    label = capability_scope_root_label(Path("/repo"), "research", config)

    assert label == "scopes/research"


def test_missing_external_workspace_disables_only_import_and_review_capabilities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as repo_name:
        repo_root = Path(repo_name)
        write_docs_scope_config(repo_root)
        monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(tmp_path / "missing-projects"))

        payload = docs_management_service.capabilities_payload(repo_root)

    capabilities = payload["capabilities"]
    assert capabilities["docs_management"] is True
    assert capabilities["source_editor"] is True
    assert capabilities["local_folder_links"] == {
        "authoring": False,
        "activation": False,
        "base_path": "",
    }
    assert capabilities["html_import"] is False
    assert capabilities["library_import"] is False
    assert capabilities["docs_import"]["available"] is False
    assert capabilities["docs_review"]["available"] is False
    assert capabilities["scopes"]["studio"]["available"] is True
    assert capabilities["static_html_export"]["preview"] is False
    assert capabilities["static_html_export"]["apply"] is False
    assert capabilities["scopes"]["studio"]["static_html_export"]["preview"] is False
    assert str(tmp_path) not in capabilities["static_html_export"]["error"]

def test_source_config_report_reads_known_config_files() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_docs_viewer_browser_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_source_config_report.build_source_config_report(repo_root)

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_source_config_report_v1"
    assert payload["source_config_path"] == "docs-viewer/config/scopes/docs_scopes.json"
    assert payload["scopes"][0]["scope_id"] == "studio"
    assert payload["scopes"][0]["source_config"]["scope_type"] == "local"
    assert payload["scopes"][0]["roles"]["source"]["provider"] == "repository"
    assert payload["scopes"][0]["roles"]["published_documents"]["provider"] == "repository"
    assert payload["scopes"][0]["browser_config"]["index_tree_url"] == "/docs-viewer/scopes/studio/published/documents/index-tree.json"
    assert payload["scopes"][0]["browser_config"]["recent_url"] == "/docs-viewer/scopes/studio/published/documents/recent.json"
    assert payload["scopes"][0]["artifacts"] == {
        "published_documents_available": True,
        "published_search_available": True,
    }
    assert payload["scopes"][0]["warnings"] == []
