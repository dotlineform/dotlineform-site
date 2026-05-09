#!/usr/bin/env python3
"""Focused checks for export/import adapter registry dispatch."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTERS_PATH = REPO_ROOT / "scripts" / "docs" / "export_import_adapters.py"


def load_adapters_module():
    scripts_docs_dir = ADAPTERS_PATH.parent
    if str(scripts_docs_dir) not in sys.path:
        sys.path.insert(0, str(scripts_docs_dir))
    spec = importlib.util.spec_from_file_location("export_import_adapters", ADAPTERS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load export_import_adapters.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapters = load_adapters_module()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def registry_payload() -> dict[str, object]:
    return {
        "schema_version": "export_import_adapters_v1",
        "dispatch": [
            {"data_domain": "library", "operation": "export", "adapter_id": "documents"},
            {"data_domain": "catalogue", "operation": "export", "adapter_id": "catalogue"},
        ],
        "adapters": [
            {
                "id": "documents",
                "module": "documents",
                "label": "Documents",
                "status": "active",
                "data_domains": {
                    "library": {
                        "label": "Library",
                        "scope": "library",
                        "status": "active",
                        "paths": {
                            "export_root": "var/studio/export-import/library/exports",
                            "staging_root": "var/studio/export-import/library/import-staging",
                            "preview_root": "var/studio/export-import/library/import-preview",
                            "source_root": "_docs_library",
                        },
                        "sources": {
                            "docs_index": "assets/data/docs/scopes/library/index.json",
                            "docs_payload_root": "assets/data/docs/scopes/library/by-id",
                            "source_root": "_docs_library",
                        },
                        "config": {
                            "export_configs_path": "assets/studio/data/library_export_configs.json",
                        },
                    }
                },
                "capabilities": [
                    {"operation": "export", "status": "active"},
                ],
            },
            {
                "id": "catalogue",
                "module": "catalogue",
                "label": "Catalogue",
                "status": "stub",
                "data_domains": {
                    "catalogue": {
                        "label": "Catalogue",
                        "scope": "catalogue",
                        "status": "stub",
                        "paths": {
                            "export_root": "var/studio/export-import/catalogue/exports",
                            "staging_root": "var/studio/export-import/catalogue/import-staging",
                            "preview_root": "var/studio/export-import/catalogue/import-preview",
                            "source_root": "assets/studio/data/catalogue",
                        },
                        "sources": {
                            "source_root": "assets/studio/data/catalogue",
                        },
                        "config": {},
                    }
                },
                "capabilities": [
                    {
                        "operation": "export",
                        "status": "planned",
                        "message": "Catalogue export is not implemented yet.",
                    },
                ],
            },
        ],
    }


def test_active_documents_adapter_resolves() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_json(repo_root / adapters.REGISTRY_REL_PATH, registry_payload())

        resolution = adapters.resolve_adapter(repo_root, data_domain="library", operation="export")

    assert resolution.adapter_id == "documents"
    assert resolution.scope == "library"
    assert resolution.capability["status"] == "active"


def test_future_stub_adapter_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        write_json(repo_root / adapters.REGISTRY_REL_PATH, registry_payload())

        try:
            adapters.resolve_adapter(repo_root, data_domain="catalogue", operation="export")
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("catalogue stub unexpectedly resolved")

    assert "adapter 'catalogue' is stub" in message


def main() -> None:
    tests = [
        test_active_documents_adapter_resolves,
        test_future_stub_adapter_fails_closed,
    ]
    for test in tests:
        test()


if __name__ == "__main__":
    main()
