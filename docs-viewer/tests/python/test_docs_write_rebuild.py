#!/usr/bin/env python3
"""Focused checks for Docs Management write/rebuild helpers."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from repo_factory import docs_scope_record


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

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


def with_fake_python(value: str = "/tmp/python"):
    original = write_rebuild.PYTHON_EXECUTABLE
    write_rebuild.PYTHON_EXECUTABLE = value
    return original


def write_scope_config(path: Path, scopes: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": "docs_scopes_v2", "scopes": scopes}, indent=2) + "\n",
        encoding="utf-8",
    )


def test_rebuild_scope_outputs_preserves_full_command_shapes() -> None:
    calls: list[tuple[list[str], str]] = []
    original_python = with_fake_python()
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
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert result["ok"] is True
    assert result["docs"] == {
        "mode": "full",
        "doc_ids": [],
        "reason": "full-scope fallback: no targeted docs payload ids provided",
    }
    assert result["search"] == {"mode": "full", "doc_ids": []}
    assert calls == [
        (["/tmp/python", "docs-viewer/build/build_docs.py", "--scope", "studio", "--write", "--diagnostics"], calls[0][1]),
        (["/tmp/python", "docs-viewer/build/build_search.py", "--scope", "studio", "--write"], calls[0][1]),
    ]
    assert result["diagnostics"]["search"]["mode"] == "full"
    assert result["diagnostics"]["search"]["doc_ids"] == []
    assert isinstance(result["diagnostics"]["search"]["elapsed_seconds"], float)


def test_rebuild_scope_outputs_extracts_docs_and_search_diagnostics() -> None:
    calls: list[list[str]] = []
    original_python = with_fake_python()
    original_run = write_rebuild.subprocess.run

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if any(str(part).endswith("build_docs.py") for part in command):
            return Completed(stdout=DOCS_DIAGNOSTICS_STDOUT)
        return Completed(
            stdout=(
                "Targeted search index JSON done. Wrote: 1. Skipped: 0. "
                "Changed: 2. Removed: 1. Unchanged: 3. Full fallback: 0. "
                "Path: docs-viewer/published/search/studio/index.json\n"
            )
        )

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            result = write_rebuild.rebuild_scope_outputs(Path(temp_path), "studio", search_doc_ids=["a", "b"])
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.PYTHON_EXECUTABLE = original_python

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
    original_python = with_fake_python()
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
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert result["search"] == {"mode": "targeted", "doc_ids": ["child", "parent"]}
    assert calls[1] == [
        "/tmp/python",
        "docs-viewer/build/build_search.py",
        "--scope",
        "library",
        "--write",
        "--only-doc-ids",
        "child,parent",
        "--remove-missing",
    ]


def test_rebuild_scope_outputs_passes_targeted_docs_command() -> None:
    calls: list[list[str]] = []
    original_python = with_fake_python()
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
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert result["docs"] == {
        "mode": "targeted",
        "doc_ids": ["body-doc", "linked-doc"],
        "reason": "targeted docs payload ids provided",
    }
    assert result["search"] == {"mode": "none", "doc_ids": []}
    assert calls == [
        [
            "/tmp/python",
            "docs-viewer/build/build_docs.py",
                "--scope",
                "studio",
                "--write",
                "--diagnostics",
                "--only-doc-ids",
                "body-doc,linked-doc",
            ]
    ]


def test_rebuild_scope_outputs_falls_back_when_targeted_docs_outputs_are_missing() -> None:
    calls: list[list[str]] = []
    original_python = with_fake_python()
    original_run = write_rebuild.subprocess.run
    original_fallback = write_rebuild.targeted_docs_build_fallback_reason

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    write_rebuild.targeted_docs_build_fallback_reason = lambda *_args, **_kwargs: "full-scope fallback: existing docs index tree missing"
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
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert result["docs"] == {
        "mode": "full",
        "doc_ids": ["body-doc"],
        "reason": "full-scope fallback: existing docs index tree missing",
    }
    assert calls == [["/tmp/python", "docs-viewer/build/build_docs.py", "--scope", "studio", "--write", "--diagnostics"]]


def test_targeted_docs_build_uses_index_tree_without_flat_index() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        write_scope_config(
            config_path,
            [
                docs_scope_record(
                    "library",
                    scope_type="public",
                    viewer_base_url="/library/",
                    include_scope_param=False,
                    default_doc_id="library",
                )
            ],
        )
        source_root = repo_root / "docs-viewer/source/library/documents"
        source_root.mkdir(parents=True)
        (source_root / "library.md").write_text("---\ndoc_id: library\ntitle: Library\n---\n# Library\n", encoding="utf-8")
        (source_root / "child.md").write_text("---\ndoc_id: child\ntitle: Child\n---\n# Child\n", encoding="utf-8")
        (repo_root / "docs-viewer/published/docs/library/by-id").mkdir(parents=True)
        (repo_root / "docs-viewer/published/docs/library/by-id/library.json").write_text("{}", encoding="utf-8")
        (repo_root / "docs-viewer/published/docs/library/index-tree.json").write_text(
            """{"docs":[{"doc_id":"library","children":[{"doc_id":"child"}]}]}""",
            encoding="utf-8",
        )
        (repo_root / "docs-viewer/published/docs/library/references").mkdir(parents=True)
        (repo_root / "docs-viewer/published/docs/library/references/index.json").write_text("{}", encoding="utf-8")

        reason = write_rebuild.targeted_docs_build_fallback_reason(repo_root, "library", ["child"])

    assert reason == ""


def test_targeted_docs_build_falls_back_for_unindexed_source_without_payload() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        write_scope_config(
            config_path,
            [
                docs_scope_record(
                    "library",
                    scope_type="public",
                    viewer_base_url="/library/",
                    include_scope_param=False,
                    default_doc_id="library",
                )
            ],
        )
        source_root = repo_root / "docs-viewer/source/library/documents"
        source_root.mkdir(parents=True)
        (source_root / "library.md").write_text("---\ndoc_id: library\ntitle: Library\n---\n# Library\n", encoding="utf-8")
        (source_root / "child.md").write_text("---\ndoc_id: child\ntitle: Child\n---\n# Child\n", encoding="utf-8")
        (source_root / "new.md").write_text("---\ndoc_id: new\ntitle: New\n---\n# New\n", encoding="utf-8")
        (repo_root / "docs-viewer/published/docs/library/by-id").mkdir(parents=True)
        (repo_root / "docs-viewer/published/docs/library/by-id/library.json").write_text("{}", encoding="utf-8")
        (repo_root / "docs-viewer/published/docs/library/index-tree.json").write_text(
            """{"docs":[{"doc_id":"library","children":[{"doc_id":"child"}]}]}""",
            encoding="utf-8",
        )
        (repo_root / "docs-viewer/published/docs/library/references").mkdir(parents=True)
        (repo_root / "docs-viewer/published/docs/library/references/index.json").write_text("{}", encoding="utf-8")

        reason = write_rebuild.targeted_docs_build_fallback_reason(repo_root, "library", ["child"])

    assert reason == "full-scope fallback: existing payloads missing for unselected docs"


def test_rebuild_scope_outputs_skips_empty_targeted_search() -> None:
    calls: list[list[str]] = []
    original_python = with_fake_python()
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
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert result["search"] == {"mode": "none", "doc_ids": []}
    assert calls == [["/tmp/python", "docs-viewer/build/build_docs.py", "--scope", "studio", "--write", "--diagnostics"]]


def test_rebuild_scope_outputs_preserves_front_matter_failure_message() -> None:
    original_python = with_fake_python()
    original_run = write_rebuild.subprocess.run

    def fake_run(_command, **_kwargs):
        return Completed(returncode=1, stderr="problem with front-matter on doc docs-viewer/source/studio/documents/bad.md at line 7 column 1: could not find expected ':'")

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            try:
                write_rebuild.rebuild_scope_outputs(Path(temp_path), "studio")
            except RuntimeError as exc:
                message = str(exc)
            else:
                raise AssertionError("Expected rebuild failure to propagate")
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert message == "problem with front-matter on doc docs-viewer/source/studio/documents/bad.md at line 7 column 1: could not find expected ':'"


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
            source_path = repo_root / "docs-viewer/source/studio/documents" / "child.md"
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


def test_current_scope_source_root_uses_fresh_repo_config() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
        write_scope_config(config_path, [docs_scope_record("fresh-scope")])

        root = write_rebuild.current_scope_source_root(repo_root, "fresh-scope")

    assert root == repo_root / "docs-viewer/source/fresh-scope/documents"


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
            source_path = repo_root / "docs-viewer/source/studio/documents" / "child.md"
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


def test_perform_source_write_and_rebuild_completes_only_reported_written_paths() -> None:
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
            source_root = repo_root / "docs-viewer/source/studio/documents"
            source_root.mkdir(parents=True)
            first = source_root / "first.md"
            second = source_root / "second.md"
            written_paths: list[Path] = []

            def write_first_only() -> None:
                events.append(("write", "studio", []))
                written_paths.append(first)

            write_rebuild.perform_source_write_and_rebuild(
                repo_root,
                "studio",
                [first, second],
                write_first_only,
                suppression_reason="test",
                written_paths=written_paths,
            )
    finally:
        write_rebuild.set_watch_suppressions = original_set
        write_rebuild.clear_watch_suppressions = original_clear
        write_rebuild.rebuild_scope_outputs = original_rebuild

    assert events == [
        ("set", write_rebuild.SUPPRESSION_PENDING, ["first.md", "second.md"]),
        ("write", "studio", []),
        ("clear", "studio", ["first.md", "second.md"]),
        ("set", write_rebuild.SUPPRESSION_COMPLETE, ["first.md"]),
    ]


def test_rebuild_all_docs_outputs_preserves_command_sequence() -> None:
    calls: list[list[str]] = []
    original_python = with_fake_python()
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
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert result["ok"] is True
    assert calls[0] == ["/tmp/python", "docs-viewer/build/build_docs.py", "--write", "--diagnostics"]
    assert calls[1:] == [
        ["/tmp/python", "docs-viewer/build/build_search.py", "--scope", scope["scope"], "--write"]
        for scope in result["diagnostics"]["search"]
        if scope["mode"] == "full"
    ]


def test_rebuild_all_docs_outputs_uses_current_scope_config() -> None:
    calls: list[list[str]] = []
    original_python = with_fake_python()
    original_run = write_rebuild.subprocess.run

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            repo_root = Path(temp_path)
            config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
            write_scope_config(config_path, [docs_scope_record("studio", default_doc_id="dev-home")])
            result = write_rebuild.rebuild_all_docs_outputs(repo_root)
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert result["ok"] is True
    assert calls == [
        ["/tmp/python", "docs-viewer/build/build_docs.py", "--write", "--diagnostics"],
        ["/tmp/python", "docs-viewer/build/build_search.py", "--scope", "studio", "--write"],
    ]


def test_rebuild_all_docs_outputs_rejects_local_assets_outputs() -> None:
    original_python = with_fake_python()
    original_run = write_rebuild.subprocess.run
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return Completed()

    write_rebuild.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as temp_path:
            repo_root = Path(temp_path)
            config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
            record = docs_scope_record("studio", default_doc_id="dev-home")
            record["published"]["documents"]["location"]["path"] = "site/assets/data/docs/scopes/studio"
            record["published"]["search"]["location"]["path"] = "site/assets/data/search/studio/index.json"
            write_scope_config(config_path, [record])
            try:
                write_rebuild.rebuild_all_docs_outputs(repo_root)
            except ValueError as exc:
                assert "scopes[0].published.documents" in str(exc)
                assert "docs-viewer/published/docs" in str(exc)
            else:
                raise AssertionError("Expected docs rebuild to reject a public path used for local published output")
    finally:
        write_rebuild.subprocess.run = original_run
        write_rebuild.PYTHON_EXECUTABLE = original_python

    assert calls == []


def main() -> None:
    test_rebuild_scope_outputs_preserves_full_command_shapes()
    test_rebuild_scope_outputs_extracts_docs_and_search_diagnostics()
    test_rebuild_scope_outputs_preserves_targeted_search_command()
    test_rebuild_scope_outputs_passes_targeted_docs_command()
    test_rebuild_scope_outputs_falls_back_when_targeted_docs_outputs_are_missing()
    test_targeted_docs_build_uses_index_tree_without_flat_index()
    test_rebuild_scope_outputs_skips_empty_targeted_search()
    test_rebuild_scope_outputs_preserves_front_matter_failure_message()
    test_perform_source_write_and_rebuild_marks_pending_then_complete()
    test_perform_source_write_and_rebuild_clears_pending_on_exception()
    test_rebuild_all_docs_outputs_preserves_command_sequence()
    test_rebuild_all_docs_outputs_uses_current_scope_config()
    test_rebuild_all_docs_outputs_rejects_local_assets_outputs()
    print("Docs write/rebuild tests OK")


if __name__ == "__main__":
    main()
