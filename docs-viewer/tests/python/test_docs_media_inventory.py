#!/usr/bin/env python3
"""Typed Docs media inventory and producer-boundary checks."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
for _path in (REPO_ROOT / "docs-viewer/build", REPO_ROOT / "docs-viewer/services"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


from docs_builder.media_builds import referenced_build_media_identities, run_registered_media_builds
import docs_builder.pipeline as pipeline
from build_docs_test_support import CHILD_DOC_ID, prepare_repo, run_builder, write_source_docs
from docs_media_inventory import inventory_scope_media
from docs_scope_config import load_docs_scope_configs
from repo_factory import docs_scope_record, read_json, write_docs_scope_config, write_json, write_site_tools_config


def write_config(repo_root: Path, record: dict[str, object]) -> None:
    write_docs_scope_config(repo_root, [record])


@pytest.fixture(autouse=True)
def isolated_media_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_base = tmp_path / "projects"
    (projects_base / "docs-viewer/media").mkdir(parents=True)
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))


def configure_mermaid_build(repo_root: Path) -> None:
    config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    payload = read_json(config_path)
    studio = payload["scopes"][0]  # type: ignore[index]
    studio["media"]["build_sources"] = {  # type: ignore[index]
        "mermaid": {
            "producer": "mermaid",
            "publishes_to": "svg",
        }
    }
    studio["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
    write_json(config_path, payload, indent=2)


def test_inventory_lists_unreferenced_owned_media_and_reports_missing_references(tmp_path: Path) -> None:
    write_site_tools_config(tmp_path, media_base="https://media.example.test")
    record = docs_scope_record(
        "library",
        scope_type="public",
        viewer_base_url="/library/",
        include_scope_param=False,
        default_doc_id="library",
        media_types=("img", "svg", "files", "html"),
    )
    write_config(tmp_path, record)
    source = tmp_path / "docs-viewer/scopes/library/source/documents/library.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        """---
doc_id: library
title: Library
---
![Used]([[media:docs/library/img/used.png]])
[[html-media:docs/library/html/widget.html height=320]]
[Missing]([[media:docs/library/files/missing.pdf]])
[Direct route](/assets/data/docs/scopes/library/media/html/widget.html)
""",
        encoding="utf-8",
    )
    media_root = tmp_path / "projects/docs-viewer/media/library"
    html = media_root / "html/widget.html"
    html.parent.mkdir(parents=True)
    html.write_text("<!doctype html><title>Widget</title>", encoding="utf-8")
    (media_root / "img").mkdir(parents=True)
    (media_root / "img/used.png").write_bytes(b"used")
    (media_root / "img/unreferenced.png").write_bytes(b"owned but unreferenced")

    inventory = inventory_scope_media(
        tmp_path,
        load_docs_scope_configs(tmp_path)["library"],
    )

    by_identity = {(item.media_type, item.identity): item for item in inventory.items}
    assert by_identity[("img", "used.png")].document_ids == ("library",)
    assert by_identity[("img", "unreferenced.png")].document_ids == ()
    assert by_identity[("html", "widget.html")].served_path.endswith("/html/widget.html")
    assert [(item.media_type, item.identity) for item in inventory.missing_references] == [
        ("files", "missing.pdf")
    ]


def test_registered_producer_writes_only_to_configured_published_adapter(tmp_path: Path) -> None:
    write_site_tools_config(tmp_path)
    record = docs_scope_record("studio", default_doc_id="studio")
    record["media"]["build_sources"] = {  # type: ignore[index]
        "mermaid": {
            "producer": "fixture-mermaid",
            "publishes_to": "svg",
        }
    }
    record["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
    write_config(tmp_path, record)
    media_root = tmp_path / "projects/docs-viewer/media/studio"
    source = media_root / "build-source/mermaid/diagram.mmd"
    source.parent.mkdir(parents=True)
    source.write_text("graph TD; A-->B", encoding="utf-8")
    config = load_docs_scope_configs(tmp_path)["studio"]

    def producer(context):
        assert [item.identity for item in context.source.list()] == ["diagram.mmd"]
        assert context.requested_published_identities is None
        if context.write:
            context.published.replace("diagram.svg", b"<svg></svg>", content_type="image/svg+xml")
        return ["diagram.svg"]

    dry_run = run_registered_media_builds(
        tmp_path,
        config,
        write=False,
        producers={"fixture-mermaid": producer},
    )
    written = run_registered_media_builds(
        tmp_path,
        config,
        write=True,
        producers={"fixture-mermaid": producer},
    )

    assert dry_run[0]["output_identities"] == ["diagram.svg"]
    assert written[0]["source_count"] == 1
    assert (media_root / "svg/diagram.svg").read_bytes() == b"<svg></svg>"
    assert not (source.parent / "diagram.svg").exists()


def test_registered_producer_receives_create_only_publication_policy(
    tmp_path: Path,
) -> None:
    write_site_tools_config(tmp_path)
    record = docs_scope_record("studio", default_doc_id="studio")
    record["media"]["build_sources"] = {  # type: ignore[index]
        "mermaid": {
            "producer": "fixture-mermaid",
            "publishes_to": "svg",
        }
    }
    record["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
    write_config(tmp_path, record)
    config = load_docs_scope_configs(tmp_path)["studio"]
    policies: list[bool] = []

    def producer(context):
        policies.append(context.replace_existing)
        return []

    run_registered_media_builds(
        tmp_path,
        config,
        write=False,
        producers={"fixture-mermaid": producer},
        replace_existing=False,
    )

    assert policies == [False]


def test_referenced_build_media_identities_select_only_configured_same_scope_outputs(tmp_path: Path) -> None:
    write_site_tools_config(tmp_path)
    record = docs_scope_record("studio", default_doc_id="studio")
    record["media"]["build_sources"] = {  # type: ignore[index]
        "mermaid": {
            "producer": "mermaid",
            "publishes_to": "svg",
        }
    }
    record["media"]["types"]["svg"]["build_inputs"] = ["mermaid"]  # type: ignore[index]
    write_config(tmp_path, record)
    config = load_docs_scope_configs(tmp_path)["studio"]

    requested = referenced_build_media_identities(
        config,
        [
            """![Zeta]([[media:docs/studio/svg/zeta.svg]])
![Measured]([[media:docs/studio/svg/alpha.svg width=800]])
![Duplicate]([[media:docs/studio/svg/zeta.svg]])
![Raster]([[media:docs/studio/img/raster.png]])
![Other scope]([[media:docs/library/svg/other.svg]])
"""
        ],
    )

    assert requested == {"mermaid": ("alpha.svg", "zeta.svg")}


def test_full_and_targeted_builds_invoke_media_stage_with_expected_selection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    prepare_repo(tmp_path)
    configure_mermaid_build(tmp_path)
    write_source_docs(
        tmp_path,
        child_body_suffix="![Referenced diagram]([[media:docs/studio/svg/referenced.svg]])",
    )
    calls: list[tuple[str, bool, object]] = []

    def record_media_build(
        _root,
        config,
        *,
        write,
        requested_published_identities=None,
    ):
        calls.append((config.scope_id, write, requested_published_identities))
        return []

    monkeypatch.setattr(pipeline, "run_registered_media_builds", record_media_build)

    run_builder(tmp_path, write=True)
    run_builder(tmp_path, only_doc_ids=[CHILD_DOC_ID], write=True)
    config = load_docs_scope_configs(tmp_path)["studio"]
    pipeline.DocsDataBuilder(
        repo_root=tmp_path,
        config=config,
        skip_media_builds=True,
    ).run(write=True)

    assert calls == [
        ("studio", True, None),
        (
            "studio",
            True,
            {"mermaid": ("persistent-diagram.svg", "referenced.svg")},
        ),
    ]
