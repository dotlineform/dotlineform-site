#!/usr/bin/env python3
"""Rendered Document Info Mermaid source contracts."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace

import pytest

import docs_diagram_source_service
import docs_management_routes as routes
import docs_management_service
from docs_import_test_support import make_repo
from repo_factory import (
    docs_scope_record,
    docs_sub_scope_record,
    write_docs_scope_config,
)


@pytest.fixture(autouse=True)
def isolated_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects = tmp_path / "projects"
    (projects / "docs-viewer/media").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects))


def managed_media_path(root: Path, scope: str, lifecycle: str, *parts: str) -> Path:
    return root / "docs-viewer/scopes" / scope / lifecycle / "media" / Path(*parts)


def _configure_mermaid_fixture(root: Path) -> None:
    record = docs_scope_record(
        "example",
        scope_type="public",
        viewer_base_url="/example/",
        include_scope_param=False,
        default_doc_id="example",
        allow_unresolved_parent_ids=True,
        media_provider="repository",
        media_location_root="site/assets/data/docs/scopes/example/media",
        media_served_root="/assets/data/docs/scopes/example/media",
        media_types=("img", "svg", "files", "html"),
    )
    record["media"]["build_sources"] = {  # type: ignore[index]
        "mermaid": {
            "producer": "mermaid",
            "publishes_to": "svg",
        }
    }
    record["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
    record["sub_scopes"] = [
        docs_sub_scope_record("example", "tags", scope_type="public")
    ]
    write_docs_scope_config(root, [record])

    doc_path = root / "docs-viewer/scopes/example/source/documents/example.md"
    doc_path.write_text(
        doc_path.read_text(encoding="utf-8")
        + "\n![Architecture]([[media:docs/example/svg/architecture.svg]])\n"
        + "![Missing]([[media:docs/example/svg/missing.svg]])\n",
        encoding="utf-8",
    )
    detail_path = (
        root
        / "docs-viewer/scopes/example/source/sub-scopes/tags/documents/detail.md"
    )
    detail_path.parent.mkdir(parents=True)
    detail_path.write_text(
        "---\n"
        "doc_id: detail\n"
        "title: Detail\n"
        "---\n"
        "# Detail\n\n"
        "![Architecture]([[media:docs/example/svg/architecture.svg]])\n",
        encoding="utf-8",
    )
    source = managed_media_path(root, "example", "source", "build-source", "mermaid", "architecture.mmd")
    source.parent.mkdir(parents=True)
    source.write_text("flowchart LR\nA --> B\n", encoding="utf-8")
    generated = managed_media_path(root, "example", "generated", "svg", "architecture.svg")
    generated.parent.mkdir(parents=True)
    generated.write_text("<svg xmlns='http://www.w3.org/2000/svg'><rect width='1'/></svg>", encoding="utf-8")


def test_manage_diagram_sources_lists_only_verified_same_basename_pairs() -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_mermaid_fixture(root)

        payload = docs_management_service.docs_management_get_payload(
            root,
            routes.DIAGRAM_SOURCES_PATH,
            {"scope": ["example"], "doc_id": ["example"]},
        )

    assert payload == {
        "ok": True,
        "scope": "example",
        "doc_id": "example",
        "sources": [
            {
                "label": "Architecture",
                "media_identity": "docs/example/svg/architecture.svg",
                "source_identity": "architecture.mmd",
            }
        ],
    }
    assert str(root) not in str(payload)


def test_open_diagram_source_rederives_registered_local_source_without_returning_a_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **_options):
        calls.append(list(command))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with make_repo() as temp:
        root = Path(temp)
        _configure_mermaid_fixture(root)
        monkeypatch.setattr(docs_diagram_source_service.subprocess, "run", fake_run)

        status, payload = docs_management_service.docs_management_post_response(
            root,
            routes.OPEN_DIAGRAM_SOURCE_PATH,
            {
                "scope": "example",
                "doc_id": "example",
                "media_identity": "docs/example/svg/architecture.svg",
                "editor": "vscode",
            },
        )

    assert status == HTTPStatus.OK
    assert calls[0][:3] == ["open", "-a", "Visual Studio Code"]
    assert Path(calls[0][3]) == managed_media_path(
        root, "example", "source", "build-source", "mermaid", "architecture.mmd"
    ).resolve()
    assert payload["source_identity"] == "architecture.mmd"
    assert "path" not in payload
    assert str(root) not in str(payload)


def test_manage_diagram_sources_use_explicit_sub_scope_target() -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_mermaid_fixture(root)

        payload = docs_management_service.docs_management_get_payload(
            root,
            routes.DIAGRAM_SOURCES_PATH,
            {
                "scope": ["example"],
                "sub_scope": ["tags"],
                "doc_id": ["detail"],
            },
        )
        _status, opened = docs_management_service.docs_management_post_response(
            root,
            routes.OPEN_DIAGRAM_SOURCE_PATH,
            {
                "scope": "example",
                "sub_scope": "tags",
                "doc_id": "detail",
                "media_identity": "docs/example/svg/architecture.svg",
                "editor": "vscode",
            },
            dry_run=True,
        )

    assert payload["scope"] == "example"
    assert payload["sub_scope"] == "tags"
    assert payload["doc_id"] == "detail"
    assert [record["source_identity"] for record in payload["sources"]] == [
        "architecture.mmd"
    ]
    assert opened["sub_scope"] == "tags"
    assert opened["doc_id"] == "detail"


def test_open_diagram_source_rejects_media_not_registered_by_selected_document() -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_mermaid_fixture(root)

        with pytest.raises(FileNotFoundError, match="not registered"):
            docs_management_service.docs_management_post_response(
                root,
                routes.OPEN_DIAGRAM_SOURCE_PATH,
                {
                    "scope": "example",
                    "doc_id": "alpha",
                    "media_identity": "docs/example/svg/architecture.svg",
                    "editor": "vscode",
                },
                dry_run=True,
            )


def test_open_diagram_source_failure_does_not_expose_the_physical_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_mermaid_fixture(root)
        monkeypatch.setattr(
            docs_diagram_source_service.subprocess,
            "run",
            lambda *_args, **_kwargs: SimpleNamespace(
                returncode=1,
                stdout="",
                stderr=f"could not open {managed_media_path(root, 'example', 'source', 'build-source', 'mermaid', 'architecture.mmd')}",
            ),
        )

        with pytest.raises(RuntimeError) as error:
            docs_management_service.docs_management_post_response(
                root,
                routes.OPEN_DIAGRAM_SOURCE_PATH,
                {
                    "scope": "example",
                    "doc_id": "example",
                    "media_identity": "docs/example/svg/architecture.svg",
                    "editor": "vscode",
                },
            )

    assert str(root) not in str(error.value)
