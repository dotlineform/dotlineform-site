from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PublicSiteConfig:
    schema_version: str
    site: dict[str, Any]
    assets: dict[str, Any]
    runtime_text: dict[str, str]
    media: dict[str, str]
    thumbs: dict[str, str]
    home_media: dict[str, str]
    docs_viewer: dict[str, str]
    default_destination: str
    marker_file: str
    nojekyll_file: str
    root_artifacts: tuple[str, ...]
    public_files: tuple[str, ...]
    public_trees: tuple[str, ...]
    docs_viewer_runtime_entrypoints: tuple[str, ...]
    docs_viewer_runtime_dynamic_files: tuple[str, ...]
    required_files: tuple[str, ...]
    required_directories: tuple[str, ...]
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
        assets=_dict_value(data, "assets"),
        runtime_text=_string_dict(data, "runtime_text"),
        media=_string_dict(data, "media"),
        thumbs=_string_dict(data, "thumbs"),
        home_media=_string_dict(data, "home_media"),
        docs_viewer=_string_dict(data, "docs_viewer"),
        default_destination=_str_value(output, "default_destination"),
        marker_file=_str_value(output, "marker_file"),
        nojekyll_file=_str_value(output, "nojekyll_file"),
        root_artifacts=_str_tuple(data, "root_artifacts"),
        public_files=_str_tuple(data, "public_files"),
        public_trees=_str_tuple(data, "public_trees"),
        docs_viewer_runtime_entrypoints=_str_tuple(_dict_value(data, "docs_viewer_public_runtime"), "entrypoints"),
        docs_viewer_runtime_dynamic_files=_str_tuple(_dict_value(data, "docs_viewer_public_runtime"), "dynamic_files"),
        required_files=_str_tuple(audit, "required_files"),
        required_directories=_str_tuple(audit, "required_directories"),
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


def _string_dict(data: dict[str, Any], key: str) -> dict[str, str]:
    value = _dict_value(data, key)
    if not all(isinstance(item_key, str) and isinstance(item_value, str) for item_key, item_value in value.items()):
        raise RuntimeError(f"public-site config field must be an object of strings: {key}")
    return dict(value)
