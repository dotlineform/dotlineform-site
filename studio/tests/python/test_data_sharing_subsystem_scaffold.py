#!/usr/bin/env python3
"""Focused checks for the headless Data Sharing subsystem scaffold."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SUBSYSTEM_ROOT = REPO_ROOT / "data-sharing"
PACKAGE_ROOT = SUBSYSTEM_ROOT / "data_sharing"


def import_subsystem_module(name: str):
    if str(SUBSYSTEM_ROOT) not in sys.path:
        sys.path.insert(0, str(SUBSYSTEM_ROOT))
    return importlib.import_module(name)


def test_subsystem_root_and_core_modules_are_importable() -> None:
    package = import_subsystem_module("data_sharing")
    dispatch = import_subsystem_module("data_sharing.services.dispatch")
    paths = import_subsystem_module("data_sharing.services.paths")
    registry = import_subsystem_module("data_sharing.services.registry")

    assert package.SUBSYSTEM_ROOT == SUBSYSTEM_ROOT
    assert dispatch.CANONICAL_OPERATIONS == ("prepare", "list_returned", "review", "apply")
    assert paths.domain_artifact_root("Library").as_posix() == "var/studio/data-sharing/library"
    assert registry.ADAPTER_REGISTRY_REL_PATH.as_posix() == "data-sharing/config/adapters.json"
    assert registry.LIBRARY_EXPORT_CONFIG_SCHEMA_REL_PATH.as_posix() == "data-sharing/config/library-export-configs.schema.json"


def test_subsystem_contains_expected_headless_ownership_roots() -> None:
    expected = [
        PACKAGE_ROOT / "adapters" / "documents",
        PACKAGE_ROOT / "adapters" / "tags",
        PACKAGE_ROOT / "adapters" / "catalogue",
        PACKAGE_ROOT / "config",
        PACKAGE_ROOT / "schemas",
        PACKAGE_ROOT / "services",
        PACKAGE_ROOT / "workflows",
        SUBSYSTEM_ROOT / "config",
        SUBSYSTEM_ROOT / "schemas",
    ]
    missing = [path.relative_to(REPO_ROOT).as_posix() for path in expected if not path.exists()]
    assert missing == []


def test_subsystem_config_files_live_under_data_sharing_boundary() -> None:
    expected = [
        SUBSYSTEM_ROOT / "config" / "adapters.json",
        SUBSYSTEM_ROOT / "config" / "adapters.schema.json",
        SUBSYSTEM_ROOT / "config" / "library-export-configs.json",
        SUBSYSTEM_ROOT / "config" / "library-export-configs.schema.json",
    ]
    missing = [path.relative_to(REPO_ROOT).as_posix() for path in expected if not path.is_file()]
    assert missing == []


def test_subsystem_has_no_server_ui_or_browser_files() -> None:
    forbidden_suffixes = {".html", ".js", ".css", ".scss", ".liquid"}
    forbidden_path_parts = {
        "app",
        "browser",
        "frontend",
        "routes",
        "server",
        "templates",
        "ui",
        "views",
    }
    offenders: list[str] = []
    for path in SUBSYSTEM_ROOT.rglob("*"):
        if path.is_dir():
            continue
        relative = path.relative_to(SUBSYSTEM_ROOT)
        if path.suffix in forbidden_suffixes:
            offenders.append(relative.as_posix())
            continue
        if any(part in forbidden_path_parts for part in relative.parts):
            offenders.append(relative.as_posix())
    assert offenders == []


def main() -> None:
    test_subsystem_root_and_core_modules_are_importable()
    test_subsystem_contains_expected_headless_ownership_roots()
    test_subsystem_config_files_live_under_data_sharing_boundary()
    test_subsystem_has_no_server_ui_or_browser_files()


if __name__ == "__main__":
    main()
