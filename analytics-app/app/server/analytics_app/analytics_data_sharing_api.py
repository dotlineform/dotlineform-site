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
DATA_SHARING_ROOT = REPO_ROOT / "data-sharing"
if str(DATA_SHARING_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_SHARING_ROOT))

import script_logging  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
from docs_scope_config import document_source_path, load_docs_scope_configs  # noqa: E402
from adapters.documents import adapter as documents_data_sharing_adapter  # noqa: E402
from adapters.documents import context as documents_data_sharing_context  # noqa: E402
from adapters.tags import adapter as tags_data_sharing_adapter  # noqa: E402
from adapters.tags import context as tags_data_sharing_context  # noqa: E402
from docs_document_packages.returned_profiles import supported_return_import_profile_ids  # noqa: E402
from docs_document_packages.workspace import workspace_status  # noqa: E402
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
RETURNED_RECORDS_PATH = "/returned-records"
PREPARE_PATH = "/prepare"
CONTEXT_PATH = "/context"
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


def documents_data_sharing_dependencies() -> documents_data_sharing_context.DocumentsDataSharingDependencies:
    return documents_data_sharing_context.DocumentsDataSharingDependencies(
        log_event=log_event,
        perform_source_write_and_rebuild=write_rebuild.perform_source_write_and_rebuild,
    )


def tags_data_sharing_dependencies() -> tags_data_sharing_context.TagsDataSharingDependencies:
    return tags_data_sharing_context.TagsDataSharingDependencies(log_event=log_event)


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
        "returned_records": f"{API_BASE}{RETURNED_RECORDS_PATH}",
        "prepare": f"{API_BASE}{PREPARE_PATH}",
        "context": f"{API_BASE}{CONTEXT_PATH}",
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


def docs_scope_options(repo_root: Path) -> list[dict[str, object]]:
    configs = load_docs_scope_configs(repo_root)
    return [
        {
            "id": scope_id,
            "label": scope_id.replace("-", " ").replace("_", " ").title(),
            "source": document_source_path(config).as_posix(),
        }
        for scope_id, config in configs.items()
    ]


def documents_sharing_profiles(repo_root: Path, registry: dict[str, Any]) -> list[dict[str, Any]]:
    for adapter in registry.get("adapters", []):
        if not isinstance(adapter, dict):
            continue
        domains = adapter.get("data_domains") if isinstance(adapter.get("data_domains"), dict) else {}
        documents_domain = domains.get("documents") if isinstance(domains.get("documents"), dict) else {}
        config = documents_domain.get("config") if isinstance(documents_domain.get("config"), dict) else {}
        path_value = config.get("sharing_profiles_path")
        if not path_value:
            continue
        rel_path = data_sharing_adapters.safe_relative_path(path_value, field="config.sharing_profiles_path")
        payload = read_json_object(repo_root / rel_path, "Documents export config")
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
    if isinstance(profile.get("content_format"), dict):
        payload["content_format"] = public_profile_content_format(profile["content_format"])
    if isinstance(profile.get("selection"), dict):
        payload["selection"] = public_profile_selection(profile["selection"])
    if isinstance(profile.get("workflow"), dict):
        payload["workflow"] = public_profile_workflow(profile["workflow"])
    if isinstance(profile.get("external_context"), dict):
        payload["external_context"] = public_profile_external_context(profile["external_context"])
    if isinstance(profile.get("document_fields"), list):
        payload["document_fields"] = public_profile_document_fields(profile["document_fields"])
    return payload


def public_profile_workflow(workflow: dict[str, Any]) -> dict[str, object]:
    payload: dict[str, object] = {}
    if "supports_return_import" in workflow:
        payload["supports_return_import"] = workflow.get("supports_return_import") is True
    return payload


def public_profile_content_format(content_format: dict[str, Any]) -> dict[str, object]:
    supported_formats = content_format.get("supported_formats")
    return {
        "format": str(content_format.get("format") or "").strip(),
        "supported_formats": [
            str(item).strip()
            for item in supported_formats
            if str(item).strip()
        ] if isinstance(supported_formats, list) else [],
    }


def public_profile_external_context(external_context: dict[str, Any]) -> dict[str, object]:
    payload: dict[str, object] = {
        "task": str(external_context.get("task") or ""),
        "response_guidance": str(external_context.get("response_guidance") or ""),
        "field_descriptions": {},
    }
    field_descriptions = external_context.get("field_descriptions")
    if isinstance(field_descriptions, dict):
        payload["field_descriptions"] = {
            str(key): str(value or "")
            for key, value in field_descriptions.items()
            if str(key).strip()
        }
    return payload


def public_profile_document_fields(document_fields: list[Any]) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    for field in document_fields:
        if not isinstance(field, dict):
            continue
        output_path = str(field.get("output_path") or "").strip()
        if not output_path:
            continue
        fields.append(
            {
                "source": str(field.get("source") or "").strip(),
                "output_path": output_path,
            }
        )
    return fields


def public_profile_target(target: dict[str, Any]) -> dict[str, object]:
    return {
        "format": str(target.get("format") or "").strip(),
        "supported_formats": [
            str(item).strip()
            for item in target.get("supported_formats", [])
            if str(item).strip()
        ] if isinstance(target.get("supported_formats"), list) else [],
        "record_shape": str(target.get("record_shape") or "").strip(),
    }


def public_profile_selection(selection: dict[str, Any]) -> dict[str, object]:
    payload: dict[str, object] = {
        "mode": str(selection.get("mode") or "").strip(),
    }
    for key in ("include_descendants", "supports_missing_summary_only", "default_missing_summary_only"):
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
    workspace = workspace_status(repo_root)
    documents_profiles = documents_sharing_profiles(repo_root, registry)
    docs_scopes = docs_scope_options(repo_root)
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
            if isinstance(domain.get("record_selectors"), dict):
                public_domain["record_selectors"] = dict(domain["record_selectors"])
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
            if public_capability["status"] == "active" and not workspace["available"]:
                public_capability["status"] = "disabled"
                public_capability["message"] = workspace["message"]
            if isinstance(capability.get("sharing_profiles"), list):
                public_capability["sharing_profiles"] = [
                    public_sharing_profile(item) for item in capability["sharing_profiles"] if isinstance(item, dict)
                ]
            elif public_adapter["id"] == "documents" and public_capability["operation"] == "prepare":
                public_capability["sharing_profiles"] = documents_profiles
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
        "docs_scopes": docs_scopes,
        "workspace": workspace,
        "adapters": public_adapters,
    }


def actionable_returned_packages(payload: dict[str, object]) -> dict[str, object]:
    files = payload.get("files") if isinstance(payload.get("files"), list) else []
    blocked_files = list(payload.get("blocked_files") if isinstance(payload.get("blocked_files"), list) else [])
    documents_profile_ids = supported_return_import_profile_ids()
    actionable_files: list[dict[str, Any]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        if (
            item.get("metadata_ok")
            and str(item.get("data_domain") or "").strip() == "documents"
        ):
            profile_id = str(item.get("profile_id") or "").strip()
            if item.get("supports_return_import") is False:
                blocked = dict(item)
                blocked["return_import_supported"] = False
                blocked["blocked_reason"] = "export_only_profile"
                blocked_files.append(blocked)
                continue
            if profile_id not in documents_profile_ids:
                blocked = dict(item)
                blocked["return_import_supported"] = False
                blocked["blocked_reason"] = "unsupported_import_profile"
                blocked_files.append(blocked)
                continue
            item["return_import_supported"] = True
        actionable_files.append(item)
    payload = dict(payload)
    payload["files"] = actionable_files
    payload["blocked_files"] = blocked_files
    return payload


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
            "workspace": workspace_status(repo_root),
        }
    if api_path == CONFIG_PATH:
        return public_data_sharing_config(repo_root)
    if api_path == SELECTABLE_RECORDS_PATH:
        return data_sharing_service.selectable_records(
            repo_root,
            query_value(query, "data_domain"),
            {"docs_scope": query_value(query, "docs_scope"), "config_id": query_value(query, "config_id")},
            DATA_SHARING_HANDLERS,
        )
    if api_path == RETURNED_PACKAGES_PATH:
        return actionable_returned_packages(data_sharing_service.list_returned_packages(
            repo_root,
            query_value(query, "data_domain"),
            DATA_SHARING_HANDLERS,
        ))
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
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if api_path == CONTEXT_PATH:
        data_domain = str(body.get("data_domain") or "").strip()
        if data_domain != "documents":
            raise ValueError("context editing is only available for documents prepare profiles")
        adapter = data_sharing_service.resolve_for_service(repo_root, data_domain, "prepare")
        payload = documents_data_sharing_adapter.update_prepare_context(
            repo_root,
            body,
            dry_run,
            adapter,
            documents_data_sharing_dependencies(),
        )
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if api_path == REVIEW_PATH:
        payload = data_sharing_service.review_returned_package(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if api_path == RETURNED_RECORDS_PATH:
        payload = data_sharing_service.returned_records(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if api_path == APPLY_PATH:
        payload = data_sharing_service.apply_returned_changes(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    raise FileNotFoundError("Not found")
