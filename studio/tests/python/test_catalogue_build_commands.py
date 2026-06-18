#!/usr/bin/env python3
"""Verify scoped catalogue build command helpers."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue import catalogue_build_commands as commands  # noqa: E402
from catalogue import catalogue_public_paths as public_paths  # noqa: E402


GENERATE_OUTPUT_ARGS = [
    "--series-json-dir",
    public_paths.SERIES_JSON_DIR.as_posix(),
    "--series-index-json-path",
    public_paths.SERIES_INDEX_JSON_PATH.as_posix(),
    "--works-json-dir",
    public_paths.WORKS_JSON_DIR.as_posix(),
    "--works-index-json-path",
    public_paths.WORKS_INDEX_JSON_PATH.as_posix(),
    "--recent-index-json-path",
    public_paths.RECENT_INDEX_JSON_PATH.as_posix(),
]


def test_generate_work_command_preserves_scope_and_flags() -> None:
    repo_root = Path("/repo")
    source_dir = repo_root / "studio/data/canonical/catalogue"
    scope = {
        "work_ids": ["00001", "00002"],
        "series_ids": ["009"],
        "generate_only": ["work-json", "series-index-json"],
    }

    cmd = commands.build_generate_command(
        repo_root,
        source_dir,
        scope,
        write=True,
        force=True,
        refresh_published=True,
    )

    assert cmd == [
        sys.executable,
        "/repo/studio/services/catalogue/generate_work_pages.py",
        "--internal-json-source-run",
        "--source-dir",
        "/repo/studio/data/canonical/catalogue",
        "--work-ids",
        "00001,00002",
        *GENERATE_OUTPUT_ARGS,
        "--series-ids",
        "009",
        "--only",
        "work-json",
        "--only",
        "series-index-json",
        "--write",
        "--refresh-published",
        "--force",
    ]


def test_search_command_uses_python_builder_and_catalogue_scope() -> None:
    cmd = commands.build_search_command(
        Path("/repo"),
        write=True,
        force=True,
        env={"HOME": "/no/such/home"},
    )

    assert cmd == [
        sys.executable,
        "/repo/studio/services/catalogue/search/build_search.py",
        "--scope",
        "catalogue",
        "--output",
        public_paths.CATALOGUE_SEARCH_INDEX_JSON_PATH.as_posix(),
        "--series-index",
        public_paths.SERIES_INDEX_JSON_PATH.as_posix(),
        "--works-index",
        public_paths.WORKS_INDEX_JSON_PATH.as_posix(),
        "--write",
        "--force",
    ]


def test_failed_command_step_shape_and_message_without_running_subprocess() -> None:
    step = commands.normalize_subprocess_step(
        "Build Catalogue Search Index",
        ["build", "search"],
        returncode=2,
        stdout="\n".join([f"out {index}" for index in range(10)]),
        stderr="\n".join([f"err {index}" for index in range(10)]),
    )

    assert step == {
        "label": "Build Catalogue Search Index",
        "command": ["build", "search"],
        "exit_code": 2,
        "stdout_tail": "\n".join([f"out {index}" for index in range(2, 10)]),
        "stderr_tail": "\n".join([f"err {index}" for index in range(2, 10)]),
    }
    assert commands.step_failure_message("Build Catalogue Search Index", step) == step["stderr_tail"]


if __name__ == "__main__":
    test_generate_work_command_preserves_scope_and_flags()
    test_search_command_uses_python_builder_and_catalogue_scope()
    test_failed_command_step_shape_and_message_without_running_subprocess()
    print("Catalogue build command tests OK")
