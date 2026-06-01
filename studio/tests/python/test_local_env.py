#!/usr/bin/env python3
"""Verify repo-local site.env loading."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

import local_env  # noqa: E402


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_raises_contains(fn: Callable[[], Any], expected: str, label: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if expected not in str(exc):
            raise AssertionError(f"{label}: expected error containing {expected!r}, got {str(exc)!r}") from exc
        return
    raise AssertionError(f"{label}: expected ValueError")


def test_load_env_file_accepts_export_quotes_and_blank_values() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "site.env"
        path.write_text(
            "\n".join(
                [
                    "# local config",
                    'export DOTLINEFORM_PROJECTS_BASE_DIR="/tmp/projects"',
                    "MAKE_SRCSET_JOBS=4",
                    'EMPTY_VALUE=""',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        values = local_env.load_env_file(path)

    assert_equal(values["DOTLINEFORM_PROJECTS_BASE_DIR"], "/tmp/projects", "quoted export")
    assert_equal(values["MAKE_SRCSET_JOBS"], "4", "unexported value")
    assert_equal(values["EMPTY_VALUE"], "", "blank value")


def test_runtime_env_site_file_wins_over_inherited_shell() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "site.env"
        path.write_text("R2_BUCKET=site-bucket\n", encoding="utf-8")

        values = local_env.runtime_env(environ={"R2_BUCKET": "shell-bucket", "HOME": "/tmp/home"}, env_files=[path])

    assert_equal(values["R2_BUCKET"], "site-bucket", "site env wins")
    assert_equal(values["HOME"], "/tmp/home", "unrelated env preserved")


def test_missing_default_site_env_falls_back_to_process_env() -> None:
    with tempfile.TemporaryDirectory() as temp:
        repo = Path(temp)
        (repo / "_config.yml").write_text("", encoding="utf-8")

        values = local_env.runtime_env(repo_root=repo, environ={"DOTLINEFORM_PROJECTS_BASE_DIR": "/tmp/projects"})

    assert_equal(values["DOTLINEFORM_PROJECTS_BASE_DIR"], "/tmp/projects", "process env fallback")


def test_invalid_line_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "site.env"
        path.write_text("not valid\n", encoding="utf-8")

        assert_raises_contains(lambda: local_env.load_env_file(path), "invalid env file line", "invalid line")


def main() -> None:
    test_load_env_file_accepts_export_quotes_and_blank_values()
    test_runtime_env_site_file_wins_over_inherited_shell()
    test_missing_default_site_env_falls_back_to_process_env()
    test_invalid_line_is_rejected()
    print("Local env tests OK")


if __name__ == "__main__":
    main()
