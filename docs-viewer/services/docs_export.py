#!/usr/bin/env python3
"""Export Docs Viewer source data through configured prepare profiles.

Run:
  ./docs-viewer/services/docs_export.py --config-id parent-child-relationships --scope library
  ./docs-viewer/services/docs_export.py --config-id parent-child-relationships --scope library --write
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime as dt
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from docs_data_sharing import source_metadata


DEFAULT_CONFIG_PATH = Path("data-sharing/adapters/documents/config/prepare-profiles.json")
OUTPUT_ROOT = Path("var/analytics/data-sharing")
SCHEMA_VERSION = "documents_prepare_profiles_v1"
TEXT_WHITESPACE_RE = re.compile(r"\s+")
PUNCTUATION_SPACING_RE = re.compile(r"\s+([,.;:!?])")
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
    "ancestor_ids",
    "ancestor_titles",
    "child_ids",
    "child_titles",
    "summary",
    "current_summary",
    "headings",
    "source_text",
    "last_updated",
    "viewable",
}
SUPPORTED_TARGET_FORMATS = {"json", "jsonl"}
SUPPORTED_RECORD_SHAPES = {"envelope", "document_rows"}
SUPPORTED_SELECTION_MODES = {"explicit_doc_ids", "all_matching"}
SKIPPED_REASON_LABELS = {
    "has_summary": "already have summaries",
    "max_documents": "exceeded the configured maximum document count",
    "non_viewable": "are not viewable",
    "unknown_doc_id": "were not found",
}


@dataclasses.dataclass(frozen=True)
class ExportContext:
    repo_root: Path
    scope: str
    data_domain: str
    config: dict[str, Any]
    source_context: source_metadata.DataSharingDocsSourceContext
    docs: list[dict[str, Any]]
    docs_by_id: dict[str, dict[str, Any]]
    children_by_parent: dict[str, list[dict[str, Any]]]


class PlainTextExtractor(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "div",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "main",
        "p",
        "section",
        "table",
    }

    def __init__(
        self,
        *,
        title: str,
        omit_code_blocks: bool,
        image_text_mode: str,
        empty_image_mode: str,
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.title = normalize_text(title)
        self.omit_code_blocks = omit_code_blocks
        self.image_text_mode = image_text_mode
        self.empty_image_mode = empty_image_mode
        self.lines: list[str] = []
        self.current_line = ""
        self.list_stack: list[dict[str, Any]] = []
        self.skip_depth = 0
        self.svg_depth = 0
        self.svg_text_tag: str | None = None
        self.svg_parts: list[str] = []
        self.blockquote_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        attrs_by_name = {key.lower(): str(value or "") for key, value in attrs}

        if tag_name in {"script", "style"} or (self.omit_code_blocks and tag_name in {"pre", "code"}):
            self.skip_depth += 1
            return
        if self.skip_depth:
            return

        if self.svg_depth:
            self.svg_depth += 1
            if tag_name in {"title", "desc", "text"}:
                self.svg_text_tag = tag_name
            return

        if tag_name == "svg":
            self.flush_line()
            self.svg_depth = 1
            self.svg_parts = []
            self.svg_text_tag = None
            return
        if tag_name in self.BLOCK_TAGS:
            self.block_break()
            if tag_name == "blockquote":
                self.blockquote_depth += 1
        elif tag_name == "br":
            self.flush_line()
        elif tag_name in {"ul", "ol"}:
            self.block_break()
            self.list_stack.append({"tag": tag_name, "counter": 0})
        elif tag_name == "li":
            self.flush_line()
            prefix = "- "
            if self.list_stack and self.list_stack[-1]["tag"] == "ol":
                self.list_stack[-1]["counter"] += 1
                prefix = f"{self.list_stack[-1]['counter']}. "
            self.add_raw(prefix)
        elif tag_name == "img":
            self.add_image_marker(attrs_by_name.get("alt", ""))

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if self.skip_depth:
            if tag_name in {"script", "style", "pre", "code"}:
                self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.svg_depth:
            if tag_name == self.svg_text_tag:
                self.svg_text_tag = None
            self.svg_depth -= 1
            if self.svg_depth == 0:
                self.add_image_marker("; ".join(self.svg_parts))
                self.svg_parts = []
                self.svg_text_tag = None
            return

        if tag_name in self.BLOCK_TAGS:
            self.block_break()
            if tag_name == "blockquote":
                self.blockquote_depth = max(0, self.blockquote_depth - 1)
        elif tag_name == "li":
            self.flush_line()
        elif tag_name in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self.block_break()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.svg_depth:
            if self.svg_text_tag:
                text = normalize_text(data)
                if text:
                    self.svg_parts.append(text)
            return
        self.add_text(data)

    def add_raw(self, value: str) -> None:
        self.current_line += value

    def add_text(self, value: str) -> None:
        text = normalize_text(value)
        if not text:
            return
        if self.current_line and not self.current_line.endswith((" ", "\n")):
            self.current_line += " "
        self.current_line += text

    def add_image_marker(self, text: str) -> None:
        if self.image_text_mode == "omit":
            return
        image_text = normalize_text(text)
        if self.image_text_mode == "marker":
            marker = "[image]"
        elif self.image_text_mode == "extract_text" and image_text:
            marker = f"[image: {image_text}]"
        elif self.empty_image_mode == "marker":
            marker = "[image]"
        else:
            return
        self.flush_line()
        self.lines.append(marker)
        self.block_break()

    def flush_line(self) -> None:
        line = normalize_text(self.current_line)
        if line:
            if self.blockquote_depth and not line.startswith(">"):
                line = f"> {line}"
            self.lines.append(line)
        self.current_line = ""

    def block_break(self) -> None:
        self.flush_line()
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def text(self) -> str:
        self.flush_line()
        lines = trim_blank_lines(self.lines)
        if lines and self.title and lines[0] == self.title:
            lines = trim_blank_lines(lines[1:])
        return "\n".join(collapse_blank_lines(lines)).strip()


def detect_repo_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "site-tools" / "config" / "site-tools.json").exists():
            raise ValueError(f"--repo-root does not look like repo root: {repo_root}")
        return repo_root

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate

    raise ValueError("Could not detect repo root")


def normalize_text(value: Any) -> str:
    text = TEXT_WHITESPACE_RE.sub(" ", str(value or "")).strip()
    return PUNCTUATION_SPACING_RE.sub(r"\1", text)


def trim_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and lines[start] == "":
        start += 1
    while end > start and lines[end - 1] == "":
        end -= 1
    return lines[start:end]


def collapse_blank_lines(lines: list[str]) -> list[str]:
    collapsed: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank
    return collapsed


def read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


EXTERNAL_CONTEXT_SCHEMA_VERSION = "documents_external_context_v1"


def package_metadata_sidecar_path(path: Path) -> Path:
    return path.with_suffix(".meta.json")


def package_context_sidecar_path(path: Path) -> Path:
    return path.with_suffix(".context.json")


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
    if target_format and target_formats and target_format not in target_formats:
        errors.append(f"config {config_id}: target.format must be included in target.supported_formats")
    if record_shape not in SUPPORTED_RECORD_SHAPES:
        errors.append(f"config {config_id}: unsupported target.record_shape {record_shape!r}")
    if record_shape == "envelope":
        document_array_path = normalize_text(target.get("document_array_path") or "documents")
        if not OUTPUT_PATH_RE.match(document_array_path):
            errors.append(f"config {config_id}: target.document_array_path is not a supported output path")

    output = config.get("output") if isinstance(config.get("output"), dict) else {}
    path_pattern = normalize_text(output.get("path_pattern"))
    if not path_pattern:
        errors.append(f"config {config_id}: output.path_pattern is required")
    elif "{data_domain}" not in path_pattern or "{export_id}" not in path_pattern or "{timestamp}" not in path_pattern:
        errors.append(f"config {config_id}: output.path_pattern must include data_domain, export_id, and timestamp placeholders")
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
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict):
            errors.append(f"config {config_id}: document_fields[{index}] must be an object")
            continue
        source = normalize_text(mapping.get("source"))
        output_path = normalize_text(mapping.get("output_path"))
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
        if source == "source_text" and "plain_text_from_rendered_html" not in transforms:
            errors.append(f"config {config_id}: source_text fields must use plain_text_from_rendered_html")
        if "truncate_chars" in transforms:
            limit_key = normalize_text(mapping.get("limit_key"))
            if limit_key not in {"max_chars_per_document", "max_total_chars"}:
                errors.append(f"config {config_id}: field {source} uses truncate_chars without a supported limit_key")
            elif not isinstance(limits.get(limit_key), int):
                errors.append(f"config {config_id}: field {source} uses truncate_chars but limits.{limit_key} is not set")

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


def source_record_to_export_doc(record: source_metadata.DataSharingDocsSourceRecord) -> dict[str, Any]:
    return {
        "doc_id": record.doc_id,
        "scope": record.scope,
        "title": record.title,
        "published": record.published,
        "summary": record.summary,
        "added_date": record.added_date,
        "last_updated": record.last_updated,
        "parent_id": record.parent_id,
        "parent_title": record.parent_title,
        "viewable": record.viewable,
        "ui_status": record.ui_status,
        "source_path": record.source_path,
        "viewer_url": record.viewer_url,
        "content_text_length": record.content_text_length,
    }


def load_source_export_context(repo_root: Path, scope: str) -> tuple[source_metadata.DataSharingDocsSourceContext, list[dict[str, Any]]]:
    context = source_metadata.load_data_sharing_docs_source_context(repo_root, scope)
    return context, [source_record_to_export_doc(record) for record in context.records]


def build_children_by_parent(docs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    children: dict[str, list[dict[str, Any]]] = {}
    for doc in docs:
        parent_id = normalize_text(doc.get("parent_id"))
        children.setdefault(parent_id, []).append(doc)
    return children


def resolve_selected_doc_ids(selected_doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    resolved: list[str] = []
    for raw_doc_id in selected_doc_ids:
        doc_id = normalize_text(raw_doc_id)
        if not doc_id:
            continue
        if doc_id not in seen:
            seen.add(doc_id)
            resolved.append(doc_id)
    return resolved


def sort_doc_ids(doc_ids: list[str]) -> list[str]:
    return sorted(doc_ids)


def selected_docs(
    context: ExportContext,
    *,
    selected_doc_ids: list[str],
    select_all: bool,
    missing_summary_only: bool | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str], list[str]]:
    selection = context.config.get("selection", {})
    mode = normalize_text(selection.get("mode"))
    skipped: list[dict[str, str]] = []
    errors: list[str] = []
    warnings: list[str] = []

    if select_all and selected_doc_ids:
        warnings.append("selection: explicit doc_ids were ignored because select_all is true")
    if missing_summary_only and not selection.get("supports_missing_summary_only"):
        warnings.append("selection: missing_summary_only was ignored because the selected config does not support it")

    if mode == "all_matching" or select_all:
        requested_ids = sort_doc_ids([normalize_text(doc.get("doc_id")) for doc in context.docs])
    else:
        requested_ids = sort_doc_ids(resolve_selected_doc_ids(selected_doc_ids))
        if not requested_ids:
            errors.append("explicit_doc_ids selection requires at least one --doc-id, --doc-ids, or --all")

    selected: list[dict[str, Any]] = []
    for doc_id in requested_ids:
        doc = context.docs_by_id.get(doc_id)
        if doc is None:
            skipped.append({"doc_id": doc_id, "reason": "unknown_doc_id"})
            continue
        if not selection.get("include_non_viewable") and doc.get("viewable") is False:
            skipped.append({"doc_id": doc_id, "reason": "non_viewable"})
            continue
        if effective_missing_summary_only(context.config, missing_summary_only) and normalize_text(doc.get("summary")):
            skipped.append({"doc_id": doc_id, "reason": "has_summary"})
            continue
        selected.append(doc)

    max_documents = context.config.get("limits", {}).get("max_documents")
    if isinstance(max_documents, int) and len(selected) > max_documents:
        for doc in selected[max_documents:]:
            skipped.append({"doc_id": normalize_text(doc.get("doc_id")), "reason": "max_documents"})
        selected = selected[:max_documents]

    unknown_ids = [item["doc_id"] for item in skipped if item.get("reason") == "unknown_doc_id"]
    if unknown_ids:
        errors.append(f"selection: unknown doc_id value(s): {', '.join(unknown_ids)}")
    if requested_ids and not selected:
        errors.append("selection: no exportable documents remain after applying filters")

    return selected, skipped, errors, warnings


def effective_missing_summary_only(config: dict[str, Any], override: bool | None) -> bool:
    selection = config.get("selection", {})
    if override is not None:
        if not selection.get("supports_missing_summary_only") and override:
            return False
        return override
    return bool(selection.get("default_missing_summary_only")) if selection.get("supports_missing_summary_only") else False


def normalize_plain_text(value: str) -> str:
    normalized_lines = [normalize_text(line) for line in str(value or "").splitlines()]
    return "\n".join(collapse_blank_lines(trim_blank_lines(normalized_lines))).strip()


def plain_text_from_rendered_html(
    content_html: str,
    *,
    title: str,
    omit_code_blocks: bool,
    options: dict[str, Any],
) -> str:
    image_text_mode = normalize_text(options.get("image_text_mode") or "extract_text")
    empty_image_mode = normalize_text(options.get("empty_image_mode") or "omit")
    if image_text_mode not in {"omit", "marker", "extract_text"}:
        image_text_mode = "extract_text"
    if empty_image_mode not in {"omit", "marker"}:
        empty_image_mode = "omit"
    parser = PlainTextExtractor(
        title=title,
        omit_code_blocks=omit_code_blocks,
        image_text_mode=image_text_mode,
        empty_image_mode=empty_image_mode,
    )
    parser.feed(content_html)
    parser.close()
    return parser.text()


def truncate_text(value: str, *, max_chars: int | None, marker: str, strategy: str) -> tuple[str, bool]:
    text = str(value or "")
    if not isinstance(max_chars, int) or max_chars < 1 or len(text) <= max_chars:
        return text, False
    marker_text = marker or "[truncated]"
    limit = max(0, max_chars - len(marker_text) - 1)
    truncated = text[:limit].rstrip()
    if strategy == "paragraph_boundary":
        boundary = truncated.rfind("\n\n")
        if boundary > 0:
            truncated = truncated[:boundary].rstrip()
    if truncated:
        return f"{truncated}\n{marker_text}", True
    return marker_text[:max_chars], True


def apply_transforms(
    value: Any,
    *,
    transforms: list[str],
    context: ExportContext,
    doc: dict[str, Any],
    mapping: dict[str, Any],
) -> tuple[Any, bool]:
    transformed = value
    truncated = False
    transform_set = set(transforms)
    for transform in transforms:
        if transform in {"identity", "headings_from_rendered_html", "omit_code_blocks"}:
            continue
        if transform == "plain_text_from_rendered_html":
            transformed = plain_text_from_rendered_html(
                str(transformed or ""),
                title=normalize_text(doc.get("title")),
                omit_code_blocks="omit_code_blocks" in transform_set,
                options=mapping.get("options") if isinstance(mapping.get("options"), dict) else {},
            )
        elif transform == "normalize_whitespace":
            transformed = normalize_plain_text(str(transformed or ""))
        elif transform == "truncate_chars":
            limit_key = normalize_text(mapping.get("limit_key"))
            limit_value = context.config.get("limits", {}).get(limit_key)
            truncate_config = context.config.get("limits", {}).get("truncate", {})
            transformed, was_truncated = truncate_text(
                str(transformed or ""),
                max_chars=limit_value if isinstance(limit_value, int) else None,
                marker=normalize_text(truncate_config.get("marker") or "[truncated]"),
                strategy=normalize_text(truncate_config.get("strategy") or "hard"),
            )
            truncated = truncated or was_truncated
        else:
            raise ValueError(f"Unsupported transform: {transform}")
    return transformed, truncated


def ancestor_chain(context: ExportContext, doc: dict[str, Any]) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    parent_id = normalize_text(doc.get("parent_id"))
    while parent_id:
        if parent_id in seen:
            break
        seen.add(parent_id)
        parent = context.docs_by_id.get(parent_id)
        if parent is None:
            break
        chain.append(parent)
        parent_id = normalize_text(parent.get("parent_id"))
    chain.reverse()
    return chain


def source_value(context: ExportContext, doc: dict[str, Any], source: str) -> Any:
    doc_id = normalize_text(doc.get("doc_id"))
    if source in {"doc_id", "title", "parent_id", "summary", "last_updated", "viewable"}:
        return doc.get(source)
    if source == "current_summary":
        return doc.get("summary", "")
    if source == "parent_title":
        parent_id = normalize_text(doc.get("parent_id"))
        parent = context.docs_by_id.get(parent_id)
        return parent.get("title") if parent else ""
    if source == "ancestor_ids":
        return [normalize_text(item.get("doc_id")) for item in ancestor_chain(context, doc)]
    if source == "ancestor_titles":
        return [normalize_text(item.get("title")) for item in ancestor_chain(context, doc)]
    if source == "child_ids":
        return [normalize_text(item.get("doc_id")) for item in context.children_by_parent.get(doc_id, [])]
    if source == "child_titles":
        return [normalize_text(item.get("title")) for item in context.children_by_parent.get(doc_id, [])]
    if source == "headings":
        return source_metadata.data_sharing_doc_headings(context.source_context, doc_id)
    if source == "source_text":
        return source_metadata.render_data_sharing_doc_html(context.source_context, doc_id)
    raise ValueError(f"Unsupported field source: {source}")


def set_output_path(record: dict[str, Any], output_path: str, value: Any) -> None:
    parts = [part for part in output_path.split(".") if part]
    if not parts:
        raise ValueError("output_path cannot be blank")
    target = record
    for part in parts[:-1]:
        current = target.get(part)
        if not isinstance(current, dict):
            current = {}
            target[part] = current
        target = current
    target[parts[-1]] = value


def build_document_record(context: ExportContext, doc: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str], bool]:
    record: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []
    truncated = False
    doc_id = normalize_text(doc.get("doc_id"))
    for mapping in context.config.get("document_fields", []):
        if not isinstance(mapping, dict):
            errors.append(f"{doc_id}: invalid field mapping")
            continue
        source = normalize_text(mapping.get("source"))
        output_path = normalize_text(mapping.get("output_path"))
        transforms = [normalize_text(item) for item in mapping.get("transforms", [])]
        unsupported = [item for item in transforms if item and item not in SUPPORTED_TRANSFORMS]
        if unsupported:
            errors.append(f"{doc_id}: unsupported transform(s): {', '.join(unsupported)}")
            continue
        try:
            value = source_value(context, doc, source)
        except (FileNotFoundError, ValueError, NotImplementedError) as exc:
            errors.append(f"{doc_id}: {exc}")
            continue

        if value is None and "default" in mapping:
            value = copy.deepcopy(mapping.get("default"))
        if value is None:
            value = ""
        try:
            value, was_truncated = apply_transforms(
                value,
                transforms=transforms,
                context=context,
                doc=doc,
                mapping=mapping,
            )
            truncated = truncated or was_truncated
        except ValueError as exc:
            errors.append(f"{doc_id}: {exc}")
            continue
        if mapping.get("required") and value in ("", [], {}):
            errors.append(f"{doc_id}: required field {source} is empty")
            continue
        if not mapping.get("include_if_empty", True) and value in ("", [], {}):
            continue
        if not output_path:
            errors.append(f"{doc_id}: field {source} has blank output_path")
            continue
        set_output_path(record, output_path, value)
    return record, warnings, errors, truncated


def skipped_reason_counts(skipped: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in skipped:
        reason = normalize_text(item.get("reason"))
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return counts


def skipped_summary_warnings(skipped: list[dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    for reason, count in sorted(skipped_reason_counts(skipped).items()):
        if reason == "unknown_doc_id":
            continue
        label = SKIPPED_REASON_LABELS.get(reason, reason.replace("_", " "))
        warnings.append(f"selection: {count} document(s) skipped because they {label}")
    return warnings


def export_metadata(
    context: ExportContext,
    *,
    generated_at: str,
    selected: list[dict[str, Any]],
    counts: dict[str, int],
) -> dict[str, Any]:
    include = set(context.config.get("metadata", {}).get("include", []))
    config_id = normalize_text(context.config.get("id"))
    selected_doc_ids = [normalize_text(doc.get("doc_id")) for doc in selected]
    source_last_updated = {
        normalize_text(doc.get("doc_id")): normalize_text(doc.get("last_updated"))
        for doc in selected
    }
    values = {
        "export_id": config_id,
        "config_id": config_id,
        "config_checksum": config_checksum(context.config),
        "data_domain": context.data_domain,
        "scope": context.scope,
        "generated_at": generated_at,
        "selected_doc_ids": selected_doc_ids,
        "source_last_updated": source_last_updated,
        "counts": counts,
    }
    return {key: value for key, value in values.items() if key in include}


def resolve_output_path(
    repo_root: Path,
    config: dict[str, Any],
    data_domain: str,
    timestamp: str,
    target_format: str,
    output_root: Path | str | None = None,
) -> Path:
    config_id = normalize_text(config.get("id"))
    output = config.get("output") if isinstance(config.get("output"), dict) else {}
    pattern = normalize_text(output.get("path_pattern"))
    if not pattern:
        raise ValueError(f"Export config {config_id} is missing output.path_pattern")
    relative = Path(
        pattern.format(
            data_domain=data_domain,
            timestamp=timestamp,
            export_id=config_id,
        )
    )
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe export output path: {relative}")
    if target_format:
        relative = relative.with_suffix(f".{target_format}")
    allowed_root = Path(output_root) if output_root else OUTPUT_ROOT
    if relative.parts[:len(allowed_root.parts)] != allowed_root.parts:
        raise ValueError(f"Export output path must stay under {allowed_root}: {relative}")
    return repo_root / relative


def external_field_type(field: dict[str, Any]) -> str:
    output_path = normalize_text(field.get("output_path"))
    source = normalize_text(field.get("source"))
    if output_path in {"headings", "ancestor_ids", "ancestor_titles", "child_ids", "child_titles"}:
        return "array<string>"
    if source == "viewable" or output_path == "viewable":
        return "boolean"
    default = field.get("default")
    if isinstance(default, list):
        return "array"
    if isinstance(default, bool):
        return "boolean"
    if isinstance(default, (int, float)) and not isinstance(default, bool):
        return "number"
    if isinstance(default, dict):
        return "object"
    return "string"


def build_external_context(config: dict[str, Any], target_format: str) -> dict[str, Any]:
    target = config.get("target") if isinstance(config.get("target"), dict) else {}
    record_shape = normalize_text(target.get("record_shape"))
    document_array_path = normalize_text(target.get("document_array_path") or "documents")
    external_context = config.get("external_context") if isinstance(config.get("external_context"), dict) else {}
    field_descriptions = (
        external_context.get("field_descriptions")
        if isinstance(external_context.get("field_descriptions"), dict)
        else {}
    )
    if target_format == "jsonl":
        record_container = "one JSON object per line"
        records_path = ""
    elif record_shape == "envelope":
        record_container = "JSON object containing a document array"
        records_path = document_array_path
    else:
        record_container = "JSON array of document objects"
        records_path = ""

    schema: list[dict[str, str]] = []
    for field in config.get("document_fields", []):
        if not isinstance(field, dict):
            continue
        output_path = normalize_text(field.get("output_path"))
        if not output_path:
            continue
        schema.append(
            {
                "field": output_path,
                "type": external_field_type(field),
                "description": normalize_text(field_descriptions.get(output_path)),
            }
        )

    return {
        "schema_version": EXTERNAL_CONTEXT_SCHEMA_VERSION,
        "task": normalize_text(external_context.get("task")),
        "record_format": target_format,
        "record_container": record_container,
        "records_path": records_path,
        "record_schema": schema,
        "response_guidance": normalize_text(external_context.get("response_guidance")),
    }


def build_export_payload(
    context: ExportContext,
    *,
    records: list[dict[str, Any]],
    target_format: str,
) -> dict[str, Any] | list[dict[str, Any]]:
    target = context.config.get("target", {})
    record_shape = normalize_text(target.get("record_shape"))
    if record_shape == "envelope":
        payload: dict[str, Any] = {}
        document_array_path = normalize_text(target.get("document_array_path") or "documents")
        set_output_path(payload, document_array_path, records)
        return payload
    if record_shape == "document_rows":
        return records
    raise ValueError(f"Unsupported target.record_shape: {record_shape}")


def parse_doc_ids(values: list[str]) -> list[str]:
    doc_ids: list[str] = []
    for value in values:
        for item in str(value or "").split(","):
            doc_id = normalize_text(item)
            if doc_id:
                doc_ids.append(doc_id)
    return doc_ids


def export_run_times(
    generated_at_dt: dt.datetime | None = None,
    *,
    filename_timezone: dt.tzinfo | None = None,
) -> tuple[str, dt.datetime]:
    utc_dt = generated_at_dt or dt.datetime.now(dt.timezone.utc)
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=dt.timezone.utc)
    utc_dt = utc_dt.astimezone(dt.timezone.utc)
    filename_dt = utc_dt.astimezone(filename_timezone) if filename_timezone else utc_dt.astimezone()
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), filename_dt


def build_export(
    *,
    repo_root: Path,
    config_id: str,
    scope: str,
    selected_doc_ids: list[str],
    select_all: bool,
    missing_summary_only: bool | None,
    write: bool,
    data_domain: str = "documents",
    config_path: str | None = None,
    target_format: str | None = None,
    output_root: Path | str | None = None,
) -> dict[str, Any]:
    generated_at, filename_timestamp_dt = export_run_times()
    config_payload = load_config_file(repo_root, config_path)
    payload_errors, payload_warnings = validate_config_payload(config_payload)
    if payload_errors:
        return {
            "ok": False,
            "dry_run": not write,
            "config_id": config_id,
            "scope": scope,
            "target_format": "",
            "output_file": "",
            "metadata_file": "",
            "context_file": "",
            "counts": {"selected": 0, "exported": 0, "skipped": 0, "failed": 0, "truncated": 0},
            "selected_doc_ids": [],
            "exported_doc_ids": [],
            "skipped": [],
            "skipped_summary": {},
            "warnings": payload_warnings,
            "errors": payload_errors,
            "issue_counts": {"errors": len(payload_errors), "warnings": len(payload_warnings)},
            "output_written": False,
        }
    try:
        config = find_export_config(config_payload, config_id)
    except ValueError as exc:
        errors = [str(exc)]
        return {
            "ok": False,
            "dry_run": not write,
            "config_id": config_id,
            "scope": scope,
            "target_format": "",
            "output_file": "",
            "metadata_file": "",
            "context_file": "",
            "counts": {"selected": 0, "exported": 0, "skipped": 0, "failed": 0, "truncated": 0},
            "selected_doc_ids": [],
            "exported_doc_ids": [],
            "skipped": [],
            "skipped_summary": {},
            "warnings": payload_warnings,
            "errors": errors,
            "issue_counts": {"errors": len(errors), "warnings": len(payload_warnings)},
            "output_written": False,
        }
    config_errors, config_warnings = validate_export_config(config)
    warnings: list[str] = [*payload_warnings, *config_warnings]
    errors: list[str] = [*config_errors]
    if data_domain not in config.get("data_domains", []):
        errors.append(f"config {config_id}: data_domain {data_domain} is not supported")
    if not config.get("enabled", False):
        errors.append(f"config {config_id}: export config is disabled")

    output_config = config.get("output") if isinstance(config.get("output"), dict) else {}
    target_config = config.get("target") if isinstance(config.get("target"), dict) else {}
    supported_formats = supported_target_formats(config)
    requested_target_format = normalize_text(target_format)
    resolved_target_format = requested_target_format or normalize_text(target_config.get("format"))
    if requested_target_format and requested_target_format not in supported_formats:
        errors.append(
            f"config {config_id}: target_format {requested_target_format!r} is not supported; "
            f"supported formats: {', '.join(supported_formats)}"
        )
    timestamp_format = normalize_text(output_config.get("timestamp_format") or "%Y%m%d-%H%M%S")
    timestamp = filename_timestamp_dt.strftime(timestamp_format)
    output_path: Path | None = None
    relative_output = ""
    metadata_output_path: Path | None = None
    relative_metadata_output = ""
    context_output_path: Path | None = None
    relative_context_output = ""
    try:
        output_path = resolve_output_path(repo_root, config, data_domain, timestamp, resolved_target_format, output_root)
        relative_output = str(output_path.relative_to(repo_root))
        if bool(target_config.get("include_export_metadata", True)):
            metadata_output_path = package_metadata_sidecar_path(output_path)
            relative_metadata_output = str(metadata_output_path.relative_to(repo_root))
        context_output_path = package_context_sidecar_path(output_path)
        relative_context_output = str(context_output_path.relative_to(repo_root))
    except ValueError as exc:
        errors.append(f"config {config_id}: {exc}")

    if errors:
        return {
            "ok": False,
            "dry_run": not write,
            "config_id": config_id,
            "scope": scope,
            "target_format": resolved_target_format,
            "output_file": relative_output,
            "metadata_file": relative_metadata_output,
            "context_file": relative_context_output,
            "counts": {"selected": 0, "exported": 0, "skipped": 0, "failed": 0, "truncated": 0},
            "selected_doc_ids": [],
            "exported_doc_ids": [],
            "skipped": [],
            "skipped_summary": {},
            "warnings": warnings,
            "errors": errors,
            "issue_counts": {"errors": len(errors), "warnings": len(warnings)},
            "output_written": False,
        }

    try:
        source_context, docs = load_source_export_context(repo_root, scope)
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        errors = [f"source metadata: {exc}"]
        return {
            "ok": False,
            "dry_run": not write,
            "config_id": config_id,
            "scope": scope,
            "target_format": resolved_target_format,
            "supported_target_formats": supported_formats,
            "output_file": relative_output,
            "metadata_file": relative_metadata_output,
            "context_file": relative_context_output,
            "counts": {"selected": 0, "exported": 0, "skipped": 0, "failed": 0, "truncated": 0},
            "selected_doc_ids": [],
            "exported_doc_ids": [],
            "skipped": [],
            "skipped_summary": {},
            "warnings": warnings,
            "errors": errors,
            "issue_counts": {"errors": len(errors), "warnings": len(warnings)},
            "output_written": False,
        }
    docs_by_id = {normalize_text(doc.get("doc_id")): doc for doc in docs}
    context = ExportContext(
        repo_root=repo_root,
        scope=scope,
        data_domain=data_domain,
        config=config,
        source_context=source_context,
        docs=docs,
        docs_by_id=docs_by_id,
        children_by_parent=build_children_by_parent(docs),
    )
    selected, skipped, selection_errors, selection_warnings = selected_docs(
        context,
        selected_doc_ids=selected_doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
    )

    records: list[dict[str, Any]] = []
    warnings.extend(selection_warnings)
    warnings.extend(skipped_summary_warnings(skipped))
    errors = list(selection_errors)
    failed_count = 0
    truncated_count = 0
    for doc in selected:
        record, doc_warnings, doc_errors, was_truncated = build_document_record(context, doc)
        warnings.extend(doc_warnings)
        errors.extend(doc_errors)
        if not doc_errors:
            records.append(record)
            if was_truncated:
                truncated_count += 1
        else:
            failed_count += 1
    if truncated_count:
        warnings.append(f"output: {truncated_count} document(s) were truncated by configured limits")

    counts = {
        "selected": len(selected),
        "exported": len(records),
        "skipped": len(skipped),
        "failed": failed_count,
        "truncated": truncated_count,
    }
    report: dict[str, Any] = {
        "ok": not errors,
        "dry_run": not write,
        "config_id": config_id,
        "scope": scope,
        "target_format": resolved_target_format,
        "supported_target_formats": supported_formats,
        "output_file": relative_output,
        "metadata_file": relative_metadata_output,
        "context_file": relative_context_output,
        "counts": counts,
        "selected_doc_ids": [normalize_text(doc.get("doc_id")) for doc in selected],
        "exported_doc_ids": [normalize_text(record.get("doc_id")) for record in records if isinstance(record, dict)],
        "skipped": skipped,
        "skipped_summary": skipped_reason_counts(skipped),
        "warnings": warnings,
        "errors": errors,
        "issue_counts": {"errors": len(errors), "warnings": len(warnings)},
    }

    if errors:
        report["output_written"] = False
        return report

    metadata = export_metadata(context, generated_at=generated_at, selected=selected, counts=counts)
    payload = build_export_payload(
        context,
        records=records,
        target_format=resolved_target_format,
    )
    external_context = build_external_context(config, resolved_target_format)
    if write:
        if output_path is None:
            raise ValueError("Export output path was not resolved")
        if resolved_target_format == "json":
            write_json(output_path, payload)
        elif resolved_target_format == "jsonl":
            if not isinstance(payload, list):
                raise ValueError("JSONL document_rows payload must be an array")
            write_jsonl(output_path, payload)
        else:
            raise ValueError(f"Unsupported target.format: {resolved_target_format}")
        if metadata_output_path is not None:
            write_json(metadata_output_path, metadata)
        if context_output_path is not None:
            write_json(context_output_path, external_context)
        report["output_written"] = True
    else:
        report["output_written"] = False
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Docs Viewer data through a configured export pattern.")
    parser.add_argument("--config-id", required=True, help="Export config id to run")
    parser.add_argument("--scope", default="library", help="Docs Viewer scope to export")
    parser.add_argument("--doc-id", action="append", default=[], help="Document id to include; repeatable")
    parser.add_argument("--doc-ids", action="append", default=[], help="Comma-separated document ids to include")
    parser.add_argument("--all", action="store_true", help="Export all docs matching the selected config filters")
    parser.add_argument(
        "--missing-summary-only",
        action="store_true",
        default=None,
        help="Limit summary-capable configs to docs without summaries",
    )
    parser.add_argument(
        "--include-summary-complete",
        action="store_false",
        dest="missing_summary_only",
        help="Disable a config's default missing-summary-only filter",
    )
    parser.add_argument("--config-path", default="", help="Override export config path")
    parser.add_argument("--repo-root", default="", help="Override repo root")
    parser.add_argument("--format", choices=sorted(SUPPORTED_TARGET_FORMATS), default="", help="Override output format when supported by the selected config")
    parser.add_argument("--write", action="store_true", help="Write the export file; default is dry-run")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = detect_repo_root(args.repo_root or None)
        doc_ids = parse_doc_ids([*args.doc_id, *args.doc_ids])
        report = build_export(
            repo_root=repo_root,
            config_id=normalize_text(args.config_id),
            scope=normalize_text(args.scope),
            selected_doc_ids=doc_ids,
            select_all=bool(args.all),
            missing_summary_only=args.missing_summary_only,
            write=bool(args.write),
            config_path=args.config_path or None,
            target_format=args.format or None,
        )
    except Exception as exc:
        print(f"docs_export: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
