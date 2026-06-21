#!/usr/bin/env python3
"""Analytics-owned Data Sharing API dispatch."""

from __future__ import annotations

import sys
from http import HTTPStatus
import json
from pathlib import Path
from typing import Any

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)

import script_logging  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
from data_sharing.adapters.documents import adapter as documents_data_sharing_adapter  # noqa: E402
from data_sharing.adapters.tags import adapter as tags_data_sharing_adapter  # noqa: E402
from docs_data_sharing import activity as documents_data_sharing_activity  # noqa: E402
try:
    from analytics_app import data_sharing_service  # noqa: E402
    from analytics_app import data_sharing_adapters  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover - supports direct script imports.
    import data_sharing_service  # type: ignore[no-redef]  # noqa: E402
    import data_sharing_adapters  # type: ignore[no-redef]  # noqa: E402


API_BASE = "/analytics/api/data-sharing"
HEALTH_PATH = "/health"
CONFIG_PATH = "/config"
SELECTABLE_RECORDS_PATH = "/selectable-records"
RETURNED_PACKAGES_PATH = "/returned-packages"
PREPARE_PATH = "/prepare"
REVIEW_PATH = "/review"
APPLY_PATH = "/apply"
LOGS_REL_DIR = Path("var/analytics/logs")


def log_event(repo_root: Path, event: str, details: dict[str, Any]) -> None:
    try:
        script_logging.append_script_log(
            Path(__file__),
            event,
            details=details,
            repo_root=repo_root,
            log_dir_rel=LOGS_REL_DIR,
        )
    except Exception:
        # Logging should not block local API requests.
        pass


def documents_data_sharing_dependencies() -> documents_data_sharing_adapter.DocumentsDataSharingDependencies:
    return documents_data_sharing_adapter.DocumentsDataSharingDependencies(
        log_event=log_event,
        perform_source_write_and_rebuild=write_rebuild.perform_source_write_and_rebuild,
    )


def tags_data_sharing_dependencies() -> tags_data_sharing_adapter.TagsDataSharingDependencies:
    return tags_data_sharing_adapter.TagsDataSharingDependencies(log_event=log_event)


DATA_SHARING_HANDLERS = {
    "documents": documents_data_sharing_adapter.handlers_for(documents_data_sharing_dependencies),
    "analytics.tags": tags_data_sharing_adapter.handlers_for(tags_data_sharing_dependencies),
}


def service_endpoints() -> dict[str, str]:
    return {
        "base": API_BASE,
        "health": f"{API_BASE}{HEALTH_PATH}",
        "config": f"{API_BASE}{CONFIG_PATH}",
        "selectable_records": f"{API_BASE}{SELECTABLE_RECORDS_PATH}",
        "returned_packages": f"{API_BASE}{RETURNED_PACKAGES_PATH}",
        "prepare": f"{API_BASE}{PREPARE_PATH}",
        "review": f"{API_BASE}{REVIEW_PATH}",
        "apply": f"{API_BASE}{APPLY_PATH}",
    }


def query_value(params: dict[str, list[str]], key: str) -> str:
    return (params.get(key) or [""])[0]


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} is invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def library_sharing_profiles(repo_root: Path, registry: dict[str, Any]) -> list[dict[str, Any]]:
    for adapter in registry.get("adapters", []):
        if not isinstance(adapter, dict):
            continue
        domains = adapter.get("data_domains") if isinstance(adapter.get("data_domains"), dict) else {}
        library_domain = domains.get("library") if isinstance(domains.get("library"), dict) else {}
        config = library_domain.get("config") if isinstance(library_domain.get("config"), dict) else {}
        path_value = config.get("sharing_profiles_path")
        if not path_value:
            continue
        rel_path = data_sharing_adapters.safe_relative_path(path_value, field="config.sharing_profiles_path")
        payload = read_json_object(repo_root / rel_path, "Library export config")
        configs = payload.get("configs")
        return [public_sharing_profile(item) for item in configs if isinstance(item, dict)] if isinstance(configs, list) else []
    return []


def public_sharing_profile(profile: dict[str, Any]) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": str(profile.get("id") or "").strip(),
        "label": str(profile.get("label") or "").strip(),
        "enabled": profile.get("enabled") is not False,
        "data_domains": [str(item).strip() for item in profile.get("data_domains", []) if str(item).strip()]
        if isinstance(profile.get("data_domains"), list)
        else [],
    }
    description = str(profile.get("description") or "").strip()
    if description:
        payload["description"] = description
    if isinstance(profile.get("target"), dict):
        payload["target"] = public_profile_target(profile["target"])
    if isinstance(profile.get("selection"), dict):
        payload["selection"] = public_profile_selection(profile["selection"])
    return payload


def public_profile_target(target: dict[str, Any]) -> dict[str, object]:
    return {
        "format": str(target.get("format") or "").strip(),
        "supported_formats": [
            str(item).strip()
            for item in target.get("supported_formats", [])
            if str(item).strip()
        ] if isinstance(target.get("supported_formats"), list) else [],
    }


def public_profile_selection(selection: dict[str, Any]) -> dict[str, object]:
    payload: dict[str, object] = {
        "mode": str(selection.get("mode") or "").strip(),
    }
    for key in ("supports_missing_summary_only", "default_missing_summary_only"):
        if key in selection:
            payload[key] = selection.get(key) is True
    return payload


def public_apply_action(action: dict[str, Any]) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": str(action.get("id") or "").strip(),
        "label": str(action.get("label") or "").strip(),
        "status": str(action.get("status") or "active").strip(),
    }
    for key in ("ui", "confirmation", "result"):
        if isinstance(action.get(key), dict):
            payload[key] = dict(action[key])
    return payload


def public_data_sharing_config(repo_root: Path) -> dict[str, object]:
    registry = data_sharing_adapters.load_registry(repo_root)
    library_profiles = library_sharing_profiles(repo_root, registry)
    public_adapters: list[dict[str, object]] = []

    for adapter in registry.get("adapters", []):
        if not isinstance(adapter, dict):
            continue
        public_adapter: dict[str, object] = {
            "id": str(adapter.get("id") or "").strip(),
            "label": str(adapter.get("label") or "").strip(),
            "status": str(adapter.get("status") or "active").strip(),
            "data_domains": {},
            "capabilities": [],
        }
        domains = adapter.get("data_domains") if isinstance(adapter.get("data_domains"), dict) else {}
        public_domains: dict[str, object] = {}
        for key, domain in domains.items():
            if not isinstance(domain, dict):
                continue
            public_domain: dict[str, object] = {
                "app": str(domain.get("app") or "").strip(),
                "label": str(domain.get("label") or "").strip(),
                "status": str(domain.get("status") or adapter.get("status") or "active").strip(),
                "selection_model": str(domain.get("selection_model") or "").strip(),
            }
            docs_scope = str(domain.get("docs_scope") or "").strip()
            if docs_scope:
                public_domain["docs_scope"] = docs_scope
            public_domains[str(key)] = public_domain
        public_adapter["data_domains"] = public_domains

        public_capabilities: list[dict[str, object]] = []
        for capability in adapter.get("capabilities", []):
            if not isinstance(capability, dict):
                continue
            public_capability: dict[str, object] = {
                "operation": str(capability.get("operation") or "").strip(),
                "status": str(capability.get("status") or "active").strip(),
                "message": str(capability.get("message") or "").strip(),
                "selection_model": str(capability.get("selection_model") or "").strip(),
            }
            if isinstance(capability.get("sharing_profiles"), list):
                public_capability["sharing_profiles"] = [
                    public_sharing_profile(item) for item in capability["sharing_profiles"] if isinstance(item, dict)
                ]
            elif public_adapter["id"] == "documents" and public_capability["operation"] == "prepare":
                public_capability["sharing_profiles"] = library_profiles
            if isinstance(capability.get("apply_actions"), list):
                public_capability["apply_actions"] = [
                    public_apply_action(item) for item in capability["apply_actions"] if isinstance(item, dict)
                ]
            public_capabilities.append(public_capability)
        public_adapter["capabilities"] = public_capabilities
        public_adapters.append(public_adapter)

    return {
        "ok": True,
        "schema_version": registry.get("schema_version"),
        "adapters": public_adapters,
    }


def data_sharing_get_payload(
    repo_root: Path,
    api_path: str,
    query: dict[str, list[str]],
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    if api_path == HEALTH_PATH:
        return {
            "ok": True,
            "service": "analytics_data_sharing",
            "dry_run": dry_run,
            "endpoints": service_endpoints(),
        }
    if api_path == CONFIG_PATH:
        return public_data_sharing_config(repo_root)
    if api_path == SELECTABLE_RECORDS_PATH:
        return data_sharing_service.selectable_records(
            repo_root,
            query_value(query, "data_domain"),
            DATA_SHARING_HANDLERS,
        )
    if api_path == RETURNED_PACKAGES_PATH:
        return data_sharing_service.list_returned_packages(
            repo_root,
            query_value(query, "data_domain"),
            DATA_SHARING_HANDLERS,
        )
    raise FileNotFoundError("Not found")


def data_sharing_post_response(
    repo_root: Path,
    api_path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, object]]:
    if api_path == PREPARE_PATH:
        payload = data_sharing_service.prepare_package(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        documents_data_sharing_activity.maybe_attach_docs_export_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if api_path == REVIEW_PATH:
        payload = data_sharing_service.review_returned_package(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if api_path == APPLY_PATH:
        payload = data_sharing_service.apply_returned_changes(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        documents_data_sharing_activity.maybe_attach_documents_import_apply_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    raise FileNotFoundError("Not found")
