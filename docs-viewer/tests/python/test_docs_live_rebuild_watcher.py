#!/usr/bin/env python3
"""Focused checks for Docs live rebuild watcher imports."""

from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
WATCHER_PATH = REPO_ROOT / "docs-viewer" / "services" / "docs_live_rebuild_watcher.py"


def load_docs_live_rebuild_watcher_module():
    scripts_docs_dir = WATCHER_PATH.parent
    if str(scripts_docs_dir) not in sys.path:
        sys.path.insert(0, str(scripts_docs_dir))
    spec = importlib.util.spec_from_file_location("docs_live_rebuild_watcher", WATCHER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_live_rebuild_watcher.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def timestamp_source_text(
    *,
    doc_id: str,
    title: str,
    summary: str,
    last_updated: str,
    body: str,
) -> str:
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"title: {title}\n"
        "added_date: 2026-07-15 09:00:00\n"
        f"last_updated: {last_updated}\n"
        f"summary: {summary}\n"
        "custom_field: retained\n"
        "---\n"
        f"{body}"
    )


def timestamp_snapshot_row(module, source_text: str) -> dict[str, object]:
    _front_matter_source, front_matter, body = module.split_source_text(source_text)
    return {
        "doc_id": str(front_matter.get("doc_id") or ""),
        "last_updated": str(front_matter.get("last_updated") or ""),
        "recent_edit_content": module.recent_edit_content(front_matter, body),
        "source_revision": module.source_revision(source_text.encode("utf-8")),
    }


def configured_analysis_tags(
    *,
    parent_path: str = "analysis-parent",
    child_path: str = "analysis-tags",
):
    def source(path: str):
        return SimpleNamespace(
            location=SimpleNamespace(path=Path(path)),
            documents_path=Path("documents"),
            build_media={},
        )

    tags = SimpleNamespace(
        sub_scope="tags",
        title="Tags",
        public_title="Concepts",
        ui_statuses=("draft", "done"),
        sub_scope_customisation=SimpleNamespace(
            customisation_id="analysis_tags",
            settings={"groups": ("subject", "domain")},
        ),
        source=source(child_path),
    )
    analysis = SimpleNamespace(
        scope_id="analysis",
        scope_type="public",
        source=source(parent_path),
        media=SimpleNamespace(build_sources={}),
        allow_unresolved_parent_ids=False,
        sub_scopes=(tags,),
    )
    return analysis, tags


def test_watcher_imports_source_model_helpers_directly() -> None:
    module = load_docs_live_rebuild_watcher_module()

    assert callable(module.load_document_collection_docs)
    assert callable(module.scope_doc_sort_key)
    assert module.load_document_collection_docs.__module__ == "docs_source_model"
    assert module.scope_doc_sort_key.__module__ == "docs_source_model"


def test_watcher_accumulates_changed_files_during_debounce() -> None:
    module = load_docs_live_rebuild_watcher_module()

    assert module.merge_changed_filenames(["new-doc.md"], ["roadmap.md"]) == [
        "new-doc.md",
        "roadmap.md",
    ]
    assert module.merge_changed_filenames(["new-doc.md"], ["new-doc.md", "roadmap.md"]) == [
        "new-doc.md",
        "roadmap.md",
    ]


def test_watcher_snapshot_tolerates_file_removed_after_discovery(tmp_path: Path, monkeypatch) -> None:
    module = load_docs_live_rebuild_watcher_module()
    disappearing_path = tmp_path / "disappearing.md"
    disappearing_path.write_text("# Disappearing\n", encoding="utf-8")
    original_stat = module.Path.stat

    def disappearing_stat(path, *args, **kwargs):
        if path == disappearing_path:
            raise FileNotFoundError(path)
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(module.Path, "stat", disappearing_stat)

    assert module.snapshot_scope(tmp_path, "unconfigured-test-scope") == {}
    assert module.snapshot_markdown_root(tmp_path) == {}


def test_watcher_snapshots_only_mermaid_sources_in_build_media_root(tmp_path: Path) -> None:
    module = load_docs_live_rebuild_watcher_module()
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/architecture.mmd").write_text("flowchart LR\nA --> B\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("# Notes\n", encoding="utf-8")

    assert list(module.snapshot_mermaid_root(tmp_path)) == ["nested/architecture.mmd"]


def test_watcher_pauses_and_can_resume_when_scope_root_is_temporarily_missing(tmp_path: Path) -> None:
    module = load_docs_live_rebuild_watcher_module()
    source_root = tmp_path / "source" / "research"
    state = {
        "scope": "research",
        "sub_scope": "",
        "label": "research",
        "root": source_root,
        "snapshot": {"old.md": (1, 1)},
        "doc_snapshot": {"old.md": {"doc_id": "old"}},
        "dirty_at": 1.0,
        "changed_files": ["old.md"],
        "source_missing": False,
    }

    snapshot, error = module.try_state_snapshot(state)

    assert snapshot is None
    assert "Source root not found" in error
    assert module.pause_state_for_missing_source(state) is True
    assert module.pause_state_for_missing_source(state) is False
    assert state["snapshot"] == {}
    assert state["doc_snapshot"] is None
    assert state["dirty_at"] is None
    assert state["changed_files"] == []

    source_root.mkdir(parents=True)
    (source_root / "new.md").write_text("# New\n", encoding="utf-8")
    snapshot, error = module.try_state_snapshot(state)

    assert error == ""
    assert snapshot is not None
    assert list(snapshot) == ["new.md"]


def test_watcher_reconciles_scope_and_sub_scope_state_from_config(tmp_path: Path) -> None:
    module = load_docs_live_rebuild_watcher_module()
    original_configs = dict(module.DOCS_SCOPE_CONFIGS)
    original_roots = dict(module.DOCUMENT_SOURCE_ROOTS)

    def config(source: str, sub_scopes=()):
        return SimpleNamespace(
            scope_type="local",
            source=SimpleNamespace(
                location=SimpleNamespace(path=Path(source)),
                documents_path=Path("documents"),
            ),
            media=SimpleNamespace(build_sources={}),
            sub_scopes=tuple(sub_scopes),
        )

    states = {}
    try:
        changes = module.reconcile_watch_states(
            tmp_path,
            states,
            {"notes": config("docs-viewer/scopes/notes/source")},
            baseline=False,
        )
        assert changes == {"added": ["notes"], "removed": [], "reloaded": []}
        assert states["notes"]["root"] == tmp_path / "docs-viewer/scopes/notes/source/documents"

        changes = module.reconcile_watch_states(
            tmp_path,
            states,
            {"notes": config("external/scopes/notes/source")},
            baseline=False,
        )
        assert changes == {"added": [], "removed": [], "reloaded": ["notes"]}
        assert states["notes"]["root"] == tmp_path / "external/scopes/notes/source/documents"

        tags = SimpleNamespace(
            sub_scope="tags",
            source=SimpleNamespace(
                location=SimpleNamespace(path=Path("external/scopes/notes/source/sub-scopes/tags")),
                documents_path=Path("documents"),
            ),
        )
        changes = module.reconcile_watch_states(
            tmp_path,
            states,
            {"archive": config("external/source/archive", (tags,))},
            baseline=False,
        )
        assert changes == {
            "added": ["archive", "archive/tags"],
            "removed": ["notes"],
            "reloaded": [],
        }
        assert sorted(states) == ["archive", "archive/tags"]
        assert module.DOCUMENT_SOURCE_ROOTS == {"archive": Path("external/source/archive/documents")}
    finally:
        module.DOCS_SCOPE_CONFIGS.clear()
        module.DOCS_SCOPE_CONFIGS.update(original_configs)
        module.DOCUMENT_SOURCE_ROOTS.clear()
        module.DOCUMENT_SOURCE_ROOTS.update(original_roots)


def test_watcher_registers_configured_mermaid_root_and_renders_only_changed_identity(tmp_path: Path) -> None:
    module = load_docs_live_rebuild_watcher_module()
    original_configs = dict(module.DOCS_SCOPE_CONFIGS)
    original_roots = dict(module.DOCUMENT_SOURCE_ROOTS)
    build = SimpleNamespace(
        location=SimpleNamespace(
            provider="repository",
            path=Path("docs-viewer/media/studio/build-source/mermaid"),
        ),
        producer="mermaid",
        publishes_to="svg",
    )
    source = SimpleNamespace(
        location=SimpleNamespace(provider="repository", path=Path("docs-viewer/scopes/studio/source")),
        documents_path=Path("documents"),
        build_media={"mermaid": build},
    )
    published_media = SimpleNamespace(
        location=SimpleNamespace(provider="repository", path=Path("published/svg")),
        served_path_prefix="/docs/media/studio/svg",
    )
    config = SimpleNamespace(
        scope_type="local",
        source=source,
        media=SimpleNamespace(
            build_sources={"mermaid": build},
            types={"svg": published_media},
        ),
        sub_scopes=(),
    )
    calls: list[tuple[str, ...]] = []

    def fake_producer(context):
        calls.append(context.requested_published_identities)
        return context.requested_published_identities

    original_producer = module.produce_mermaid_svg
    module.produce_mermaid_svg = fake_producer
    states: dict[str, dict[str, object]] = {}
    try:
        changes = module.reconcile_watch_states(
            tmp_path,
            states,
            {"studio": config},
            baseline=False,
        )
        media_state = states["studio/media/mermaid"]
        assert media_state["root"] == tmp_path / "docs-viewer/media/studio/build-source/mermaid"
        assert changes["added"] == ["studio", "studio/media/mermaid"]
        assert module.rebuild_build_media(
            tmp_path,
            media_state,
            ["architecture.mmd"],
        )
    finally:
        module.produce_mermaid_svg = original_producer
        module.DOCS_SCOPE_CONFIGS.clear()
        module.DOCS_SCOPE_CONFIGS.update(original_configs)
        module.DOCUMENT_SOURCE_ROOTS.clear()
        module.DOCUMENT_SOURCE_ROOTS.update(original_roots)

    assert calls == [("architecture.svg",)]


def test_watcher_formats_affected_doc_ids_for_logs() -> None:
    module = load_docs_live_rebuild_watcher_module()

    assert module.affected_doc_ids_log_text(None) == "full-search fallback"
    assert module.affected_doc_ids_log_text([]) == "none"
    assert module.affected_doc_ids_log_text(["parent", "child"]) == "parent, child"


def test_watcher_plans_direct_edit_timestamp_evidence_without_writing() -> None:
    module = load_docs_live_rebuild_watcher_module()
    previous = {
        "body.md": {
            "doc_id": "body",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("old body", "Body", ""),
        },
        "summary.md": {
            "doc_id": "summary",
            "last_updated": "2026-07-16 10:00:05",
            "recent_edit_content": ("body", "Summary", "Old summary"),
        },
        "old-title.md": {
            "doc_id": "renamed-title",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("body", "Old title", ""),
        },
        "metadata.md": {
            "doc_id": "metadata",
            "last_updated": "2026-07-16",
            "recent_edit_content": ("body", "Metadata", ""),
        },
        "replaced.md": {
            "doc_id": "old-identity",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("body", "Replaced", ""),
        },
        "ambiguous-a.md": {
            "doc_id": "ambiguous",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("body", "Ambiguous", ""),
        },
        "ambiguous-b.md": {
            "doc_id": "ambiguous",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("body", "Ambiguous", ""),
        },
        "invalid-content.md": {
            "doc_id": "invalid-content",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ["body", "Invalid", ""],
        },
    }
    current = {
        "body.md": {
            "doc_id": "body",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("new body", "Body", ""),
        },
        "summary.md": {
            "doc_id": "summary",
            "last_updated": "2026-07-16",
            "recent_edit_content": ("body", "Summary", "New summary"),
        },
        "renamed-title.md": {
            "doc_id": "renamed-title",
            "last_updated": "2026-07-16 09:59:59",
            "recent_edit_content": ("body", "New title", ""),
        },
        "metadata.md": {
            "doc_id": "metadata",
            "last_updated": "2026-07-16",
            "recent_edit_content": ("body", "Metadata", ""),
        },
        "replaced.md": {
            "doc_id": "new-identity",
            "last_updated": "",
            "recent_edit_content": ("body", "Replaced", ""),
        },
        "ambiguous-new.md": {
            "doc_id": "ambiguous",
            "last_updated": "",
            "recent_edit_content": ("changed body", "Ambiguous", ""),
        },
        "invalid-content.md": {
            "doc_id": "invalid-content",
            "last_updated": "",
            "recent_edit_content": ("changed body", "Invalid", ""),
        },
        "new.md": {
            "doc_id": "new",
            "last_updated": "",
            "recent_edit_content": ("new body", "New", ""),
        },
    }
    previous_before = copy.deepcopy(previous)
    current_before = copy.deepcopy(current)

    plans = module.direct_edit_timestamp_plan(
        previous,
        current,
        [
            "body.md",
            "summary.md",
            "old-title.md",
            "renamed-title.md",
            "metadata.md",
            "replaced.md",
            "ambiguous-new.md",
            "invalid-content.md",
            "new.md",
        ],
        captured_timestamp="2026-07-16 10:00:00",
    )
    plans_by_filename = {plan["filename"]: plan for plan in plans}

    assert previous == previous_before
    assert current == current_before
    assert list(plans_by_filename) == [
        "body.md",
        "summary.md",
        "renamed-title.md",
        "metadata.md",
        "replaced.md",
        "ambiguous-new.md",
        "invalid-content.md",
        "new.md",
    ]
    assert plans_by_filename["body.md"] == {
        "filename": "body.md",
        "previous_filename": "body.md",
        "doc_id": "body",
        "matched": True,
        "qualifying_content_changed": True,
        "manual_timestamp_evidence": False,
        "requires_rewrite": True,
        "previous_last_updated": "2026-07-16 10:00:00",
        "current_last_updated": "2026-07-16 10:00:00",
        "previous_source_revision": "",
        "current_source_revision": "",
        "replacement_last_updated": "2026-07-16 10:00:06",
        "reason": "last_updated_not_advanced",
    }
    assert plans_by_filename["summary.md"]["qualifying_content_changed"] is True
    assert plans_by_filename["summary.md"]["requires_rewrite"] is True
    assert plans_by_filename["summary.md"]["replacement_last_updated"] == (
        "2026-07-16 10:00:06"
    )
    assert plans_by_filename["summary.md"]["reason"] == "invalid_last_updated"
    assert plans_by_filename["renamed-title.md"] == {
        "filename": "renamed-title.md",
        "previous_filename": "old-title.md",
        "doc_id": "renamed-title",
        "matched": True,
        "qualifying_content_changed": True,
        "manual_timestamp_evidence": True,
        "requires_rewrite": False,
        "previous_last_updated": "2026-07-16 10:00:00",
        "current_last_updated": "2026-07-16 09:59:59",
        "previous_source_revision": "",
        "current_source_revision": "",
        "replacement_last_updated": "",
        "reason": "manual_full_timestamp",
    }
    assert plans_by_filename["metadata.md"]["qualifying_content_changed"] is False
    assert plans_by_filename["metadata.md"]["reason"] == "recent_edit_content_unchanged"
    assert plans_by_filename["metadata.md"]["requires_rewrite"] is False
    assert plans_by_filename["replaced.md"]["matched"] is False
    assert plans_by_filename["replaced.md"]["reason"] == "document_identity_changed"
    assert plans_by_filename["ambiguous-new.md"]["matched"] is False
    assert plans_by_filename["ambiguous-new.md"]["reason"] == "ambiguous_previous_identity"
    assert plans_by_filename["invalid-content.md"]["matched"] is True
    assert plans_by_filename["invalid-content.md"]["reason"] == "invalid_recent_edit_content"
    assert plans_by_filename["invalid-content.md"]["requires_rewrite"] is False
    assert plans_by_filename["new.md"]["matched"] is False
    assert plans_by_filename["new.md"]["reason"] == "no_previous_document"
    assert plans_by_filename["new.md"]["requires_rewrite"] is False


def test_watcher_timestamp_plan_fails_closed_without_valid_snapshot_or_capture() -> None:
    module = load_docs_live_rebuild_watcher_module()
    current = {
        "doc.md": {
            "doc_id": "doc",
            "last_updated": "",
            "recent_edit_content": ("body", "Doc", ""),
        }
    }

    assert module.direct_edit_timestamp_plan(
        None,
        current,
        ["doc.md"],
        captured_timestamp="2026-07-16 10:00:00",
    ) == [
        {
            "filename": "doc.md",
            "previous_filename": "",
            "doc_id": "doc",
            "matched": False,
            "qualifying_content_changed": None,
            "manual_timestamp_evidence": False,
            "requires_rewrite": False,
            "previous_last_updated": "",
            "current_last_updated": "",
            "previous_source_revision": "",
            "current_source_revision": "",
            "replacement_last_updated": "",
            "reason": "missing_previous_snapshot",
        }
    ]

    try:
        module.direct_edit_timestamp_plan(
            {},
            current,
            ["doc.md"],
            captured_timestamp="2026-07-16",
        )
    except ValueError as exc:
        assert "YYYY-MM-DD HH:MM:SS" in str(exc)
    else:
        raise AssertionError("invalid batch timestamp should block timestamp planning")


def test_watcher_invalid_parsed_snapshot_fails_closed() -> None:
    module = load_docs_live_rebuild_watcher_module()
    original_snapshot = module.parsed_doc_snapshot

    def fail_snapshot(
        _repo_root: Path,
        _scope: str,
        _sub_scope: str = "",
    ):
        raise ValueError("simulated invalid source")

    module.parsed_doc_snapshot = fail_snapshot
    try:
        snapshot, error = module.try_parsed_doc_snapshot(Path("/repo"), "studio")
    finally:
        module.parsed_doc_snapshot = original_snapshot

    assert snapshot is None
    assert error == "simulated invalid source"


def test_watcher_sub_scope_snapshot_and_baseline_are_exact() -> None:
    module = load_docs_live_rebuild_watcher_module()
    analysis, _tags = configured_analysis_tags()
    original_configs = dict(module.DOCS_SCOPE_CONFIGS)
    original_roots = dict(module.DOCUMENT_SOURCE_ROOTS)

    with tempfile.TemporaryDirectory() as temp:
        repo_root = Path(temp)
        parent_root = repo_root / "analysis-parent/documents"
        child_root = repo_root / "analysis-tags/documents"
        parent_root.mkdir(parents=True)
        child_root.mkdir(parents=True)
        parent_root.joinpath("shared.md").write_text(
            timestamp_source_text(
                doc_id="shared",
                title="Parent version",
                summary="",
                last_updated="2026-07-16 10:00:00",
                body="# Parent\n",
            ),
            encoding="utf-8",
        )
        child_root.joinpath("shared.md").write_text(
            timestamp_source_text(
                doc_id="shared",
                title="Tag version",
                summary="",
                last_updated="2026-07-16 10:00:00",
                body="# Tag\n",
            ),
            encoding="utf-8",
        )
        try:
            module.sync_scope_config_globals({"analysis": analysis})
            parent_snapshot = module.parsed_doc_snapshot(
                repo_root,
                "analysis",
            )
            child_snapshot = module.parsed_doc_snapshot(
                repo_root,
                "analysis",
                "tags",
            )
            missing_snapshot, missing_error = module.try_parsed_doc_snapshot(
                repo_root,
                "analysis",
                "missing",
            )
            child_spec = module.desired_watch_state_specs(
                repo_root,
                {"analysis": analysis},
            )["analysis/tags"]
            child_state = module.new_watch_state(
                repo_root,
                child_spec,
                baseline=True,
            )
        finally:
            module.DOCS_SCOPE_CONFIGS.clear()
            module.DOCS_SCOPE_CONFIGS.update(original_configs)
            module.DOCUMENT_SOURCE_ROOTS.clear()
            module.DOCUMENT_SOURCE_ROOTS.update(original_roots)

    assert parent_snapshot["shared.md"]["title"] == "Parent version"
    assert child_snapshot["shared.md"]["title"] == "Tag version"
    assert child_state["doc_snapshot"]["shared.md"]["title"] == "Tag version"
    assert child_state["root"] == child_root
    assert missing_snapshot is None
    assert "unknown sub_scope 'missing' for scope 'analysis'" in missing_error


def test_parent_watcher_rewrites_body_title_and_summary_once_then_adopts() -> None:
    module = load_docs_live_rebuild_watcher_module()
    previous_sources = {
        "body.md": timestamp_source_text(
            doc_id="body",
            title="Body",
            summary="Summary",
            last_updated="2026-07-16 10:00:00",
            body="# Old body\n",
        ),
        "title.md": timestamp_source_text(
            doc_id="title",
            title="Old title",
            summary="Summary",
            last_updated="2026-07-16 10:00:00",
            body="# Body\n",
        ),
        "summary.md": timestamp_source_text(
            doc_id="summary",
            title="Summary",
            summary="Old summary",
            last_updated="2026-07-16 10:00:00",
            body="# Body\n",
        ),
    }
    current_sources = {
        "body.md": timestamp_source_text(
            doc_id="body",
            title="Body",
            summary="Summary",
            last_updated="2026-07-16 10:00:00",
            body="# New body\n",
        ),
        "title.md": timestamp_source_text(
            doc_id="title",
            title="New title",
            summary="Summary",
            last_updated="2026-07-16 10:00:00",
            body="# Body\n",
        ),
        "summary.md": timestamp_source_text(
            doc_id="summary",
            title="Summary",
            summary="New summary",
            last_updated="2026-07-16 10:00:00",
            body="# Body\n",
        ),
    }

    with tempfile.TemporaryDirectory() as temp:
        source_root = Path(temp)
        for filename, source_text in current_sources.items():
            (source_root / filename).write_text(source_text, encoding="utf-8")
        previous = {
            filename: timestamp_snapshot_row(module, source_text)
            for filename, source_text in previous_sources.items()
        }
        current = {
            filename: timestamp_snapshot_row(module, source_text)
            for filename, source_text in current_sources.items()
        }
        state = {"snapshot": module.snapshot_markdown_root(source_root)}
        plans = module.direct_edit_timestamp_plan(
            previous,
            current,
            list(current_sources),
            captured_timestamp="2026-07-16 10:00:00",
        )

        result = module.apply_collection_timestamp_rewrites(
            source_root,
            plans,
        )
        adopted = module.adopt_collection_timestamp_rewrites(
            state,
            current,
            result,
        )

        assert result["conflicts"] == []
        assert result["failures"] == []
        assert adopted == ["body.md", "title.md", "summary.md"]
        assert {
            record["last_updated"]
            for record in result["rewritten"]
        } == {"2026-07-16 10:00:01"}
        assert state["snapshot"] == module.snapshot_markdown_root(source_root)

        fresh = {}
        for filename in current_sources:
            rewritten_text = (source_root / filename).read_text(encoding="utf-8")
            fresh[filename] = timestamp_snapshot_row(module, rewritten_text)
            assert fresh[filename]["last_updated"] == "2026-07-16 10:00:01"
            assert "custom_field: retained" in rewritten_text
        assert fresh["body.md"]["recent_edit_content"][0] == "# New body\n"
        assert fresh["title.md"]["recent_edit_content"][1] == "New title"
        assert fresh["summary.md"]["recent_edit_content"][2] == "New summary"

        next_plans = module.direct_edit_timestamp_plan(
            current,
            fresh,
            list(current_sources),
            captured_timestamp="2026-07-16 10:00:02",
        )
        assert all(not plan["requires_rewrite"] for plan in next_plans)
        assert all(
            not plan["qualifying_content_changed"]
            for plan in next_plans
        )


def test_parent_watcher_capture_runs_one_existing_rebuild() -> None:
    module = load_docs_live_rebuild_watcher_module()
    previous_source = timestamp_source_text(
        doc_id="doc",
        title="Doc",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# Old body\n",
    )
    current_source = timestamp_source_text(
        doc_id="doc",
        title="Doc",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# Current body\n",
    )
    original_snapshot = module.try_parsed_doc_snapshot
    original_rebuild = module.rebuild_scope
    original_timestamp = module.current_doc_timestamp
    original_log = module.log
    rebuilds = []
    logs = []

    with tempfile.TemporaryDirectory() as temp:
        repo_root = Path(temp)
        source_root = repo_root / "source"
        source_root.mkdir()
        (source_root / "doc.md").write_text(current_source, encoding="utf-8")
        previous = {"doc.md": timestamp_snapshot_row(module, previous_source)}
        current = {"doc.md": timestamp_snapshot_row(module, current_source)}
        state = {
            "scope": "studio",
            "root": source_root,
            "doc_snapshot": previous,
            "snapshot": module.snapshot_markdown_root(source_root),
        }

        module.try_parsed_doc_snapshot = (
            lambda _root, _scope, _sub_scope="": (current, "")
        )
        module.current_doc_timestamp = lambda: "2026-07-16 10:00:01"
        module.rebuild_scope = lambda *args, **kwargs: (
            rebuilds.append((args, kwargs)) or True
        )
        module.log = logs.append
        try:
            rebuilt, adopted_docs = module.process_document_collection_changes(
                repo_root,
                state,
                ["doc.md"],
                targeted_docs_threshold=5,
            )
        finally:
            module.try_parsed_doc_snapshot = original_snapshot
            module.rebuild_scope = original_rebuild
            module.current_doc_timestamp = original_timestamp
            module.log = original_log

        assert rebuilt is True
        assert adopted_docs is current
        assert current["doc.md"]["last_updated"] == "2026-07-16 10:00:01"
        assert state["snapshot"] == module.snapshot_markdown_root(source_root)
        assert rebuilds == [
            (
                (repo_root, "studio"),
                {
                    "docs_doc_ids": ["doc"],
                    "search_doc_ids": ["doc"],
                },
            )
        ]
        assert any(
            message
            == (
                "studio captured last_updated for direct source edits: "
                "doc.md (doc)."
            )
            for message in logs
        )


def test_sub_scope_watcher_captures_preserves_and_rebuilds_exact_collection_once() -> None:
    module = load_docs_live_rebuild_watcher_module()
    analysis, _tags = configured_analysis_tags()
    original_configs = dict(module.DOCS_SCOPE_CONFIGS)
    original_roots = dict(module.DOCUMENT_SOURCE_ROOTS)
    original_timestamp = module.current_doc_timestamp
    original_parent_rebuild = module.rebuild_scope
    original_sub_scope_rebuild = module.rebuild_sub_scope
    original_log = module.log
    rebuilds: list[tuple[Path, str, str]] = []
    logs: list[str] = []
    previous_sources = {
        "body.md": timestamp_source_text(
            doc_id="body",
            title="Body",
            summary="",
            last_updated="2026-07-16 10:00:00",
            body="# Old body\n",
        ),
        "summary.md": timestamp_source_text(
            doc_id="summary",
            title="Summary",
            summary="Old summary",
            last_updated="2026-07-16 10:00:00",
            body="# Body\n",
        ),
        "manual.md": timestamp_source_text(
            doc_id="manual",
            title="Old title",
            summary="",
            last_updated="2026-07-16 10:00:00",
            body="# Body\n",
        ),
    }
    current_sources = {
        "body.md": timestamp_source_text(
            doc_id="body",
            title="Body",
            summary="",
            last_updated="2026-07-16 10:00:00",
            body="# New body\n",
        ),
        "summary.md": timestamp_source_text(
            doc_id="summary",
            title="Summary",
            summary="New summary",
            last_updated="2026-07-16 10:00:00",
            body="# Body\n",
        ),
        "manual.md": timestamp_source_text(
            doc_id="manual",
            title="New title",
            summary="",
            last_updated="2026-07-16 10:00:05",
            body="# Body\n",
        ),
    }

    with tempfile.TemporaryDirectory() as temp:
        repo_root = Path(temp)
        parent_root = repo_root / "analysis-parent/documents"
        child_root = repo_root / "analysis-tags/documents"
        parent_root.mkdir(parents=True)
        child_root.mkdir(parents=True)
        parent_source = timestamp_source_text(
            doc_id="parent-body",
            title="Parent body",
            summary="",
            last_updated="2026-07-16 09:00:00",
            body="# Parent source remains untouched\n",
        )
        parent_root.joinpath("body.md").write_text(
            parent_source,
            encoding="utf-8",
        )
        for filename, source_text in previous_sources.items():
            child_root.joinpath(filename).write_text(
                source_text,
                encoding="utf-8",
            )
        try:
            module.sync_scope_config_globals({"analysis": analysis})
            previous_docs = module.parsed_doc_snapshot(
                repo_root,
                "analysis",
                "tags",
            )
            for filename, source_text in current_sources.items():
                child_root.joinpath(filename).write_text(
                    source_text,
                    encoding="utf-8",
                )
            state = {
                "scope": "analysis",
                "sub_scope": "tags",
                "label": "analysis/tags",
                "root": child_root,
                "doc_snapshot": previous_docs,
                "snapshot": module.snapshot_markdown_root(child_root),
            }
            module.current_doc_timestamp = lambda: "2026-07-16 10:00:00"
            module.rebuild_scope = lambda *_args, **_kwargs: (
                (_ for _ in ()).throw(
                    AssertionError("sub-scope processing must not rebuild parent")
                )
            )
            module.rebuild_sub_scope = lambda root, scope, sub_scope: (
                rebuilds.append((root, scope, sub_scope)) or True
            )
            module.log = logs.append

            rebuilt, adopted_docs = (
                module.process_document_collection_changes(
                    repo_root,
                    state,
                    list(current_sources),
                    targeted_docs_threshold=5,
                )
            )
            fresh_docs = module.parsed_doc_snapshot(
                repo_root,
                "analysis",
                "tags",
            )
            no_loop_plans = module.direct_edit_timestamp_plan(
                adopted_docs,
                fresh_docs,
                list(current_sources),
                captured_timestamp="2026-07-16 10:00:06",
            )
        finally:
            module.current_doc_timestamp = original_timestamp
            module.rebuild_scope = original_parent_rebuild
            module.rebuild_sub_scope = original_sub_scope_rebuild
            module.log = original_log
            module.DOCS_SCOPE_CONFIGS.clear()
            module.DOCS_SCOPE_CONFIGS.update(original_configs)
            module.DOCUMENT_SOURCE_ROOTS.clear()
            module.DOCUMENT_SOURCE_ROOTS.update(original_roots)

        assert rebuilt is True
        assert rebuilds == [(repo_root, "analysis", "tags")]
        assert state["snapshot"] == module.snapshot_markdown_root(child_root)
        assert parent_root.joinpath("body.md").read_text(
            encoding="utf-8"
        ) == parent_source
        assert fresh_docs["body.md"]["last_updated"] == "2026-07-16 10:00:01"
        assert fresh_docs["summary.md"]["last_updated"] == "2026-07-16 10:00:01"
        assert fresh_docs["manual.md"]["last_updated"] == "2026-07-16 10:00:05"
        assert all(not plan["requires_rewrite"] for plan in no_loop_plans)
        assert all(
            not plan["qualifying_content_changed"]
            for plan in no_loop_plans
        )
        assert (
            "analysis/tags captured last_updated for direct source edits: "
            "body.md (body), summary.md (summary)."
        ) in logs


def test_sub_scope_watcher_timestamp_failure_keeps_source_and_rebuilds_once() -> None:
    module = load_docs_live_rebuild_watcher_module()
    analysis, _tags = configured_analysis_tags()
    original_configs = dict(module.DOCS_SCOPE_CONFIGS)
    original_roots = dict(module.DOCUMENT_SOURCE_ROOTS)
    original_timestamp = module.current_doc_timestamp
    original_write = module.write_text_atomic
    original_sub_scope_rebuild = module.rebuild_sub_scope
    original_log = module.log
    rebuilds: list[tuple[Path, str, str]] = []
    logs: list[str] = []
    previous_source = timestamp_source_text(
        doc_id="failure",
        title="Failure",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# Old body\n",
    )
    current_source = timestamp_source_text(
        doc_id="failure",
        title="Failure",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# New body\n",
    )

    with tempfile.TemporaryDirectory() as temp:
        repo_root = Path(temp)
        child_root = repo_root / "analysis-tags/documents"
        child_root.mkdir(parents=True)
        path = child_root / "failure.md"
        path.write_text(previous_source, encoding="utf-8")
        try:
            module.sync_scope_config_globals({"analysis": analysis})
            previous_docs = module.parsed_doc_snapshot(
                repo_root,
                "analysis",
                "tags",
            )
            path.write_text(current_source, encoding="utf-8")
            state = {
                "scope": "analysis",
                "sub_scope": "tags",
                "label": "analysis/tags",
                "root": child_root,
                "doc_snapshot": previous_docs,
                "snapshot": module.snapshot_markdown_root(child_root),
            }
            module.current_doc_timestamp = lambda: "2026-07-16 10:00:01"
            module.write_text_atomic = lambda _path, _text: (
                (_ for _ in ()).throw(
                    OSError("simulated sub-scope timestamp write failure")
                )
            )
            module.rebuild_sub_scope = lambda root, scope, sub_scope: (
                rebuilds.append((root, scope, sub_scope)) or True
            )
            module.log = logs.append

            rebuilt, current_docs = (
                module.process_document_collection_changes(
                    repo_root,
                    state,
                    ["failure.md"],
                    targeted_docs_threshold=5,
                )
            )
        finally:
            module.current_doc_timestamp = original_timestamp
            module.write_text_atomic = original_write
            module.rebuild_sub_scope = original_sub_scope_rebuild
            module.log = original_log
            module.DOCS_SCOPE_CONFIGS.clear()
            module.DOCS_SCOPE_CONFIGS.update(original_configs)
            module.DOCUMENT_SOURCE_ROOTS.clear()
            module.DOCUMENT_SOURCE_ROOTS.update(original_roots)

        assert rebuilt is True
        assert current_docs["failure.md"]["last_updated"] == (
            "2026-07-16 10:00:00"
        )
        assert path.read_text(encoding="utf-8") == current_source
        assert rebuilds == [(repo_root, "analysis", "tags")]
        assert any(
            message.startswith(
                "analysis/tags timestamp capture failed for "
                "failure.md (failure): simulated sub-scope"
            )
            for message in logs
        )


def test_parent_watcher_timestamp_write_refuses_a_stale_source_revision() -> None:
    module = load_docs_live_rebuild_watcher_module()
    previous_source = timestamp_source_text(
        doc_id="doc",
        title="Doc",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# Old body\n",
    )
    planned_source = timestamp_source_text(
        doc_id="doc",
        title="Doc",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# Planned body\n",
    )
    later_source = timestamp_source_text(
        doc_id="doc",
        title="Doc",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# Later body\n",
    )

    with tempfile.TemporaryDirectory() as temp:
        source_root = Path(temp)
        path = source_root / "doc.md"
        path.write_text(planned_source, encoding="utf-8")
        plans = module.direct_edit_timestamp_plan(
            {"doc.md": timestamp_snapshot_row(module, previous_source)},
            {"doc.md": timestamp_snapshot_row(module, planned_source)},
            ["doc.md"],
            captured_timestamp="2026-07-16 10:00:01",
        )
        path.write_text(later_source, encoding="utf-8")

        result = module.apply_collection_timestamp_rewrites(
            source_root,
            plans,
        )

        assert result == {
            "rewritten": [],
            "conflicts": [
                {
                    "filename": "doc.md",
                    "doc_id": "doc",
                    "reason": "source changed after timestamp planning",
                }
            ],
            "failures": [],
        }
        assert path.read_text(encoding="utf-8") == later_source


def test_parent_watcher_timestamp_write_failure_leaves_source_for_retry() -> None:
    module = load_docs_live_rebuild_watcher_module()
    previous_source = timestamp_source_text(
        doc_id="doc",
        title="Doc",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# Old body\n",
    )
    current_source = timestamp_source_text(
        doc_id="doc",
        title="Doc",
        summary="",
        last_updated="2026-07-16 10:00:00",
        body="# Current body\n",
    )
    original_write = module.write_text_atomic

    def fail_write(_path: Path, _text: str) -> None:
        raise OSError("simulated timestamp write failure")

    with tempfile.TemporaryDirectory() as temp:
        source_root = Path(temp)
        path = source_root / "doc.md"
        path.write_text(current_source, encoding="utf-8")
        plans = module.direct_edit_timestamp_plan(
            {"doc.md": timestamp_snapshot_row(module, previous_source)},
            {"doc.md": timestamp_snapshot_row(module, current_source)},
            ["doc.md"],
            captured_timestamp="2026-07-16 10:00:01",
        )
        module.write_text_atomic = fail_write
        try:
            result = module.apply_collection_timestamp_rewrites(
                source_root,
                plans,
            )
        finally:
            module.write_text_atomic = original_write

        assert result == {
            "rewritten": [],
            "conflicts": [],
            "failures": [
                {
                    "filename": "doc.md",
                    "doc_id": "doc",
                    "reason": "simulated timestamp write failure",
                }
            ],
        }
        assert path.read_text(encoding="utf-8") == current_source


def test_parent_watcher_leaves_managed_and_nonqualifying_edits_untouched() -> None:
    module = load_docs_live_rebuild_watcher_module()
    previous = {
        "source.md": {
            "doc_id": "source",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("old body", "Source", ""),
        },
        "metadata.md": {
            "doc_id": "metadata",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("body", "Old title", ""),
        },
        "import.md": {
            "doc_id": "import",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("old body", "Import", ""),
        },
        "placement.md": {
            "doc_id": "placement",
            "last_updated": "2026-07-16",
            "recent_edit_content": ("body", "Placement", ""),
        },
        "old-name.md": {
            "doc_id": "rename",
            "last_updated": "2026-07-16",
            "recent_edit_content": ("body", "Rename", ""),
        },
    }
    current = {
        "source.md": {
            "doc_id": "source",
            "last_updated": "2026-07-16 10:00:01",
            "recent_edit_content": ("new body", "Source", ""),
        },
        "metadata.md": {
            "doc_id": "metadata",
            "last_updated": "2026-07-16 10:00:01",
            "recent_edit_content": ("body", "New title", ""),
        },
        "import.md": {
            "doc_id": "import",
            "last_updated": "2026-07-16 10:00:01",
            "recent_edit_content": ("new body", "Import", ""),
        },
        "placement.md": {
            "doc_id": "placement",
            "last_updated": "2026-07-16",
            "recent_edit_content": ("body", "Placement", ""),
        },
        "new-name.md": {
            "doc_id": "rename",
            "last_updated": "2026-07-16",
            "recent_edit_content": ("body", "Rename", ""),
        },
        "new.md": {
            "doc_id": "new",
            "last_updated": "",
            "recent_edit_content": ("body", "New", ""),
        },
    }

    plans = module.direct_edit_timestamp_plan(
        previous,
        current,
        list(current),
        captured_timestamp="2026-07-16 10:00:02",
    )

    assert all(not plan["requires_rewrite"] for plan in plans)
    assert module.apply_collection_timestamp_rewrites(
        Path("/unused"),
        plans,
    ) == {
        "rewritten": [],
        "conflicts": [],
        "failures": [],
    }


def test_watcher_surfaces_direct_edits_without_advanced_full_timestamp() -> None:
    module = load_docs_live_rebuild_watcher_module()
    previous = {
        "changed.md": {
            "doc_id": "changed",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("old body", "Changed", ""),
        },
        "invalid.md": {
            "doc_id": "invalid",
            "last_updated": "2026-07-15 10:00:00",
            "recent_edit_content": ("body", "Invalid", "old summary"),
        },
        "valid.md": {
            "doc_id": "valid",
            "last_updated": "2026-07-15 10:00:00",
            "recent_edit_content": ("body", "Valid", ""),
        },
        "metadata.md": {
            "doc_id": "metadata",
            "last_updated": "2026-07-15",
            "recent_edit_content": ("body", "Metadata", ""),
        },
        "old-name.md": {
            "doc_id": "old-id",
            "last_updated": "2026-07-15",
            "recent_edit_content": ("renamed body", "Renamed", ""),
        },
    }
    current = {
        "changed.md": {
            "doc_id": "changed",
            "last_updated": "2026-07-16 10:00:00",
            "recent_edit_content": ("new body", "Changed", ""),
        },
        "invalid.md": {
            "doc_id": "invalid",
            "last_updated": "2026-07-16",
            "recent_edit_content": ("body", "Invalid", "new summary"),
        },
        "valid.md": {
            "doc_id": "valid",
            "last_updated": "2026-07-16 11:00:00",
            "recent_edit_content": ("body", "Valid title", ""),
        },
        "metadata.md": {
            "doc_id": "metadata",
            "last_updated": "2026-07-15",
            "recent_edit_content": ("body", "Metadata", ""),
        },
        "new-name.md": {
            "doc_id": "new-id",
            "last_updated": "2026-07-15",
            "recent_edit_content": ("renamed body", "Renamed", ""),
        },
        "new.md": {
            "doc_id": "new",
            "last_updated": "",
            "recent_edit_content": ("new body", "New", ""),
        },
    }

    assert module.direct_edit_timestamp_issues(
        previous,
        current,
        [
            "changed.md",
            "invalid.md",
            "valid.md",
            "metadata.md",
            "old-name.md",
            "new-name.md",
            "new.md",
            "deleted.md",
        ],
    ) == [
        {
            "filename": "changed.md",
            "doc_id": "changed",
            "reason": "last_updated did not advance",
        },
        {
            "filename": "invalid.md",
            "doc_id": "invalid",
            "reason": "last_updated is not a full timestamp",
        },
        {
            "filename": "new-name.md",
            "doc_id": "new-id",
            "reason": "new source lacks a full last_updated timestamp",
        },
        {
            "filename": "new.md",
            "doc_id": "new",
            "reason": "new source lacks a full last_updated timestamp",
        },
    ]


def test_watcher_formats_docs_builder_diagnostics_on_separate_lines() -> None:
    module = load_docs_live_rebuild_watcher_module()
    stdout = (
        'Docs builder diagnostics: {"scope":"studio","source_files_scanned":3,'
        '"docs_emitted":2,"warnings":[],"elapsed_seconds":0.25}\n'
    )

    assert module.formatted_docs_builder_diagnostics(stdout) == [
        "scope: studio",
        "source_files_scanned: 3",
        "docs_emitted: 2",
        "warnings: []",
        "elapsed_seconds: 0.25",
    ]


def test_sub_scope_rebuild_runs_child_docs_then_full_parent_search() -> None:
    module = load_docs_live_rebuild_watcher_module()
    calls: list[list[str]] = []
    original_run = module.subprocess.run
    original_log = module.log

    class Completed:
        returncode = 0
        stdout = "done\n"
        stderr = ""

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    module.subprocess.run = fake_run
    module.log = lambda _message: None
    try:
        assert module.rebuild_sub_scope(Path("/repo"), "analysis", "tags")
    finally:
        module.subprocess.run = original_run
        module.log = original_log

    assert calls == [
        [
            module.PYTHON_EXECUTABLE,
            "docs-viewer/build/build_docs.py",
            "--scope",
            "analysis",
            "--sub-scope",
            "tags",
            "--write",
            "--diagnostics",
        ],
        [
            module.PYTHON_EXECUTABLE,
            "docs-viewer/build/build_search.py",
            "--scope",
            "analysis",
            "--write",
        ],
    ]


def test_watcher_falls_back_to_full_docs_build_when_targeted_payloads_are_missing() -> None:
    module = load_docs_live_rebuild_watcher_module()
    calls: list[list[str]] = []
    original_run = module.subprocess.run
    original_fallback = module.targeted_docs_build_fallback_reason

    class Completed:
        returncode = 0
        stdout = "ok\n"
        stderr = ""

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    module.subprocess.run = fake_run
    module.targeted_docs_build_fallback_reason = lambda *_args, **_kwargs: (
        "full-scope fallback: existing payloads missing for unselected docs"
    )
    try:
        assert module.rebuild_scope(
            Path("/repo"),
            "tmp",
            docs_doc_ids=["tmp"],
            search_doc_ids=["tmp"],
        )
    finally:
        module.subprocess.run = original_run
        module.targeted_docs_build_fallback_reason = original_fallback

    assert calls == [
        [module.PYTHON_EXECUTABLE, "docs-viewer/build/build_docs.py", "--scope", "tmp", "--write", "--diagnostics"],
        [
            module.PYTHON_EXECUTABLE,
            "docs-viewer/build/build_search.py",
            "--scope",
            "tmp",
            "--write",
        ],
    ]


def main() -> None:
    test_watcher_imports_source_model_helpers_directly()
    test_watcher_accumulates_changed_files_during_debounce()
    test_watcher_formats_affected_doc_ids_for_logs()
    test_watcher_plans_direct_edit_timestamp_evidence_without_writing()
    test_watcher_timestamp_plan_fails_closed_without_valid_snapshot_or_capture()
    test_watcher_invalid_parsed_snapshot_fails_closed()
    test_watcher_sub_scope_snapshot_and_baseline_are_exact()
    test_parent_watcher_rewrites_body_title_and_summary_once_then_adopts()
    test_parent_watcher_capture_runs_one_existing_rebuild()
    test_sub_scope_watcher_captures_preserves_and_rebuilds_exact_collection_once()
    test_sub_scope_watcher_timestamp_failure_keeps_source_and_rebuilds_once()
    test_parent_watcher_timestamp_write_refuses_a_stale_source_revision()
    test_parent_watcher_timestamp_write_failure_leaves_source_for_retry()
    test_parent_watcher_leaves_managed_and_nonqualifying_edits_untouched()
    test_watcher_surfaces_direct_edits_without_advanced_full_timestamp()
    test_watcher_formats_docs_builder_diagnostics_on_separate_lines()
    test_watcher_falls_back_to_full_docs_build_when_targeted_payloads_are_missing()


if __name__ == "__main__":
    main()
