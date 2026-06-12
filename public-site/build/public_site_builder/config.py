from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PublicSiteConfig:
    schema_version: str
    site: dict[str, Any]
    default_destination: str
    marker_file: str
    nojekyll_file: str
    root_artifacts: tuple[str, ...]
    initial_pages: dict[str, dict[str, Any]]
    required_files: tuple[str, ...]
    denied_path_prefixes: tuple[str, ...]
    denied_file_patterns: tuple[str, ...]
    denied_html_tokens: tuple[str, ...]


def load_config(path: Path) -> PublicSiteConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    schema_version = data.get("schema_version")
    if schema_version != "public_site_config_v1":
        raise RuntimeError(f"unsupported public-site config schema: {schema_version!r}")

    output = _dict_value(data, "output")
    audit = _dict_value(data, "audit")
    return PublicSiteConfig(
        schema_version=schema_version,
        site=_dict_value(data, "site"),
        default_destination=_str_value(output, "default_destination"),
        marker_file=_str_value(output, "marker_file"),
        nojekyll_file=_str_value(output, "nojekyll_file"),
        root_artifacts=_str_tuple(data, "root_artifacts"),
        initial_pages=_initial_pages(data),
        required_files=_str_tuple(audit, "required_files"),
        denied_path_prefixes=_str_tuple(audit, "denied_path_prefixes"),
        denied_file_patterns=_str_tuple(audit, "denied_file_patterns"),
        denied_html_tokens=_str_tuple(audit, "denied_html_tokens"),
    )


def _dict_value(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise RuntimeError(f"public-site config field must be an object: {key}")
    return value


def _str_value(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"public-site config field must be a non-empty string: {key}")
    return value


def _str_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise RuntimeError(f"public-site config field must be a list of strings: {key}")
    return tuple(value)


def _initial_pages(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = data.get("initial_pages", {})
    if not isinstance(value, dict):
        raise RuntimeError("public-site config field must be an object: initial_pages")
    pages: dict[str, dict[str, Any]] = {}
    for path, page in value.items():
        if not isinstance(path, str) or not path:
            raise RuntimeError("initial page paths must be non-empty strings")
        if not isinstance(page, dict):
            raise RuntimeError(f"initial page config must be an object: {path}")
        pages[path] = page
    return pages
