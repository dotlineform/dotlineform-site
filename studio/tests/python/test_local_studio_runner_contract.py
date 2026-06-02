#!/usr/bin/env python3
"""Verify the Local Studio runner stays inside the Python/JS app boundary."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LOCAL_STUDIO_RUNNER = REPO_ROOT / "bin" / "local-studio"


def test_local_studio_runner_has_no_ruby_or_jekyll_startup_dependency() -> None:
    text = LOCAL_STUDIO_RUNNER.read_text(encoding="utf-8")

    for fragment in (
        "bundle",
        "Bundler",
        "ruby",
        "jekyll",
        "build_docs.rb",
        "build_search.rb",
        "build_search.py",
        "build_docs.py",
        "catalogue_json_build.py",
        "export_catalogue_lookup",
    ):
        assert fragment not in text


def test_local_studio_runner_starts_python_owned_children() -> None:
    text = LOCAL_STUDIO_RUNNER.read_text(encoding="utf-8")

    assert "studio/app/server/studio/studio_app_server.py" in text
    assert "docs-viewer/services/docs_live_rebuild_watcher.py" in text


def main() -> None:
    test_local_studio_runner_has_no_ruby_or_jekyll_startup_dependency()
    test_local_studio_runner_starts_python_owned_children()
    print("Local Studio runner contract tests OK")


if __name__ == "__main__":
    main()
