#!/usr/bin/env python3
"""Private Docs media-source evidence contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docs_import_test_support import make_repo
from docs_media_source_evidence import (
    TABLE_IDENTITY,
    load_media_source_evidence,
    media_source_evidence_for,
    record_media_source_evidence,
)
from repo_factory import docs_scope_record, write_docs_scope_config


@pytest.fixture(autouse=True)
def isolated_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    projects = tmp_path / "projects"
    projects.mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects))
    return projects


def test_records_sorted_scope_owned_evidence_without_a_public_projection(
    isolated_media_workspace: Path,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_docs_scope_config(
            root,
            [docs_scope_record("analysis")],
        )

        record_media_source_evidence(
            root,
            "analysis",
            media_type="svg",
            identity="zeta.svg",
            source_root="analysis",
            source_path="analysis/diagrams/zeta.svg",
        )
        record_media_source_evidence(
            root,
            "analysis",
            media_type="img",
            identity="alpha.png",
            source_root="analysis",
            source_path="analysis/images/alpha.png",
        )

        table_path = (
            root
            / "docs-viewer/scopes/analysis/source/media"
            / TABLE_IDENTITY
        )
        payload = json.loads(table_path.read_text(encoding="utf-8"))
        records = load_media_source_evidence(root, "analysis")

        assert not (root / "site" / TABLE_IDENTITY).exists()

    assert [record.identity for record in records] == ["alpha.png", "zeta.svg"]
    assert payload == {
        "schema_version": "docs_media_source_evidence_v1",
        "scope": "analysis",
        "records": [
            {
                "media_type": "img",
                "identity": "alpha.png",
                "source_root": "analysis",
                "source_path": "analysis/images/alpha.png",
            },
            {
                "media_type": "svg",
                "identity": "zeta.svg",
                "source_root": "analysis",
                "source_path": "analysis/diagrams/zeta.svg",
            },
        ],
    }


def test_same_media_identity_is_replaced_by_the_latest_explicit_source() -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_docs_scope_config(
            root,
            [docs_scope_record("analysis")],
        )
        record_media_source_evidence(
            root,
            "analysis",
            media_type="img",
            identity="photo.png",
            source_root="analysis",
            source_path="analysis/first/photo.png",
        )

        record_media_source_evidence(
            root,
            "analysis",
            media_type="img",
            identity="photo.png",
            source_root="analysis",
            source_path="analysis/second/photo.png",
        )
        evidence = media_source_evidence_for(root, "analysis", "img", "photo.png")

    assert evidence is not None
    assert evidence.source_path == "analysis/second/photo.png"


def test_external_scope_keeps_evidence_in_its_external_source_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    projects = tmp_path / "Projects"
    root.mkdir()
    (projects / "docs-viewer").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects))
    write_docs_scope_config(
        root,
        [
            docs_scope_record(
                "dotlineform",
                scope_type="local_external",
                scope_root_provider="external_local",
            )
        ],
    )

    record_media_source_evidence(
        root,
        "dotlineform",
        media_type="files",
        identity="notes.pdf",
        source_root="analysis",
        source_path="analysis/notes/notes.pdf",
    )

    assert (
        projects
        / "docs-viewer/scopes/dotlineform/source/media"
        / TABLE_IDENTITY
    ).is_file()


@pytest.mark.parametrize(
    ("source_root", "source_path"),
    [
        (".", "analysis/photo.png"),
        ("analysis", "/analysis/photo.png"),
        ("analysis", "processing/photo.png"),
        ("analysis", "analysis/../photo.png"),
    ],
)
def test_rejects_noncanonical_or_out_of_root_source_evidence(
    source_root: str,
    source_path: str,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        write_docs_scope_config(
            root,
            [docs_scope_record("analysis")],
        )

        with pytest.raises(ValueError):
            record_media_source_evidence(
                root,
                "analysis",
                media_type="img",
                identity="photo.png",
                source_root=source_root,
                source_path=source_path,
            )
