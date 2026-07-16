#!/usr/bin/env python3
"""Docs source config settings tests."""

from __future__ import annotations

import json
from pathlib import Path

from docs_management_test_support import docs_management_service, make_repo, write_docs_scope_config, write_generated_docs

def test_source_config_settings_contract_exposes_default_doc_id() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)
        payload = docs_management_service.docs_source_config_settings.build_settings_contract(repo_root, "studio")

    assert payload["ok"] is True
    assert payload["schema_version"] == "docs_source_config_settings_v1"
    assert payload["editable_scope_fields"] == [
        {
            "field": "default_doc_id",
            "type": "string",
            "source_path": "docs-viewer/config/scopes/docs_scopes.json scopes[].default_doc_id",
            "generated_path": "docs-viewer/config/defaults/docs-viewer-config.json scopes[].default_doc_id",
            "requires_rebuild": True,
            "description": "Default document id opened for this scope when no document is requested. Leave blank to use the first loadable document.",
        }
    ]
    assert payload["deferred_global_fields"][0]["field"] == "recent_limit"
    assert any(field["field"] == "source" for field in payload["blocked_scope_fields"])
    assert not any(field["field"] == "default_doc_id" for field in payload["blocked_scope_fields"])
    scope = payload["scopes"][0]
    assert scope["scope_id"] == "studio"
    assert scope["fields"][0]["field"] == "default_doc_id"
    assert scope["fields"][0]["type"] == "string"
    assert scope["fields"][0]["current_value"] == "child"
    assert scope["fields"][0]["editable"] is True

def test_source_config_settings_validates_and_writes_default_doc_id() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)

        validation = docs_management_service.docs_source_config_settings.validate_scope_settings_change(
            repo_root,
            "studio",
            {"default_doc_id": "other"},
        )
        dry_run = docs_management_service.docs_source_config_settings.apply_scope_settings_change(
            repo_root,
            "studio",
            {"default_doc_id": "other"},
            dry_run=True,
        )
        applied = docs_management_service.docs_source_config_settings.apply_scope_settings_change(
            repo_root,
            "studio",
            {"default_doc_id": "other"},
        )
        config_payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))

    assert validation["changes"]["default_doc_id"]["current_value"] == "child"
    assert validation["changes"]["default_doc_id"]["proposed_value"] == "other"
    assert validation["changes"]["default_doc_id"]["changed"] is True
    assert validation["requires_rebuild"] is True
    assert validation["affected_artifacts"] == [
        "docs-viewer/config/defaults/docs-viewer-config.json scopes[].default_doc_id"
    ]
    assert dry_run["changed"] is True
    assert applied["changed"] is True
    assert config_payload["scopes"][0]["default_doc_id"] == "other"

def test_source_config_settings_rejects_unknown_default_doc_id() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)

        try:
            docs_management_service.docs_source_config_settings.validate_scope_settings_change(
                repo_root,
                "studio",
                {"default_doc_id": "missing-doc"},
            )
        except ValueError as exc:
            assert "default_doc_id" in str(exc)
            assert "missing-doc" in str(exc)
        else:
            raise AssertionError("unknown default_doc_id should be rejected")

def test_source_config_settings_rejects_blocked_and_deferred_fields() -> None:
    with make_repo() as temp_path:
        repo_root = Path(temp_path)
        write_docs_scope_config(repo_root)
        write_generated_docs(repo_root)

        try:
            docs_management_service.docs_source_config_settings.validate_scope_settings_change(
                repo_root,
                "studio",
                {"source": "_docs2"},
            )
        except ValueError as exc:
            assert "source" in str(exc)
        else:
            raise AssertionError("blocked source field should be rejected")

        try:
            docs_management_service.docs_source_config_settings.validate_scope_settings_change(
                repo_root,
                "studio",
                {"recent_limit": 12},
            )
        except ValueError as exc:
            assert "recent_limit" in str(exc)
        else:
            raise AssertionError("deferred global field should be rejected")
