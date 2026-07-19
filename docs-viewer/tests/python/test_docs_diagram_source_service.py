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
from repo_factory import docs_scope_record, write_docs_scope_config


def _configure_mermaid_fixture(root: Path) -> None:
    record = docs_scope_record(
        "library",
        scope_type="public",
        viewer_base_url="/library/",
        include_scope_param=False,
        default_doc_id="library",
        allow_unresolved_parent_ids=True,
        media_provider="repository",
        media_location_root="site/assets/data/docs/scopes/library/media",
        media_served_root="/assets/data/docs/scopes/library/media",
        media_types=("img", "svg", "files", "html"),
    )
    record["source"]["build_media"] = {  # type: ignore[index]
        "mermaid": {
            "path": "media/mermaid",
            "producer": "mermaid",
            "publishes_to": "svg",
        }
    }
    record["published"]["media"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
    write_docs_scope_config(root, [record])

    doc_path = root / "docs-viewer/source/library/documents/library.md"
    doc_path.write_text(
        doc_path.read_text(encoding="utf-8")
        + "\n![Architecture]([[media:docs/library/svg/architecture.svg]])\n"
        + "![Missing]([[media:docs/library/svg/missing.svg]])\n",
        encoding="utf-8",
    )
    source = root / "docs-viewer/source/library/media/mermaid/architecture.mmd"
    source.parent.mkdir(parents=True)
    source.write_text("flowchart LR\nA --> B\n", encoding="utf-8")
    published = root / "site/assets/data/docs/scopes/library/media/svg/architecture.svg"
    published.parent.mkdir(parents=True)
    published.write_text("<svg xmlns='http://www.w3.org/2000/svg'><rect width='1'/></svg>", encoding="utf-8")


def test_manage_diagram_sources_lists_only_verified_same_basename_pairs() -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_mermaid_fixture(root)

        payload = docs_management_service.docs_management_get_payload(
            root,
            routes.DIAGRAM_SOURCES_PATH,
            {"scope": ["library"], "doc_id": ["library"]},
        )

    assert payload == {
        "ok": True,
        "scope": "library",
        "doc_id": "library",
        "sources": [
            {
                "label": "Architecture",
                "media_identity": "docs/library/svg/architecture.svg",
                "source_identity": "architecture.mmd",
                "open_label": "Open in VS Code",
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
                "scope": "library",
                "doc_id": "library",
                "media_identity": "docs/library/svg/architecture.svg",
                "editor": "vscode",
            },
        )

    assert status == HTTPStatus.OK
    assert calls[0][:3] == ["open", "-a", "Visual Studio Code"]
    assert Path(calls[0][3]) == (root / "docs-viewer/source/library/media/mermaid/architecture.mmd").resolve()
    assert payload["source_identity"] == "architecture.mmd"
    assert "path" not in payload
    assert str(root) not in str(payload)


def test_open_diagram_source_rejects_media_not_registered_by_selected_document() -> None:
    with make_repo() as temp:
        root = Path(temp)
        _configure_mermaid_fixture(root)

        with pytest.raises(FileNotFoundError, match="not registered"):
            docs_management_service.docs_management_post_response(
                root,
                routes.OPEN_DIAGRAM_SOURCE_PATH,
                {
                    "scope": "library",
                    "doc_id": "alpha",
                    "media_identity": "docs/library/svg/architecture.svg",
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
                stderr=f"could not open {root}/docs-viewer/source/library/media/mermaid/architecture.mmd",
            ),
        )

        with pytest.raises(RuntimeError) as error:
            docs_management_service.docs_management_post_response(
                root,
                routes.OPEN_DIAGRAM_SOURCE_PATH,
                {
                    "scope": "library",
                    "doc_id": "library",
                    "media_identity": "docs/library/svg/architecture.svg",
                    "editor": "vscode",
                },
            )

    assert str(root) not in str(error.value)
