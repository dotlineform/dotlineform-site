#!/usr/bin/env python3
"""Focused checks for Docs live rebuild watcher imports."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


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

    assert module.merge_changed_filenames(["new-request.md"], ["change-requests.md"]) == [
        "new-request.md",
        "change-requests.md",
    ]
    assert module.merge_changed_filenames(["new-request.md"], ["new-request.md", "change-requests.md"]) == [
        "new-request.md",
        "change-requests.md",
    ]


def test_watcher_formats_affected_doc_ids_for_logs() -> None:
    module = load_docs_live_rebuild_watcher_module()

    assert module.affected_doc_ids_log_text(None) == "full-search fallback"
    assert module.affected_doc_ids_log_text([]) == "none"
    assert module.affected_doc_ids_log_text(["parent", "child"]) == "parent, child"


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
            "/tmp/bundle",
            "tmp",
            docs_doc_ids=["tmp"],
            search_doc_ids=["tmp"],
        )
    finally:
        module.subprocess.run = original_run
        module.targeted_docs_build_fallback_reason = original_fallback

    assert calls == [
        ["/tmp/bundle", "exec", "ruby", "docs-viewer/build/build_docs.rb", "--scope", "tmp", "--write"],
        [
            "/tmp/bundle",
            "exec",
            "ruby",
            "docs-viewer/build/build_search.rb",
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
    test_watcher_formats_docs_builder_diagnostics_on_separate_lines()
    test_watcher_falls_back_to_full_docs_build_when_targeted_payloads_are_missing()


if __name__ == "__main__":
    main()
