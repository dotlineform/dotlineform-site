#!/usr/bin/env python3
"""Prepare-profile config helpers for Docs Viewer data-sharing exports."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from docs_export_common import normalize_text, read_json, write_json_atomic


DEFAULT_CONFIG_PATH = Path("data-sharing/adapters/documents/config/prepare-profiles.json")
SCHEMA_VERSION = "documents_prepare_profiles_v1"
EXPORT_META_SCHEMA_VERSION = "data_sharing_export_meta_v1"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
OUTPUT_PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
SUPPORTED_TRANSFORMS = {
    "identity",
    "headings_from_rendered_html",
    "plain_text_from_rendered_html",
    "omit_code_blocks",
    "normalize_whitespace",
    "truncate_chars",
}
SUPPORTED_FIELD_SOURCES = {
    "doc_id",
    "title",
    "parent_id",
    "parent_title",
    "ancestors",
    "children",
    "summary",
    "current_summary",
    "headings",
    "content",
    "last_updated",
    "viewable",
}
SUPPORTED_TARGET_FORMATS = {"json", "jsonl"}
SUPPORTED_RECORD_SHAPES = {"document_rows", "document_tree"}
SUPPORTED_SELECTION_MODES = {"explicit_doc_ids", "all_matching"}
DEFAULT_SUPPORTS_RETURN_IMPORT = True


def load_config_file(repo_root: Path, config_path: str | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        path = repo_root / path
    return read_json(path, "export config")


def find_export_config(config_payload: dict[str, Any], config_id: str) -> dict[str, Any]:
    matches = [
        config
        for config in config_payload.get("configs", [])
        if isinstance(config, dict) and normalize_text(config.get("id")) == config_id
    ]
    if not matches:
        raise ValueError(f"Unknown export config id: {config_id}")
    if len(matches) > 1:
        raise ValueError(f"Duplicate export config id: {config_id}")
    return matches[0]


def config_file_path(repo_root: Path, config_path: str | None = None) -> Path:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        path = repo_root / path
    return path


def document_output_paths(config: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for field in config.get("document_fields", []):
        if not isinstance(field, dict):
            continue
        output_path = normalize_text(field.get("output_path"))
        if output_path:
            paths.append(output_path)
    return paths


def supported_target_formats(config: dict[str, Any]) -> list[str]:
    target = config.get("target") if isinstance(config.get("target"), dict) else {}
    raw_formats = target.get("supported_formats")
    formats: list[str] = []
    if isinstance(raw_formats, list):
        for item in raw_formats:
            item_format = normalize_text(item)
            if item_format and item_format not in formats:
                formats.append(item_format)
    default_format = normalize_text(target.get("format"))
    if not formats and default_format:
        formats.append(default_format)
    return formats


def supports_return_import(config: dict[str, Any]) -> bool:
    workflow = config.get("workflow")
    if not isinstance(workflow, dict):
        return DEFAULT_SUPPORTS_RETURN_IMPORT
    return workflow.get("supports_return_import") is not False


def clean_context_text(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def normalize_external_context_for_config(config: dict[str, Any], external_context: Any) -> dict[str, Any]:
    config_id = normalize_text(config.get("id")) or "<unknown>"
    if not isinstance(external_context, dict):
        raise ValueError("external_context must be an object")
    field_descriptions = external_context.get("field_descriptions")
    if not isinstance(field_descriptions, dict):
        raise ValueError("external_context.field_descriptions must be an object")

    output_paths = document_output_paths(config)
    output_path_set = set(output_paths)
    stale_fields = sorted({normalize_text(key) for key in field_descriptions.keys()} - output_path_set)
    if stale_fields:
        raise ValueError(
            f"config {config_id}: external_context.field_descriptions has unknown field(s): {', '.join(stale_fields)}"
        )

    normalized_descriptions = {
        output_path: clean_context_text(field_descriptions.get(output_path))
        for output_path in output_paths
    }
    return {
        "task": clean_context_text(external_context.get("task")),
        "response_guidance": clean_context_text(external_context.get("response_guidance")),
        "field_descriptions": normalized_descriptions,
    }


def validate_full_config_payload(config_payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors, warnings = validate_config_payload(config_payload)
    configs = config_payload.get("configs")
    if isinstance(configs, list):
        for config in configs:
            if not isinstance(config, dict):
                continue
            config_errors, config_warnings = validate_export_config(config)
            errors.extend(config_errors)
            warnings.extend(config_warnings)
    return errors, warnings


def update_external_context_config(
    repo_root: Path,
    *,
    config_id: str,
    external_context: Any,
    config_path: str | None = None,
    write: bool = True,
) -> dict[str, Any]:
    normalized_config_id = normalize_text(config_id)
    if not normalized_config_id:
        raise ValueError("config_id is required")
    path = config_file_path(repo_root, config_path)
    config_payload = read_json(path, "export config")
    config = find_export_config(config_payload, normalized_config_id)
    normalized_context = normalize_external_context_for_config(config, external_context)

    updated_payload = copy.deepcopy(config_payload)
    updated_config = find_export_config(updated_payload, normalized_config_id)
    updated_config["external_context"] = normalized_context
    errors, warnings = validate_full_config_payload(updated_payload)
    if errors:
        raise ValueError("; ".join(errors))
    if write:
        write_json_atomic(path, updated_payload)
    return {
        "ok": True,
        "config_id": normalized_config_id,
        "config_path": path.relative_to(repo_root).as_posix() if path.is_relative_to(repo_root) else path.as_posix(),
        "external_context": normalized_context,
        "warnings": warnings,
        "output_written": bool(write),
    }


def validate_config_payload(config_payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if config_payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"config: schema_version must be {SCHEMA_VERSION!r}")
    configs = config_payload.get("configs")
    if not isinstance(configs, list) or not configs:
        errors.append("config: configs must be a non-empty array")
        return errors, warnings

    seen_ids: set[str] = set()
    for index, config in enumerate(configs):
        if not isinstance(config, dict):
            errors.append(f"config[{index}]: export config must be an object")
            continue
        config_id = normalize_text(config.get("id")) or f"index {index}"
        if config_id in seen_ids:
            errors.append(f"config {config_id}: duplicate export config id")
        seen_ids.add(config_id)
        if config_id and not ID_RE.match(config_id):
            errors.append(f"config {config_id}: id must use lowercase letters, numbers, and hyphens")
    return errors, warnings


def validate_export_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    config_id = normalize_text(config.get("id")) or "<unknown>"
    errors: list[str] = []
    warnings: list[str] = []

    data_domains = config.get("data_domains")
    if not isinstance(data_domains, list) or not data_domains or not all(normalize_text(data_domain) for data_domain in data_domains):
        errors.append(f"config {config_id}: data_domains must be a non-empty array")

    target = config.get("target") if isinstance(config.get("target"), dict) else {}
    target_format = normalize_text(target.get("format"))
    target_formats = supported_target_formats(config)
    record_shape = normalize_text(target.get("record_shape"))
    if target_format not in SUPPORTED_TARGET_FORMATS:
        errors.append(f"config {config_id}: unsupported target.format {target_format!r}")
    if not target_formats:
        errors.append(f"config {config_id}: target.supported_formats must include at least one format")
    for item_format in target_formats:
        if item_format not in SUPPORTED_TARGET_FORMATS:
            errors.append(f"config {config_id}: unsupported target.supported_formats value {item_format!r}")
        if item_format == "jsonl" and record_shape != "document_rows":
            errors.append(f"config {config_id}: jsonl exports must use document_rows")
        if record_shape == "document_tree" and item_format != "json":
            errors.append(f"config {config_id}: document_tree exports only support json")
    if target_format and target_formats and target_format not in target_formats:
        errors.append(f"config {config_id}: target.format must be included in target.supported_formats")
    if record_shape not in SUPPORTED_RECORD_SHAPES:
        errors.append(f"config {config_id}: unsupported target.record_shape {record_shape!r}")
    output = config.get("output") if isinstance(config.get("output"), dict) else {}
    path_pattern = normalize_text(output.get("path_pattern"))
    if not path_pattern:
        errors.append(f"config {config_id}: output.path_pattern is required")
    elif "{export_id}" in path_pattern:
        errors.append(f"config {config_id}: output.path_pattern must not include export_id; use profile_id for filenames")
    elif "{data_domain}" not in path_pattern or "{profile_id}" not in path_pattern or "{timestamp}" not in path_pattern:
        errors.append(f"config {config_id}: output.path_pattern must include data_domain, profile_id, and timestamp placeholders")
    elif target_format and not path_pattern.endswith(f".{target_format}"):
        errors.append(f"config {config_id}: output.path_pattern extension must match target.format")
    timestamp_format = normalize_text(output.get("timestamp_format") or "%Y%m%d-%H%M%S")
    try:
        dt.datetime.now(dt.timezone.utc).strftime(timestamp_format)
    except Exception:
        errors.append(f"config {config_id}: output.timestamp_format is invalid")

    selection = config.get("selection") if isinstance(config.get("selection"), dict) else {}
    selection_mode = normalize_text(selection.get("mode"))
    if selection_mode not in SUPPORTED_SELECTION_MODES:
        errors.append(f"config {config_id}: unsupported selection.mode {selection_mode!r}")
    for key in ["include_descendants", "include_non_viewable"]:
        if not isinstance(selection.get(key), bool):
            errors.append(f"config {config_id}: selection.{key} must be true or false")
    if record_shape == "document_tree" and selection.get("include_descendants") is not True:
        errors.append(f"config {config_id}: document_tree exports require selection.include_descendants true")

    workflow = config.get("workflow")
    if workflow is not None:
        if not isinstance(workflow, dict):
            errors.append(f"config {config_id}: workflow must be an object")
        elif "supports_return_import" in workflow and not isinstance(workflow.get("supports_return_import"), bool):
            errors.append(f"config {config_id}: workflow.supports_return_import must be true or false")

    limits = config.get("limits") if isinstance(config.get("limits"), dict) else {}
    for key in ["max_documents", "max_chars_per_document", "max_total_chars"]:
        value = limits.get(key)
        if value is not None and (not isinstance(value, int) or value < 1):
            errors.append(f"config {config_id}: limits.{key} must be null or a positive integer")
    if limits.get("max_total_chars") is not None:
        warnings.append(f"config {config_id}: limits.max_total_chars is documented but not enforced in v1")
    truncate = limits.get("truncate") if isinstance(limits.get("truncate"), dict) else {}
    if truncate and normalize_text(truncate.get("strategy")) not in {"hard", "paragraph_boundary"}:
        errors.append(f"config {config_id}: limits.truncate.strategy is unsupported")

    mappings = config.get("document_fields")
    if not isinstance(mappings, list) or not mappings:
        errors.append(f"config {config_id}: document_fields must be a non-empty array")
        return errors, warnings

    seen_output_paths: set[str] = set()
    seen_sources: set[str] = set()
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict):
            errors.append(f"config {config_id}: document_fields[{index}] must be an object")
            continue
        source = normalize_text(mapping.get("source"))
        output_path = normalize_text(mapping.get("output_path"))
        if source:
            seen_sources.add(source)
        transforms = [normalize_text(item) for item in mapping.get("transforms", [])]
        if source not in SUPPORTED_FIELD_SOURCES:
            errors.append(f"config {config_id}: document_fields[{index}] has unsupported source {source!r}")
        if not output_path or not OUTPUT_PATH_RE.match(output_path):
            errors.append(f"config {config_id}: document_fields[{index}] has invalid output_path")
        if output_path in seen_output_paths:
            errors.append(f"config {config_id}: duplicate document output_path {output_path}")
        for seen_path in seen_output_paths:
            if output_path.startswith(f"{seen_path}.") or seen_path.startswith(f"{output_path}."):
                errors.append(f"config {config_id}: conflicting nested output paths {seen_path} and {output_path}")
        if output_path:
            seen_output_paths.add(output_path)
        unsupported = [item for item in transforms if item and item not in SUPPORTED_TRANSFORMS]
        if unsupported:
            errors.append(f"config {config_id}: field {source} uses unsupported transform(s): {', '.join(unsupported)}")
        if source == "content" and "plain_text_from_rendered_html" not in transforms:
            errors.append(f"config {config_id}: content fields must use plain_text_from_rendered_html")
        if "truncate_chars" in transforms:
            limit_key = normalize_text(mapping.get("limit_key"))
            if limit_key not in {"max_chars_per_document", "max_total_chars"}:
                errors.append(f"config {config_id}: field {source} uses truncate_chars without a supported limit_key")
            elif not isinstance(limits.get(limit_key), int):
                errors.append(f"config {config_id}: field {source} uses truncate_chars but limits.{limit_key} is not set")
    if record_shape == "document_tree":
        if seen_output_paths != {"doc_id", "title"} or seen_sources != {"doc_id", "title"}:
            errors.append(f"config {config_id}: document_tree exports support only doc_id and title fields")

    external_context = config.get("external_context")
    if not isinstance(external_context, dict):
        errors.append(f"config {config_id}: external_context must be an object")
    else:
        task = normalize_text(external_context.get("task"))
        response_guidance = normalize_text(external_context.get("response_guidance"))
        if not task:
            errors.append(f"config {config_id}: external_context.task is required")
        if not response_guidance:
            errors.append(f"config {config_id}: external_context.response_guidance is required")
        field_descriptions = external_context.get("field_descriptions")
        if not isinstance(field_descriptions, dict):
            errors.append(f"config {config_id}: external_context.field_descriptions must be an object")
        else:
            described_fields = {normalize_text(key) for key in field_descriptions.keys()}
            for output_path in sorted(seen_output_paths):
                if not normalize_text(field_descriptions.get(output_path)):
                    errors.append(f"config {config_id}: external_context.field_descriptions.{output_path} is required")
            for field_name in sorted(described_fields - seen_output_paths):
                errors.append(f"config {config_id}: external_context.field_descriptions.{field_name} does not match a document output_path")
    return errors, warnings


def config_checksum(config: dict[str, Any]) -> str:
    serialized = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
