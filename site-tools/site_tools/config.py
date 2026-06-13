from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "site_tools_config_v1"


@dataclass(frozen=True)
class DocsViewerRuntimeValidation:
    root: str
    expected_module_count: int


@dataclass(frozen=True)
class SiteValidationConfig:
    site_root: str
    required_files: tuple[str, ...]
    required_directories: tuple[str, ...]
    docs_viewer_runtime: DocsViewerRuntimeValidation


@dataclass(frozen=True)
class SiteToolsConfig:
    schema_version: str
    site: dict[str, Any]
    media: dict[str, str]
    thumbs: dict[str, str]
    home_media: dict[str, str]
    docs_viewer: dict[str, str]
    validation: SiteValidationConfig


def load_config(path: Path) -> SiteToolsConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"site-tools config must be a JSON object: {path}")
    schema_version = data.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise RuntimeError(f"unsupported site-tools config schema: {schema_version!r}")

    validation = _dict_value(data, "validation")
    docs_viewer_runtime = _dict_value(validation, "docs_viewer_runtime")
    return SiteToolsConfig(
        schema_version=schema_version,
        site=_dict_value(data, "site"),
        media=_string_dict(data, "media"),
        thumbs=_string_dict(data, "thumbs"),
        home_media=_string_dict(data, "home_media"),
        docs_viewer=_string_dict(data, "docs_viewer"),
        validation=SiteValidationConfig(
            site_root=_str_value(validation, "site_root"),
            required_files=_str_tuple(validation, "required_files"),
            required_directories=_str_tuple(validation, "required_directories"),
            docs_viewer_runtime=DocsViewerRuntimeValidation(
                root=_str_value(docs_viewer_runtime, "root"),
                expected_module_count=_int_value(docs_viewer_runtime, "expected_module_count"),
            ),
        ),
    )


def _dict_value(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise RuntimeError(f"site-tools config field must be an object: {key}")
    return value


def _str_value(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"site-tools config field must be a non-empty string: {key}")
    return value


def _int_value(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise RuntimeError(f"site-tools config field must be an integer: {key}")
    return value


def _str_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise RuntimeError(f"site-tools config field must be a list of strings: {key}")
    return tuple(value)


def _string_dict(data: dict[str, Any], key: str) -> dict[str, str]:
    value = _dict_value(data, key)
    if not all(isinstance(item_key, str) and isinstance(item_value, str) for item_key, item_value in value.items()):
        raise RuntimeError(f"site-tools config field must be an object of strings: {key}")
    return dict(value)
