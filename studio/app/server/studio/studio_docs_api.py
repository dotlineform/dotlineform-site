"""Docs Viewer API adapters for the local Studio app server."""

from __future__ import annotations

import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCRIPTS_DOCS_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (SCRIPTS_DIR, SCRIPTS_DOCS_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import docs_management_service as docs_service  # noqa: E402


def load_docs_management_service_module(repo_root: Path):
    """Return the shared Docs management service module for fixture-backed tests."""
    return docs_service


def disabled_docs_capabilities_payload() -> dict[str, object]:
    scopes = {
        scope_id: {
            "available": False,
            "root": "",
            "archive_available": False,
            "generated_data_reads": False,
            "generated_search_reads": False,
            "count": 0,
            "scope_lifecycle": {
                "manifest_recorded": False,
                "owner": "",
                "created_by_tool": False,
                "delete_eligible": False,
            },
        }
        for scope_id in ("analysis", "library", "studio")
    }
    return {
        "ok": True,
        "capabilities": {
            "docs_management": False,
            "generated_data_reads": False,
            "source_config_reads": False,
            "source_config_settings_reads": False,
            "source_config_settings_writes": False,
            "html_import": False,
            "docs_export": False,
            "library_import": False,
            "scope_lifecycle": {
                "manifest": False,
                "create_preview": False,
                "create_apply": False,
                "delete_preview": False,
                "delete_apply": False,
                "publishing_modes": [],
                "manifest_path": "",
            },
            "scopes": scopes,
        },
    }


def docs_capabilities_payload(repo_root: Path) -> dict[str, object]:
    try:
        payload = docs_service.capabilities_payload(repo_root)
    except Exception:
        return disabled_docs_capabilities_payload()

    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        return disabled_docs_capabilities_payload()

    return payload


def docs_allowed_origin(repo_root: Path, origin: str) -> str:
    return docs_service.allowed_origin(origin) or ""


def docs_generated_read_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    return docs_service.docs_generated_read_payload(repo_root, path, params)


def docs_management_get_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    return docs_service.docs_management_get_payload(repo_root, path, params)


def docs_management_post_response(
    repo_root: Path,
    path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, object]]:
    return docs_service.docs_management_post_response(repo_root, path, body, dry_run=dry_run)
