"""Docs Viewer API adapters for the local Studio app server."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_docs_management_server_modules: dict[Path, object] = {}


def load_docs_management_server_module(repo_root: Path):
    repo_root = repo_root.resolve()
    if repo_root in _docs_management_server_modules:
        return _docs_management_server_modules[repo_root]

    scripts_dir = repo_root / "scripts"
    docs_dir = scripts_dir / "docs"
    for path in (docs_dir, scripts_dir):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

    module_path = docs_dir / "docs_management_server.py"
    spec = importlib.util.spec_from_file_location("docs_management_server", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _docs_management_server_modules[repo_root] = module
    return module


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
        payload = load_docs_management_server_module(repo_root).capabilities_payload(repo_root)
    except Exception:
        return disabled_docs_capabilities_payload()

    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        return disabled_docs_capabilities_payload()

    capabilities["docs_management"] = False
    capabilities["source_config_reads"] = False
    capabilities["source_config_settings_reads"] = False
    capabilities["source_config_settings_writes"] = False
    capabilities["html_import"] = False
    capabilities["docs_export"] = False
    capabilities["library_import"] = False
    capabilities["scope_lifecycle"] = {
        "manifest": False,
        "create_preview": False,
        "create_apply": False,
        "delete_preview": False,
        "delete_apply": False,
        "publishing_modes": [],
        "manifest_path": "",
    }

    return payload


def docs_api_query_value(params: dict[str, list[str]], key: str) -> str:
    return (params.get(key) or [""])[0]


def docs_generated_read_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    module = load_docs_management_server_module(repo_root)
    generated_reads = module.docs_generated_reads
    source_model = module.source_model
    scope = source_model.normalize_scope(docs_api_query_value(params, "scope"))

    if path in {"/docs/index", "/docs/generated/index"}:
        return generated_reads.read_generated_docs_index(repo_root, scope)
    if path in {"/docs/search", "/docs/generated/search"}:
        return generated_reads.read_generated_search_index(repo_root, scope)
    if path in {"/docs/doc", "/docs/generated/payload"}:
        doc_id = docs_api_query_value(params, "doc_id") or docs_api_query_value(params, "doc")
        if not doc_id:
            raise ValueError("doc_id is required")
        return generated_reads.read_generated_doc_payload(repo_root, scope, doc_id)
    if path == "/docs/generated/docs-log":
        projection = docs_api_query_value(params, "projection") or "search-index"
        return generated_reads.read_generated_docs_log_projection(repo_root, projection)
    if path in {"/docs/references", "/docs/generated/references"}:
        return generated_reads.read_generated_references_index(repo_root, scope)
    if path in {"/docs/reference-target", "/docs/generated/reference-target"}:
        target_kind = docs_api_query_value(params, "target_kind")
        target_slug = docs_api_query_value(params, "target_slug")
        if not target_kind or not target_slug:
            raise ValueError("target_kind and target_slug are required")
        return generated_reads.read_generated_reference_target(repo_root, scope, target_kind, target_slug)
    raise FileNotFoundError("Not found")
