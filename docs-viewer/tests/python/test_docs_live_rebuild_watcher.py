#!/usr/bin/env python3
"""Focused checks for Docs live rebuild watcher imports."""

from __future__ import annotations

import importlib.util
import sys
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


def test_watcher_imports_source_model_helpers_directly() -> None:
    module = load_docs_live_rebuild_watcher_module()

    assert callable(module.load_scope_docs)
    assert callable(module.scope_doc_sort_key)
    assert module.load_scope_docs.__module__ == "docs_source_model"
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
    original_roots = dict(module.SCOPE_ROOTS)

    def config(source: str, sub_scopes=()):
        return SimpleNamespace(
            scope_type="local",
            source=Path(source),
            sub_scopes=tuple(sub_scopes),
        )

    states = {}
    try:
        changes = module.reconcile_watch_states(
            tmp_path,
            states,
            {"notes": config("docs-viewer/source/notes")},
            baseline=False,
        )
        assert changes == {"added": ["notes"], "removed": [], "reloaded": []}
        assert states["notes"]["root"] == tmp_path / "docs-viewer/source/notes"

        changes = module.reconcile_watch_states(
            tmp_path,
            states,
            {"notes": config("external/source/notes")},
            baseline=False,
        )
        assert changes == {"added": [], "removed": [], "reloaded": ["notes"]}
        assert states["notes"]["root"] == tmp_path / "external/source/notes"

        tags = SimpleNamespace(sub_scope="tags", source=Path("external/source/archive/tags"))
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
        assert module.SCOPE_ROOTS == {"archive": Path("external/source/archive")}
    finally:
        module.DOCS_SCOPE_CONFIGS.clear()
        module.DOCS_SCOPE_CONFIGS.update(original_configs)
        module.SCOPE_ROOTS.clear()
        module.SCOPE_ROOTS.update(original_roots)


def test_watcher_formats_affected_doc_ids_for_logs() -> None:
    module = load_docs_live_rebuild_watcher_module()

    assert module.affected_doc_ids_log_text(None) == "full-search fallback"
    assert module.affected_doc_ids_log_text([]) == "none"
    assert module.affected_doc_ids_log_text(["parent", "child"]) == "parent, child"


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
            "--only-doc-ids",
            "tmp",
            "--remove-missing",
        ],
    ]


def main() -> None:
    test_watcher_imports_source_model_helpers_directly()
    test_watcher_accumulates_changed_files_during_debounce()
    test_watcher_formats_affected_doc_ids_for_logs()
    test_watcher_surfaces_direct_edits_without_advanced_full_timestamp()
    test_watcher_formats_docs_builder_diagnostics_on_separate_lines()
    test_watcher_falls_back_to_full_docs_build_when_targeted_payloads_are_missing()


if __name__ == "__main__":
    main()
