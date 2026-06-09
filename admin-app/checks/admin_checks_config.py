#!/usr/bin/env python3
"""Load and validate the Admin checks configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = Path("admin-app/checks/config/admin-checks.json")
REPORTS_ROOT = Path("admin-app/checks/reports")
REQUIRED_SCOPES = {"admin", "analytics", "docs-viewer", "public-site", "studio", "all"}


class ChecksConfigError(ValueError):
    """Raised when the Admin checks config is malformed."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_checks_config(config_path: Path | None = None, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    path = repo_root / (config_path or DEFAULT_CONFIG_PATH)
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ChecksConfigError("admin checks config must be a JSON object")
    validate_checks_config(payload)
    return payload


def as_object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ChecksConfigError(f"{label} must be an object")
    return value


def as_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ChecksConfigError(f"{label} must be a non-empty string")
    return value.strip()


def as_string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise ChecksConfigError(f"{label} must be a list")
    out: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ChecksConfigError(f"{label}[{index}] must be a non-empty string")
        out.append(item.strip())
    if not out and not allow_empty:
        raise ChecksConfigError(f"{label} must not be empty")
    return out


def validate_path_pattern(value: str, label: str) -> None:
    if value.startswith(("/", "~")):
        raise ChecksConfigError(f"{label} must be repo-relative: {value}")
    if "\\" in value:
        raise ChecksConfigError(f"{label} must use POSIX separators: {value}")
    if any(part == ".." for part in Path(value).parts):
        raise ChecksConfigError(f"{label} must not contain '..': {value}")


def validate_path_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    patterns = as_string_list(value, label, allow_empty=allow_empty)
    for index, pattern in enumerate(patterns):
        validate_path_pattern(pattern, f"{label}[{index}]")
    return patterns


def validate_id_map(value: Any, label: str) -> Mapping[str, Any]:
    payload = as_object(value, label)
    if not payload:
        raise ChecksConfigError(f"{label} must not be empty")
    for key, item in payload.items():
        as_nonempty_string(key, f"{label} id")
        as_object(item, f"{label}.{key}")
    return payload


def validate_target_map(config: Mapping[str, Any], section: str) -> None:
    targets = validate_id_map(config.get(section), section)
    for target_id, target in targets.items():
        as_nonempty_string(target.get("label"), f"{section}.{target_id}.label")
        validate_path_list(target.get("include"), f"{section}.{target_id}.include")
        validate_path_list(target.get("shared", []), f"{section}.{target_id}.shared", allow_empty=True)
        validate_path_list(target.get("exclude", []), f"{section}.{target_id}.exclude", allow_empty=True)


def validate_scope_map(config: Mapping[str, Any]) -> None:
    scopes = validate_id_map(config.get("scopes"), "scopes")
    missing = sorted(REQUIRED_SCOPES.difference(scopes))
    if missing:
        raise ChecksConfigError(f"missing required scopes: {', '.join(missing)}")
    for scope_id, scope in scopes.items():
        as_nonempty_string(scope.get("label"), f"scopes.{scope_id}.label")
        validate_path_list(scope.get("include"), f"scopes.{scope_id}.include")
        validate_path_list(scope.get("exclude", []), f"scopes.{scope_id}.exclude", allow_empty=True)


def validate_links(config: Mapping[str, Any]) -> None:
    routes = set(as_object(config.get("routes"), "routes"))
    areas = set(as_object(config.get("areas"), "areas"))
    for area_id, area in as_object(config.get("areas"), "areas").items():
        for route_id in as_string_list(area.get("routes", []), f"areas.{area_id}.routes", allow_empty=True):
            if route_id not in routes:
                raise ChecksConfigError(f"areas.{area_id}.routes references unknown route: {route_id}")
    for route_id, route in as_object(config.get("routes"), "routes").items():
        route_path = as_nonempty_string(route.get("path"), f"routes.{route_id}.path")
        if not route_path.startswith("/"):
            raise ChecksConfigError(f"routes.{route_id}.path must start with /")
        for area_id in as_string_list(route.get("areas", []), f"routes.{route_id}.areas", allow_empty=True):
            if area_id not in areas:
                raise ChecksConfigError(f"routes.{route_id}.areas references unknown area: {area_id}")


def validate_option_schema(value: Any, label: str) -> None:
    options = as_object(value, label)
    for option_id, schema in options.items():
        as_nonempty_string(option_id, f"{label} option id")
        schema_obj = as_object(schema, f"{label}.{option_id}")
        option_type = as_nonempty_string(schema_obj.get("type"), f"{label}.{option_id}.type")
        if option_type not in {"integer", "string", "boolean"}:
            raise ChecksConfigError(f"{label}.{option_id}.type is invalid: {option_type}")
        if "enum" in schema_obj:
            as_string_list(schema_obj["enum"], f"{label}.{option_id}.enum")


def validate_report_options(report_id: str, report: Mapping[str, Any]) -> None:
    defaults = as_object(report.get("default_options", {}), f"reports.{report_id}.default_options")
    allowed = as_object(report.get("allowed_options", {}), f"reports.{report_id}.allowed_options")
    unknown_defaults = sorted(set(defaults).difference(allowed))
    if unknown_defaults:
        raise ChecksConfigError(f"reports.{report_id}.default_options has unknown options: {', '.join(unknown_defaults)}")
    validate_option_schema(allowed, f"reports.{report_id}.allowed_options")


def validate_report_map(config: Mapping[str, Any]) -> None:
    reports = validate_id_map(config.get("reports"), "reports")
    for report_id, report in reports.items():
        as_nonempty_string(report.get("label"), f"reports.{report_id}.label")
        as_nonempty_string(report.get("description"), f"reports.{report_id}.description")
        script = Path(as_nonempty_string(report.get("script"), f"reports.{report_id}.script"))
        validate_path_pattern(script.as_posix(), f"reports.{report_id}.script")
        if not script.as_posix().startswith(f"{REPORTS_ROOT.as_posix()}/"):
            raise ChecksConfigError(f"reports.{report_id}.script must be under {REPORTS_ROOT.as_posix()}/")
        if script.suffix != ".py":
            raise ChecksConfigError(f"reports.{report_id}.script must be a Python file")
        validate_report_options(report_id, report)


def validate_checks_config(config: Mapping[str, Any]) -> None:
    if config.get("config_id") != "admin-checks":
        raise ChecksConfigError("config_id must be admin-checks")
    version = config.get("version")
    if not isinstance(version, int) or version < 1:
        raise ChecksConfigError("version must be a positive integer")
    validate_scope_map(config)
    validate_target_map(config, "families")
    validate_target_map(config, "areas")
    validate_target_map(config, "routes")
    validate_links(config)
    validate_report_map(config)


def validate_report_options_for_request(config: Mapping[str, Any], report_id: str, options: Mapping[str, Any]) -> None:
    reports = as_object(config.get("reports"), "reports")
    report = as_object(reports.get(report_id), f"reports.{report_id}")
    allowed = as_object(report.get("allowed_options", {}), f"reports.{report_id}.allowed_options")
    unknown = sorted(set(options).difference(allowed))
    if unknown:
        raise ChecksConfigError(f"unknown options for report {report_id}: {', '.join(unknown)}")
    for option_id, value in options.items():
        validate_option_value(value, as_object(allowed[option_id], f"reports.{report_id}.allowed_options.{option_id}"), f"{report_id}.{option_id}")


def validate_option_value(value: Any, schema: Mapping[str, Any], label: str) -> None:
    option_type = schema["type"]
    if option_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ChecksConfigError(f"{label} must be an integer")
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, int) and value < minimum:
            raise ChecksConfigError(f"{label} must be >= {minimum}")
        if isinstance(maximum, int) and value > maximum:
            raise ChecksConfigError(f"{label} must be <= {maximum}")
    elif option_type == "string":
        if not isinstance(value, str):
            raise ChecksConfigError(f"{label} must be a string")
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            raise ChecksConfigError(f"{label} must be one of: {', '.join(enum)}")
    elif option_type == "boolean" and not isinstance(value, bool):
        raise ChecksConfigError(f"{label} must be a boolean")


def validate_id_selection(config: Mapping[str, Any], section: str, selected: Any, label: str) -> list[str]:
    values = as_string_list(selected or [], label, allow_empty=True)
    allowed = set(as_object(config.get(section), section))
    unknown = sorted(set(values).difference(allowed))
    if unknown:
        raise ChecksConfigError(f"{label} contains unknown ids: {', '.join(unknown)}")
    return values


def validate_run_request(config: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    scope = as_nonempty_string(request.get("scope"), "request.scope")
    scopes = set(as_object(config.get("scopes"), "scopes"))
    if scope not in scopes:
        raise ChecksConfigError(f"request.scope is unknown: {scope}")

    families = validate_id_selection(config, "families", request.get("families", []), "request.families")
    areas = validate_id_selection(config, "areas", request.get("areas", []), "request.areas")
    routes = validate_id_selection(config, "routes", request.get("routes", []), "request.routes")
    reports = validate_id_selection(config, "reports", request.get("reports", []), "request.reports")
    if not reports:
        raise ChecksConfigError("request.reports must not be empty")

    options = as_object(request.get("options", {}), "request.options")
    unknown_option_reports = sorted(set(options).difference(reports))
    if unknown_option_reports:
        raise ChecksConfigError(
            f"request.options contains reports not selected in request.reports: {', '.join(unknown_option_reports)}"
        )
    for report_id in reports:
        report_options = as_object(options.get(report_id, {}), f"request.options.{report_id}")
        validate_report_options_for_request(config, report_id, report_options)

    return {
        "scope": scope,
        "families": families,
        "areas": areas,
        "routes": routes,
        "reports": reports,
        "options": dict(options),
        "write": bool(request.get("write", False)),
    }
