#!/usr/bin/env python3
"""Focused tests for the one-time Analysis tag document group seed."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    REPO_ROOT
    / "docs-viewer/migrations/seed_analysis_tag_document_groups.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "seed_analysis_tag_document_groups",
        SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Analysis tag group seed module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def source(
    doc_id: str,
    *,
    added_date: str,
    title: str,
    group: str | None = None,
    marker: str = "",
) -> str:
    group_line = f"group: {group}\n" if group is not None else ""
    marker_text = f"\n**{marker}**\n" if marker else "\n"
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"title: {title}\n"
        f'added_date: "{added_date}"\n'
        'last_updated: "2026-07-27"\n'
        f"{group_line}"
        'parent_id: ""\n'
        "viewable: true\n"
        "---\n"
        f"# {title}\n"
        f"{marker_text}"
        "Description.\n"
    )


def prepare_repo(repo_root: Path) -> dict[str, Path]:
    module = load_module()
    config_path = repo_root / module.SCOPES_CONFIG_PATH
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "scopes": [
                    {
                        "scope_id": "analysis",
                        "sub_scopes": [
                            {
                                "sub_scope": "tags",
                                "report_customisation": {
                                    "id": "analysis_tags",
                                    "settings": {
                                        "groups": [
                                            "subject",
                                            "domain",
                                            "form",
                                            "theme",
                                        ]
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    registry_path = repo_root / module.REGISTRY_PATH
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "tag_registry_version": "tag_registry_v4",
                "policy": {
                    "allowed_groups": [
                        "subject",
                        "domain",
                        "form",
                        "theme",
                    ]
                },
                "tags": [
                    {
                        "tag_id": "alpha",
                        "group": "subject",
                        "description": "",
                        "doc_id": "d-20260727-225608-000001",
                    },
                    {
                        "tag_id": "beta",
                        "group": "domain",
                        "description": "",
                        "doc_id": "d-20260727-225608-000002",
                    },
                    {
                        "tag_id": "later",
                        "group": "form",
                        "description": "",
                        "doc_id": "d-20260729-100000-000003",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    documents_root = repo_root / module.DOCUMENTS_ROOT
    documents_root.mkdir(parents=True)
    paths = {
        "alpha": documents_root / "d-20260727-225608-000001.md",
        "beta": documents_root / "d-20260727-225608-000002.md",
        "later": documents_root / "d-20260729-100000-000003.md",
        "independent": documents_root / "d-20260624-100000-000004.md",
    }
    paths["alpha"].write_text(
        source(
            "d-20260727-225608-000001",
            added_date=module.BOOTSTRAP_ADDED_DATE,
            title="alpha",
            marker="subject",
        ),
        encoding="utf-8",
    )
    paths["beta"].write_text(
        source(
            "d-20260727-225608-000002",
            added_date=module.BOOTSTRAP_ADDED_DATE,
            title="beta",
            group="theme",
            marker="theme",
        ),
        encoding="utf-8",
    )
    paths["later"].write_text(
        source(
            "d-20260729-100000-000003",
            added_date="2026-07-29 10:00:00",
            title="later",
            group="form",
        ),
        encoding="utf-8",
    )
    paths["independent"].write_text(
        source(
            "d-20260624-100000-000004",
            added_date="2026-06-24 10:00:00",
            title="independent",
        ),
        encoding="utf-8",
    )
    return paths


def test_insert_missing_group_preserves_existing_lines_and_body() -> None:
    module = load_module()
    original = source(
        "d-20260727-225608-000001",
        added_date=module.BOOTSTRAP_ADDED_DATE,
        title='"alpha"',
        marker="subject",
    )

    updated = module.insert_missing_group(original, "subject")

    assert updated == original.replace(
        'parent_id: ""',
        'group: subject\nparent_id: ""',
    )
    assert module._source_body(
        updated,
        source_name="alpha.md",
    ) == module._source_body(original, source_name="alpha.md")
    assert "**subject**" in updated


def test_plan_seeds_only_absent_bootstrap_group_and_freezes_other_sources(
    tmp_path: Path,
) -> None:
    module = load_module()
    paths = prepare_repo(tmp_path)

    plan = module.build_seed_plan(
        tmp_path,
        created_at_utc="2026-07-29T12:00:00Z",
        expected_candidate_count=2,
        expected_independent_count=1,
    )

    assert plan["output"] == {
        "candidate_count": 2,
        "seeded_count": 1,
        "preserved_existing_group_count": 1,
        "independent_document_count": 1,
        "later_linked_document_count": 1,
        "body_changes": 0,
        "registry_changes": 0,
    }
    rows = {row["tag_id"]: row for row in plan["documents"]}
    assert rows["alpha"]["action"] == "seed"
    assert rows["alpha"]["registry_group"] == "subject"
    assert rows["beta"]["action"] == "preserve_existing"
    assert rows["beta"]["registry_group"] == "domain"
    assert rows["beta"]["existing_group"] == "theme"
    preserved = {
        Path(row["relative_path"]).name: row["relationship"]
        for row in plan["preserved_documents"]
    }
    assert preserved[paths["later"].name] == "registry_linked"
    assert preserved[paths["independent"].name] == "independent"


def test_apply_requires_exact_reviewed_inputs_and_preserves_body_markers(
    tmp_path: Path,
) -> None:
    module = load_module()
    paths = prepare_repo(tmp_path)
    plan = module.build_seed_plan(
        tmp_path,
        created_at_utc="2026-07-29T12:00:00Z",
        expected_candidate_count=2,
        expected_independent_count=1,
    )
    before = {name: path.read_bytes() for name, path in paths.items()}

    stats = module.apply_seed_plan(tmp_path, plan)

    assert stats["written_count"] == 1
    assert b"group: subject\n" in paths["alpha"].read_bytes()
    assert b"**subject**" in paths["alpha"].read_bytes()
    assert b"group: theme\n" in paths["beta"].read_bytes()
    assert paths["later"].read_bytes() == before["later"]
    assert paths["independent"].read_bytes() == before["independent"]

    stale_root = tmp_path / "stale"
    stale_paths = prepare_repo(stale_root)
    stale_plan = module.build_seed_plan(
        stale_root,
        created_at_utc="2026-07-29T12:00:00Z",
        expected_candidate_count=2,
        expected_independent_count=1,
    )
    stale_paths["alpha"].write_text(
        stale_paths["alpha"].read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="do not match the reviewed seed plan"):
        module.apply_seed_plan(stale_root, stale_plan)


def test_apply_rolls_back_if_post_write_validation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    paths = prepare_repo(tmp_path)
    plan = module.build_seed_plan(
        tmp_path,
        created_at_utc="2026-07-29T12:00:00Z",
        expected_candidate_count=2,
        expected_independent_count=1,
    )
    before = paths["alpha"].read_bytes()
    monkeypatch.setattr(
        module,
        "validate_applied_seed",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("synthetic validation failure")
        ),
    )

    with pytest.raises(RuntimeError, match="synthetic validation failure"):
        module.apply_seed_plan(tmp_path, plan)

    assert paths["alpha"].read_bytes() == before
