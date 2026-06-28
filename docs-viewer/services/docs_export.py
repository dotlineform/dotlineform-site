#!/usr/bin/env python3
"""Export Docs Viewer source data through configured prepare profiles.

Run:
  ./docs-viewer/services/docs_export.py --config-id document-content --scope library
  ./docs-viewer/services/docs_export.py --config-id document-content --scope library --write
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from docs_data_sharing import source_metadata
from docs_export_common import (
    OUTPUT_ROOT,
    RETURNED_PACKAGE_SCHEMA_VERSION,
    collapse_blank_lines,
    data_sharing_header_row,
    export_id_from_generated_at,
    normalize_text,
    package_context_sidecar_path,
    package_metadata_path,
    trim_blank_lines,
    write_json,
    write_jsonl,
)
from docs_export_config import (
    EXPORT_META_SCHEMA_VERSION,
    SUPPORTED_TARGET_FORMATS,
    SUPPORTED_TRANSFORMS,
    config_checksum,
    find_export_config,
    load_config_file,
    supported_target_formats,
    supports_return_import,
    validate_config_payload,
    validate_export_config,
)
from docs_export_selection import (
    ExportContext,
    build_children_by_parent,
    expand_selected_docs_for_document_tree,
    load_source_export_context,
    selected_docs,
    skipped_reason_counts,
    skipped_summary_warnings,
)


EXTERNAL_CONTEXT_SCHEMA_VERSION = "documents_external_context_v1"


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
    if source == "ancestors":
        return related_document_refs(ancestor_chain(context, doc))
    if source == "children":
        return related_document_refs(context.children_by_parent.get(doc_id, []))
    if source == "headings":
        return source_metadata.data_sharing_doc_headings(context.source_context, doc_id)
    if source == "source_text":
        return source_metadata.render_data_sharing_doc_html(context.source_context, doc_id)
    raise ValueError(f"Unsupported field source: {source}")


def related_document_refs(docs: list[dict[str, Any]]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for item in docs:
        ref_id = normalize_text(item.get("doc_id"))
        if not ref_id:
            continue
        refs.append(
            {
                "id": ref_id,
                "title": normalize_text(item.get("title")),
            }
        )
    return refs


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


def export_metadata(
    context: ExportContext,
    *,
    export_id: str,
    generated_at: str,
    selected: list[dict[str, Any]],
    counts: dict[str, int],
    target_format: str,
) -> dict[str, Any]:
    include = set(context.config.get("metadata", {}).get("include", []))
    config_id = normalize_text(context.config.get("id"))
    target = context.config.get("target") if isinstance(context.config.get("target"), dict) else {}
    record_shape = normalize_text(target.get("record_shape"))
    selected_doc_ids = [normalize_text(doc.get("doc_id")) for doc in selected]
    source_last_updated = {
        normalize_text(doc.get("doc_id")): normalize_text(doc.get("last_updated"))
        for doc in selected
    }
    metadata: dict[str, Any] = {
        "schema_version": EXPORT_META_SCHEMA_VERSION,
        "export_id": export_id,
        "app": "docs-viewer",
        "data_domain": context.data_domain,
        "adapter_id": "documents",
        "config_id": config_id,
        "profile_id": config_id,
        "scope": context.scope,
        "target_format": target_format,
        "record_shape": record_shape,
        "generated_at": generated_at,
        "supports_return_import": supports_return_import(context.config),
    }
    optional_values = {
        "config_checksum": config_checksum(context.config),
        "selected_doc_ids": selected_doc_ids,
        "source_last_updated": source_last_updated,
        "counts": counts,
    }
    metadata.update({key: value for key, value in optional_values.items() if key in include})
    return metadata


def resolve_output_path(
    repo_root: Path,
    config: dict[str, Any],
    data_domain: str,
    export_id: str,
    timestamp: str,
    target_format: str,
    output_root: Path | str | None = None,
) -> Path:
    output = config.get("output") if isinstance(config.get("output"), dict) else {}
    pattern = normalize_text(output.get("path_pattern"))
    if not pattern:
        raise ValueError(f"Export config {normalize_text(config.get('id'))} is missing output.path_pattern")
    relative = Path(
        pattern.format(
            data_domain=data_domain,
            timestamp=timestamp,
            export_id=export_id,
            profile_id=normalize_text(config.get("id")),
            config_id=normalize_text(config.get("id")),
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
    if output_path in {"ancestors", "children"} or source in {"ancestors", "children"}:
        return "array<object>"
    if output_path in {"headings"}:
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
    external_context = config.get("external_context") if isinstance(config.get("external_context"), dict) else {}
    field_descriptions = (
        external_context.get("field_descriptions")
        if isinstance(external_context.get("field_descriptions"), dict)
        else {}
    )
    if record_shape == "document_tree":
        record_container = "JSON object containing a nested docs tree"
        records_path = "docs"
    elif target_format == "jsonl":
        record_container = "JSONL header row followed by one JSON object per line"
        records_path = ""
    else:
        record_container = "JSON object containing a records array"
        records_path = "records"

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
    if record_shape == "document_tree":
        schema.append(
            {
                "field": "children",
                "type": "array<object>",
                "description": "Nested child documents with doc_id, title, and optional children.",
            }
        )

    response_guidance = normalize_text(external_context.get("response_guidance"))
    if target_format == "jsonl":
        header_guidance = "Preserve the first JSONL line unchanged; it is an internal routing header."
        response_guidance = f"{response_guidance} {header_guidance}".strip()

    return {
        "schema_version": EXTERNAL_CONTEXT_SCHEMA_VERSION,
        "task": normalize_text(external_context.get("task")),
        "record_format": target_format,
        "record_container": record_container,
        "records_path": records_path,
        "record_schema": schema,
        "response_guidance": response_guidance,
    }


def build_export_payload(
    context: ExportContext,
    *,
    export_id: str,
    records: list[dict[str, Any]],
    target_format: str,
) -> dict[str, Any] | list[dict[str, Any]]:
    target = context.config.get("target", {})
    record_shape = normalize_text(target.get("record_shape"))
    if record_shape == "document_rows":
        if target_format == "json":
            return {
                "schema_version": RETURNED_PACKAGE_SCHEMA_VERSION,
                "export_id": export_id,
                "records": records,
            }
        return records
    raise ValueError(f"Unsupported target.record_shape: {record_shape}")


def document_tree_node(
    doc: dict[str, Any],
    *,
    included_by_parent: dict[str, list[dict[str, Any]]],
    emitted_ids: set[str],
    active_ids: set[str] | None = None,
) -> dict[str, Any]:
    active = set(active_ids or set())
    doc_id = normalize_text(doc.get("doc_id"))
    active.add(doc_id)
    emitted_ids.add(doc_id)
    node: dict[str, Any] = {
        "doc_id": doc_id,
        "title": normalize_text(doc.get("title")),
    }
    children = [
        document_tree_node(
            child,
            included_by_parent=included_by_parent,
            emitted_ids=emitted_ids,
            active_ids=active,
        )
        for child in included_by_parent.get(doc_id, [])
        if normalize_text(child.get("doc_id")) not in active
        and normalize_text(child.get("doc_id")) not in emitted_ids
    ]
    if children:
        node["children"] = children
    return node


def build_document_tree_payload(
    *,
    export_id: str,
    docs: list[dict[str, Any]],
) -> dict[str, Any]:
    included_ids = {normalize_text(doc.get("doc_id")) for doc in docs}
    included_by_parent: dict[str, list[dict[str, Any]]] = {}
    for doc in docs:
        parent_id = normalize_text(doc.get("parent_id"))
        if parent_id not in included_ids:
            parent_id = ""
        included_by_parent.setdefault(parent_id, []).append(doc)

    emitted_ids: set[str] = set()
    tree = [
        document_tree_node(doc, included_by_parent=included_by_parent, emitted_ids=emitted_ids)
        for doc in included_by_parent.get("", [])
    ]
    for doc in docs:
        doc_id = normalize_text(doc.get("doc_id"))
        if doc_id not in emitted_ids:
            tree.append(document_tree_node(doc, included_by_parent=included_by_parent, emitted_ids=emitted_ids))
    return {
        "schema": "docs_data_sharing_document_tree_v1",
        "export_id": export_id,
        "docs": tree,
    }


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
    export_id = export_id_from_generated_at(generated_at)
    config_payload = load_config_file(repo_root, config_path)
    payload_errors, payload_warnings = validate_config_payload(config_payload)
    if payload_errors:
        return {
            "ok": False,
            "dry_run": not write,
            "export_id": export_id,
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
            "export_id": export_id,
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
        output_path = resolve_output_path(repo_root, config, data_domain, export_id, timestamp, resolved_target_format, output_root)
        relative_output = str(output_path.relative_to(repo_root))
        metadata_output_path = package_metadata_path(repo_root, export_id)
        relative_metadata_output = str(metadata_output_path.relative_to(repo_root))
        context_output_path = package_context_sidecar_path(output_path)
        relative_context_output = str(context_output_path.relative_to(repo_root))
    except ValueError as exc:
        errors.append(f"config {config_id}: {exc}")
    if write and metadata_output_path is not None and metadata_output_path.exists():
        errors.append(f"export_id {export_id}: metadata file already exists")

    if errors:
        return {
            "ok": False,
            "dry_run": not write,
            "export_id": export_id,
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
            "export_id": export_id,
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

    record_shape = normalize_text(target_config.get("record_shape"))
    if record_shape == "document_tree":
        selected = expand_selected_docs_for_document_tree(context, selected)

    records: list[dict[str, Any]] = []
    warnings.extend(selection_warnings)
    warnings.extend(skipped_summary_warnings(skipped))
    errors = list(selection_errors)
    failed_count = 0
    truncated_count = 0
    if record_shape == "document_rows":
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
    elif record_shape == "document_tree":
        records = [
            {
                "doc_id": normalize_text(doc.get("doc_id")),
                "title": normalize_text(doc.get("title")),
            }
            for doc in selected
        ]
    else:
        errors.append(f"config {config_id}: unsupported target.record_shape {record_shape!r}")

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
        "export_id": export_id,
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

    metadata = export_metadata(
        context,
        export_id=export_id,
        generated_at=generated_at,
        selected=selected,
        counts=counts,
        target_format=resolved_target_format,
    )
    if record_shape == "document_tree":
        payload = build_document_tree_payload(export_id=export_id, docs=selected)
    else:
        payload = build_export_payload(
            context,
            export_id=export_id,
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
            write_jsonl(output_path, [data_sharing_header_row(export_id), *payload])
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
