#!/usr/bin/env python3
"""Persistent Docs Review package publication tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_import_test_support import make_repo
import docs_review_materialization as materialization
from docs_document_packages.workspace import configured_workspace_paths


def test_failed_generated_build_removes_temporary_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        preview_root = configured_workspace_paths(root).import_preview
        package_path = preview_root / "persistent-review"

        def fail_build(*_args, **_kwargs):
            raise RuntimeError("simulated builder failure")

        monkeypatch.setattr(materialization, "build_review_package", fail_build)
        with pytest.raises(RuntimeError, match="simulated builder failure"):
            materialization.publish_review_package(
                root,
                package_path=package_path,
                package_id=package_path.name,
                default_doc_id="alpha",
                source_records=[
                    {
                        "filename": "alpha.md",
                        "source_text": "---\ndoc_id: alpha\ntitle: Alpha\n---\n# Alpha\n",
                    }
                ],
                manifest={
                    "schema_version": "docs_review_validated_package_v1",
                    "package_id": package_path.name,
                    "status": "validated",
                    "source_scope": "library",
                },
            )

        assert package_path.exists() is False
        assert list(preview_root.glob(".persistent-review.publishing-*")) == []
