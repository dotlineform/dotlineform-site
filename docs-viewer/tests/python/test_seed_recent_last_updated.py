#!/usr/bin/env python3
"""Focused tests for bounded Recent timestamp seed helpers."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "docs-viewer/migrations/seed_recent_last_updated.py"


def load_module():
    spec = importlib.util.spec_from_file_location("seed_recent_last_updated", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Recent seed module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_hidden_doc_ids_include_descendants_and_manage_roots() -> None:
    module = load_module()

    class Doc:
        def __init__(self, doc_id: str, parent_id: str = "", viewable: bool = True):
            self.doc_id = doc_id
            self.parent_id = parent_id
            self.viewable = viewable

    docs = [
        Doc("root"),
        Doc("hidden", viewable=False),
        Doc("hidden-child", "hidden"),
        Doc("managed"),
        Doc("managed-child", "managed"),
    ]

    assert module._hidden_doc_ids(docs, ["managed"]) == {
        "hidden",
        "hidden-child",
        "managed",
        "managed-child",
    }


def test_replace_last_updated_preserves_other_source_lines() -> None:
    module = load_module()
    source = "---\ntitle: Example\n# keep\nlast_updated: 2026-07-15\n---\n# Body\n"

    assert module._replace_last_updated(source, "2026-07-16 12:34:56") == (
        "---\ntitle: Example\n# keep\nlast_updated: \"2026-07-16 12:34:56\"\n---\n# Body\n"
    )


def test_replace_last_updated_inserts_missing_field() -> None:
    module = load_module()
    source = "---\ndoc_id: example\n---\n# Body\n"

    assert module._replace_last_updated(source, "2026-07-16 12:34:56") == (
        "---\ndoc_id: example\nlast_updated: \"2026-07-16 12:34:56\"\n---\n# Body\n"
    )


def test_dirty_candidate_does_not_regress_a_current_full_timestamp() -> None:
    module = load_module()

    class Doc:
        def __init__(self, path: Path, last_updated: str):
            self.path = path
            self.front_matter = {"title": "Example", "last_updated": last_updated}
            self.body = "# Body\n"

    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        source_path = repo_root / "docs-viewer/source/studio/documents/example.md"
        dirty_paths = {"docs-viewer/source/studio/documents/example.md"}

        current = module._candidate_for_doc(
            repo_root,
            Doc(source_path, "2026-07-16 17:00:00"),
            dirty_paths,
            "2026-07-16 16:52:48",
        )
        legacy = module._candidate_for_doc(
            repo_root,
            Doc(source_path, "2026-07-15 12:00:00"),
            dirty_paths,
            "2026-07-16 16:52:48",
        )

    assert current.timestamp == "2026-07-16 17:00:00"
    assert current.timestamp_source == "existing-full-timestamp"
    assert current.requires_write is False
    assert legacy.timestamp == "2026-07-16 16:52:48"
    assert legacy.timestamp_source == "dirty-write-time"
    assert legacy.requires_write is True


def test_git_timestamp_uses_latest_body_title_or_summary_revision() -> None:
    module = load_module()

    def git(repo_root: Path, *args: str, author_date: str = "") -> None:
        env = dict(os.environ)
        if author_date:
            env["GIT_AUTHOR_DATE"] = author_date
            env["GIT_COMMITTER_DATE"] = author_date
        subprocess.run(
            ["git", *args],
            cwd=repo_root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        git(repo_root, "init")
        git(repo_root, "config", "user.name", "Recent Test")
        git(repo_root, "config", "user.email", "recent@example.test")
        source_path = repo_root / "docs/source/example.md"
        source_path.parent.mkdir(parents=True)
        source_path.write_text(
            "---\n"
            "doc_id: example\n"
            "title: Original\n"
            "summary: Stable summary\n"
            "last_updated: 2026-07-01\n"
            "parent_id: \"\"\n"
            "---\n"
            "# Stable body\n\nEnough unchanged prose for rename detection.\n",
            encoding="utf-8",
        )
        git(repo_root, "add", ".")
        git(repo_root, "commit", "-m", "create", author_date="2026-07-01T09:00:00+01:00")

        source_path.write_text(
            source_path.read_text(encoding="utf-8").replace('parent_id: ""', "parent_id: parent"),
            encoding="utf-8",
        )
        git(repo_root, "add", ".")
        git(repo_root, "commit", "-m", "move", author_date="2026-07-02T09:00:00+01:00")

        source_path.write_text(
            source_path.read_text(encoding="utf-8").replace("title: Original", "title: Edited"),
            encoding="utf-8",
        )
        git(repo_root, "add", ".")
        git(repo_root, "commit", "-m", "edit title", author_date="2026-07-03T09:00:00+01:00")

        renamed_path = source_path.with_name("d-20260701-090000-abcdef.md")
        git(
            repo_root,
            "mv",
            source_path.relative_to(repo_root).as_posix(),
            renamed_path.relative_to(repo_root).as_posix(),
        )
        renamed_path.write_text(
            renamed_path.read_text(encoding="utf-8").replace("doc_id: example", "doc_id: d-20260701-090000-abcdef"),
            encoding="utf-8",
        )
        git(repo_root, "add", ".")
        git(repo_root, "commit", "-m", "migrate identity", author_date="2026-07-04T09:00:00+01:00")

        renamed_path.write_text(
            renamed_path.read_text(encoding="utf-8").replace("parent_id: parent", "parent_id: other"),
            encoding="utf-8",
        )
        git(repo_root, "add", ".")
        git(repo_root, "commit", "-m", "move again", author_date="2026-07-05T09:00:00+01:00")

        timestamp = module._git_substantive_author_timestamp(
            repo_root,
            renamed_path.relative_to(repo_root).as_posix(),
        )

        renamed_path.write_text(
            renamed_path.read_text(encoding="utf-8").replace(
                "last_updated: 2026-07-01",
                'last_updated: "2026-07-04 09:00:00"',
            ),
            encoding="utf-8",
        )
        front_matter, body = module.source_model.parse_source(renamed_path)

        class Doc:
            path = renamed_path
            source_text = renamed_path.read_text(encoding="utf-8")

            def __init__(self):
                self.front_matter = front_matter
                self.body = body

        candidate = module._candidate_for_doc(
            repo_root,
            Doc(),
            {renamed_path.relative_to(repo_root).as_posix()},
            "2026-07-06 09:00:00",
        )

    assert timestamp == "2026-07-03 09:00:00"
    assert candidate.timestamp == "2026-07-03 09:00:00"
    assert candidate.requires_write is True
    assert candidate.repairs_existing_full_timestamp is True


def test_route_policies_require_basis_for_recent() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config_path = repo_root / module.ROUTE_CONFIG_PATH
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps(
                {
                    "routes": [
                        {
                            "route_id": "missing-basis",
                            "app_kind": "public",
                            "default_scope_id": "example",
                            "features": ["recent"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        try:
            module._route_policies(repo_root)
        except ValueError as exc:
            assert "must declare" in str(exc)
        else:
            raise AssertionError("Recent route without a basis should be rejected")


def test_complete_existing_projections_skip_history_only_when_each_can_fill() -> None:
    module = load_module()

    class Doc:
        def __init__(self, doc_id: str, last_updated: str):
            self.doc_id = doc_id
            self.front_matter = {"last_updated": last_updated}

    specs = [
        {"projection": "manage:example", "scope": "example", "visibility": "manage"},
        {"projection": "public:example", "scope": "example", "visibility": "public"},
    ]
    complete = [
        Doc("hidden-newest", "2026-07-03 09:00:00"),
        Doc("public-newer", "2026-07-02 09:00:00"),
        Doc("public-older", "2026-07-01 09:00:00"),
    ]

    rows = module._complete_existing_projection_rows(
        "example",
        specs,
        complete,
        {"hidden-newest"},
        2,
    )

    assert rows is not None
    assert rows[0]["selected_doc_ids"] == ["hidden-newest", "public-newer"]
    assert rows[1]["selected_doc_ids"] == ["public-newer", "public-older"]

    incomplete = complete[:1] + [Doc("legacy", "2026-07-01")]
    assert module._complete_existing_projection_rows(
        "example",
        specs[:1],
        incomplete,
        set(),
        2,
    ) is None


def test_completed_plan_uses_fast_path_unless_repair_is_requested(monkeypatch) -> None:
    module = load_module()
    repo_root = Path("/repo")
    doc = SimpleNamespace(
        doc_id="example",
        path=repo_root / "docs/example.md",
        front_matter={"last_updated": "2026-07-02 09:00:00"},
    )
    calls = {"history_check": 0, "candidate": 0}

    monkeypatch.setattr(
        module,
        "load_docs_scope_configs",
        lambda _repo_root: {"example": SimpleNamespace(manage_only_tree_root_ids=())},
    )
    monkeypatch.setattr(module, "_recent_limit", lambda _repo_root: 1)
    monkeypatch.setattr(
        module,
        "_projection_specs",
        lambda _repo_root, _selected: [
            {"projection": "manage:example", "scope": "example", "visibility": "manage"}
        ],
    )
    monkeypatch.setattr(module.source_model, "load_scope_docs", lambda _repo_root, _scope: [doc])
    monkeypatch.setattr(module.source_model, "scope_root", lambda _repo_root, _scope: repo_root / "docs")
    monkeypatch.setattr(module, "_hidden_doc_ids", lambda _docs, _roots: set())
    monkeypatch.setattr(module, "_dirty_repo_paths", lambda _repo_root, _source_root: {"docs/example.md"})

    def history_check(_repo_root, _relative_path, _doc):
        calls["history_check"] += 1
        return False, "2026-07-01 09:00:00"

    def candidate(_repo_root, candidate_doc, _dirty_paths, _dirty_timestamp):
        calls["candidate"] += 1
        return module.Candidate(
            candidate_doc,
            "2026-07-02 09:00:00",
            "existing-full-timestamp",
            False,
        )

    monkeypatch.setattr(module, "_working_tree_recent_edit_changed", history_check)
    monkeypatch.setattr(module, "_candidate_for_doc", candidate)

    fast_plan = module.build_seed_plan(
        repo_root,
        selected_scopes={"example"},
        dirty_timestamp="2026-07-03 09:00:00",
    )
    assert fast_plan["writes"] == []
    assert calls == {"history_check": 0, "candidate": 0}

    repair_plan = module.build_seed_plan(
        repo_root,
        selected_scopes={"example"},
        dirty_timestamp="2026-07-03 09:00:00",
        repair_existing_full_timestamps=True,
    )
    assert repair_plan["writes"] == []
    assert repair_plan["repair_existing_full_timestamps"] is True
    assert calls == {"history_check": 1, "candidate": 1}
