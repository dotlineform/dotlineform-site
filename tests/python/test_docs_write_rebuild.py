#!/usr/bin/env python3
"""Focused checks for Docs Management write/rebuild helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DOCS_DIR = REPO_ROOT / "scripts" / "docs"
if str(SCRIPTS_DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_DIR))

import docs_write_rebuild as write_rebuild  # noqa: E402


class Completed:
    def __init__(self, returncode: int = 0, stdout: str = "ok\n", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


DOCS_DIAGNOSTICS_STDOUT = (
    'Docs JSON done for scope studio.\n'
    'Docs builder diagnostics: {"scope":"studio","source_files_scanned":10,'
    '"docs_emitted":9,"doc_payloads_changed":1,"doc_payloads_removed":0,'
    '"reference_index_changed":0,"reference_by_doc_payloads_changed":0,'
    '"reference_by_doc_payloads_removed":0,"reference_by_target_payloads_changed":0,'
    '"reference_by_target_payloads_removed":0,"warning_count":0,"warnings":[],'
    '"elapsed_seconds":0.123}\n'
)


def with_fake_bundle(value: str = "/tmp/bundle"):
    original = write_rebuild.detect_bundle_bin
    write_rebuild.detect_bundle_bin = lambda: value
    return original


def test_rebuild_scope_outputs_preserves_full_command_shapes() -> None:
    calls: list[tuple[list[str], str]] = []
    original_bundle = with_fake_bundle()
    original_run = write_rebuild.subprocess.run

    def fake_run(command, **kwargs):
        calls.append((list(command), kwargs["cwd"]))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            result = write_rebuild.rebuild_scope_outputs(Path(temp_path), "studio")
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.detect_bundle_bin = original_bundle

    assert result["ok"] is True
    assert result["docs"] == {
        "mode": "full",
        "doc_ids": [],
        "reason": "full-scope fallback: no targeted docs payload ids provided",
    }
    assert result["search"] == {"mode": "full", "doc_ids": []}
    assert calls == [
        (["/tmp/bundle", "exec", "ruby", "scripts/build_docs.rb", "--scope", "studio", "--write"], calls[0][1]),
        (["/tmp/bundle", "exec", "ruby", "scripts/build_search.rb", "--scope", "studio", "--write"], calls[0][1]),
    ]
    assert result["diagnostics"]["search"]["mode"] == "full"
    assert result["diagnostics"]["search"]["doc_ids"] == []
    assert isinstance(result["diagnostics"]["search"]["elapsed_seconds"], float)


def test_rebuild_scope_outputs_extracts_docs_and_search_diagnostics() -> None:
    calls: list[list[str]] = []
    original_bundle = with_fake_bundle()
    original_run = write_rebuild.subprocess.run

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if any(str(part).endswith("build_docs.rb") for part in command):
            return Completed(stdout=DOCS_DIAGNOSTICS_STDOUT)
        return Completed(
            stdout=(
                "Targeted search index JSON done. Wrote: 1. Skipped: 0. "
                "Changed: 2. Removed: 1. Unchanged: 3. Full fallback: 0. "
                "Path: assets/data/search/studio/index.json\n"
            )
        )

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            result = write_rebuild.rebuild_scope_outputs(Path(temp_path), "studio", search_doc_ids=["a", "b"])
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.detect_bundle_bin = original_bundle

    assert result["diagnostics"]["docs"]["scope"] == "studio"
    assert result["diagnostics"]["docs"]["source_files_scanned"] == 10
    assert result["diagnostics"]["search"] == {
        "mode": "targeted",
        "doc_ids": ["a", "b"],
        "changed": 2,
        "removed": 1,
        "unchanged": 3,
        "full_fallback": False,
        "skipped": 0,
        "wrote": 1,
        "elapsed_seconds": result["diagnostics"]["search"]["elapsed_seconds"],
    }


def test_rebuild_scope_outputs_preserves_targeted_search_command() -> None:
    calls: list[list[str]] = []
    original_bundle = with_fake_bundle()
    original_run = write_rebuild.subprocess.run

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            result = write_rebuild.rebuild_scope_outputs(
                Path(temp_path),
                "library",
                search_doc_ids=["child", "", "parent", "child"],
            )
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.detect_bundle_bin = original_bundle

    assert result["search"] == {"mode": "targeted", "doc_ids": ["child", "parent"]}
    assert calls[1] == [
        "/tmp/bundle",
        "exec",
        "ruby",
        "scripts/build_search.rb",
        "--scope",
        "library",
        "--write",
        "--only-doc-ids",
        "child,parent",
        "--remove-missing",
    ]


def test_rebuild_scope_outputs_passes_targeted_docs_command() -> None:
    calls: list[list[str]] = []
    original_bundle = with_fake_bundle()
    original_run = write_rebuild.subprocess.run
    original_fallback = write_rebuild.targeted_docs_build_fallback_reason

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    write_rebuild.targeted_docs_build_fallback_reason = lambda *_args, **_kwargs: ""
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            result = write_rebuild.rebuild_scope_outputs(
                Path(temp_path),
                "studio",
                include_search=False,
                docs_doc_ids=["body-doc", "", "body-doc", "linked-doc"],
            )
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.targeted_docs_build_fallback_reason = original_fallback
        write_rebuild.detect_bundle_bin = original_bundle

    assert result["docs"] == {
        "mode": "targeted",
        "doc_ids": ["body-doc", "linked-doc"],
        "reason": "targeted docs payload ids provided",
    }
    assert result["search"] == {"mode": "none", "doc_ids": []}
    assert calls == [
        [
            "/tmp/bundle",
            "exec",
            "ruby",
            "scripts/build_docs.rb",
            "--scope",
            "studio",
            "--write",
            "--only-doc-ids",
            "body-doc,linked-doc",
        ]
    ]


def test_rebuild_scope_outputs_falls_back_when_targeted_docs_outputs_are_missing() -> None:
    calls: list[list[str]] = []
    original_bundle = with_fake_bundle()
    original_run = write_rebuild.subprocess.run
    original_fallback = write_rebuild.targeted_docs_build_fallback_reason

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    write_rebuild.targeted_docs_build_fallback_reason = lambda *_args, **_kwargs: "full-scope fallback: existing docs index missing"
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            result = write_rebuild.rebuild_scope_outputs(
                Path(temp_path),
                "studio",
                include_search=False,
                docs_doc_ids=["body-doc"],
            )
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.targeted_docs_build_fallback_reason = original_fallback
        write_rebuild.detect_bundle_bin = original_bundle

    assert result["docs"] == {
        "mode": "full",
        "doc_ids": ["body-doc"],
        "reason": "full-scope fallback: existing docs index missing",
    }
    assert calls == [["/tmp/bundle", "exec", "ruby", "scripts/build_docs.rb", "--scope", "studio", "--write"]]


def test_rebuild_scope_outputs_skips_empty_targeted_search() -> None:
    calls: list[list[str]] = []
    original_bundle = with_fake_bundle()
    original_run = write_rebuild.subprocess.run

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            result = write_rebuild.rebuild_scope_outputs(Path(temp_path), "studio", search_doc_ids=["", " "])
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.detect_bundle_bin = original_bundle

    assert result["search"] == {"mode": "none", "doc_ids": []}
    assert calls == [["/tmp/bundle", "exec", "ruby", "scripts/build_docs.rb", "--scope", "studio", "--write"]]


def test_perform_source_write_and_rebuild_marks_pending_then_complete() -> None:
    events: list[tuple[str, str, list[str]]] = []
    original_set = write_rebuild.set_watch_suppressions
    original_clear = write_rebuild.clear_watch_suppressions
    original_rebuild = write_rebuild.rebuild_scope_outputs

    def fake_set(_repo_root, scope, filenames, *, status, **_kwargs):
        events.append(("set", status, list(filenames)))

    def fake_clear(_repo_root, scope, filenames):
        events.append(("clear", scope, list(filenames)))

    def fake_rebuild(_repo_root, scope, **_kwargs):
        events.append(("rebuild", scope, []))
        return {"ok": True}

    write_rebuild.set_watch_suppressions = fake_set
    write_rebuild.clear_watch_suppressions = fake_clear
    write_rebuild.rebuild_scope_outputs = fake_rebuild
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            repo_root = Path(temp_path)
            source_path = repo_root / "_docs" / "child.md"
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# Child\n", encoding="utf-8")
            result = write_rebuild.perform_source_write_and_rebuild(
                repo_root,
                "studio",
                [source_path],
                lambda: events.append(("write", "studio", [])),
                suppression_reason="test",
            )
    finally:
        write_rebuild.set_watch_suppressions = original_set
        write_rebuild.clear_watch_suppressions = original_clear
        write_rebuild.rebuild_scope_outputs = original_rebuild

    assert result == {"ok": True}
    assert events == [
        ("set", write_rebuild.SUPPRESSION_PENDING, ["child.md"]),
        ("write", "studio", []),
        ("rebuild", "studio", []),
        ("set", write_rebuild.SUPPRESSION_COMPLETE, ["child.md"]),
    ]


def test_perform_source_write_and_rebuild_clears_pending_on_exception() -> None:
    events: list[tuple[str, str, list[str]]] = []
    original_set = write_rebuild.set_watch_suppressions
    original_clear = write_rebuild.clear_watch_suppressions
    original_rebuild = write_rebuild.rebuild_scope_outputs

    def fake_set(_repo_root, scope, filenames, *, status, **_kwargs):
        events.append(("set", status, list(filenames)))

    def fake_clear(_repo_root, scope, filenames):
        events.append(("clear", scope, list(filenames)))

    write_rebuild.set_watch_suppressions = fake_set
    write_rebuild.clear_watch_suppressions = fake_clear
    write_rebuild.rebuild_scope_outputs = lambda *_args, **_kwargs: {"ok": True}
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            repo_root = Path(temp_path)
            source_path = repo_root / "_docs" / "child.md"
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# Child\n", encoding="utf-8")
            try:
                write_rebuild.perform_source_write_and_rebuild(
                    repo_root,
                    "studio",
                    [source_path],
                    lambda: (_ for _ in ()).throw(RuntimeError("write failed")),
                    suppression_reason="test",
                )
            except RuntimeError as exc:
                assert "write failed" in str(exc)
            else:
                raise AssertionError("Expected write failure to propagate")
    finally:
        write_rebuild.set_watch_suppressions = original_set
        write_rebuild.clear_watch_suppressions = original_clear
        write_rebuild.rebuild_scope_outputs = original_rebuild

    assert events == [
        ("set", write_rebuild.SUPPRESSION_PENDING, ["child.md"]),
        ("clear", "studio", ["child.md"]),
    ]


def test_rebuild_all_docs_outputs_preserves_command_sequence() -> None:
    calls: list[list[str]] = []
    original_bundle = with_fake_bundle()
    original_run = write_rebuild.subprocess.run

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            result = write_rebuild.rebuild_all_docs_outputs(Path(temp_path))
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.detect_bundle_bin = original_bundle

    assert result["ok"] is True
    assert calls == [
        ["/tmp/bundle", "exec", "ruby", "scripts/build_docs.rb", "--write"],
        ["/tmp/bundle", "exec", "ruby", "scripts/build_search.rb", "--scope", "studio", "--write"],
        ["/tmp/bundle", "exec", "ruby", "scripts/build_search.rb", "--scope", "library", "--write"],
        ["/tmp/bundle", "exec", "ruby", "scripts/build_search.rb", "--scope", "analysis", "--write"],
    ]


def test_rebuild_all_docs_outputs_uses_current_scope_config() -> None:
    calls: list[list[str]] = []
    original_bundle = with_fake_bundle()
    original_run = write_rebuild.subprocess.run

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            repo_root = Path(temp_path)
            config_path = repo_root / "scripts/docs/docs_scopes.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                """{
  "schema_version": "docs_scopes_v1",
  "scopes": [
    {
      "scope_id": "studio",
      "source": "_docs",
      "media_path_prefix": "docs/studio",
      "output": "assets/data/docs/scopes/studio",
      "viewer_base_url": "/docs/",
      "include_scope_param": true,
      "default_doc_id": "dev-home"
    }
  ]
}
""",
                encoding="utf-8",
            )
            result = write_rebuild.rebuild_all_docs_outputs(repo_root)
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.detect_bundle_bin = original_bundle

    assert result["ok"] is True
    assert calls == [
        ["/tmp/bundle", "exec", "ruby", "scripts/build_docs.rb", "--write"],
        ["/tmp/bundle", "exec", "ruby", "scripts/build_search.rb", "--scope", "studio", "--write"],
    ]


def main() -> None:
    test_rebuild_scope_outputs_preserves_full_command_shapes()
    test_rebuild_scope_outputs_extracts_docs_and_search_diagnostics()
    test_rebuild_scope_outputs_preserves_targeted_search_command()
    test_rebuild_scope_outputs_passes_targeted_docs_command()
    test_rebuild_scope_outputs_falls_back_when_targeted_docs_outputs_are_missing()
    test_rebuild_scope_outputs_skips_empty_targeted_search()
    test_perform_source_write_and_rebuild_marks_pending_then_complete()
    test_perform_source_write_and_rebuild_clears_pending_on_exception()
    test_rebuild_all_docs_outputs_preserves_command_sequence()
    test_rebuild_all_docs_outputs_uses_current_scope_config()
    print("Docs write/rebuild tests OK")


if __name__ == "__main__":
    main()
