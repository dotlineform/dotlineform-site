#!/usr/bin/env python3
"""Export generated Docs Viewer data through configured export patterns.

Run:
  ./scripts/docs/docs_export.py --config-id library-parent-child-relationships --scope library
  ./scripts/docs/docs_export.py --config-id library-parent-child-relationships --scope library --write
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


DEFAULT_CONFIG_PATH = Path("assets/studio/data/library_export_configs.json")
DOCS_SCOPES_ROOT = Path("assets/data/docs/scopes")
OUTPUT_ROOT = Path("var/docs/exports")
SCHEMA_VERSION = "library_export_configs_v1"
TEXT_WHITESPACE_RE = re.compile(r"\s+")
SUPPORTED_TRANSFORMS = {
    "identity",
    "headings_from_rendered_html",
}


@dataclasses.dataclass(frozen=True)
class ExportContext:
    repo_root: Path
    scope: str
    config: dict[str, Any]
    docs: list[dict[str, Any]]
    docs_by_id: dict[str, dict[str, Any]]
    children_by_parent: dict[str, list[dict[str, Any]]]
    payload_cache: dict[str, dict[str, Any]]


class HeadingCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[str] = []
        self._current_tag: str | None = None
        self._current_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        if tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_tag = tag_name
            self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        if self._current_tag is None or tag.lower() != self._current_tag:
            return
        text = normalize_text("".join(self._current_parts))
        if text:
            self.headings.append(text)
        self._current_tag = None
        self._current_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_tag is not None:
            self._current_parts.append(data)


def detect_repo_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise ValueError(f"--repo-root does not look like repo root: {repo_root}")
        return repo_root

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "_config.yml").exists():
            return candidate

    raise ValueError("Could not detect repo root")


def normalize_text(value: Any) -> str:
    return TEXT_WHITESPACE_RE.sub(" ", str(value or "")).strip()


def read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def load_config_file(repo_root: Path, config_path: str | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        path = repo_root / path
    payload = read_json(path, "export config")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Expected schema_version {SCHEMA_VERSION!r} in {path}")
    configs = payload.get("configs")
    if not isinstance(configs, list) or not configs:
        raise ValueError(f"Expected non-empty configs array in {path}")
    return payload


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


def config_checksum(config: dict[str, Any]) -> str:
    serialized = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_scope_index(repo_root: Path, scope: str) -> list[dict[str, Any]]:
    index_path = repo_root / DOCS_SCOPES_ROOT / scope / "index.json"
    payload = read_json(index_path, f"{scope} docs index")
    docs = payload.get("docs")
    if not isinstance(docs, list):
        raise ValueError(f"Expected docs array in {index_path}")
    normalized_docs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in docs:
        if not isinstance(item, dict):
            continue
        doc_id = normalize_text(item.get("doc_id"))
        if not doc_id:
            continue
        if doc_id in seen:
            raise ValueError(f"Duplicate doc_id in {index_path}: {doc_id}")
        seen.add(doc_id)
        row = dict(item)
        row["doc_id"] = doc_id
        normalized_docs.append(row)
    return normalized_docs


def load_doc_payload(context: ExportContext, doc_id: str) -> dict[str, Any]:
    if doc_id not in context.payload_cache:
        payload_path = context.repo_root / DOCS_SCOPES_ROOT / context.scope / "by-id" / f"{doc_id}.json"
        context.payload_cache[doc_id] = read_json(payload_path, f"{context.scope} doc payload for {doc_id}")
    return context.payload_cache[doc_id]


def build_children_by_parent(docs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    children: dict[str, list[dict[str, Any]]] = {}
    for doc in docs:
        parent_id = normalize_text(doc.get("parent_id"))
        children.setdefault(parent_id, []).append(doc)
    return children


def descendant_ids(children_by_parent: dict[str, list[dict[str, Any]]], root_id: str) -> set[str]:
    found: set[str] = set()
    stack = [root_id]
    while stack:
        parent_id = stack.pop()
        for child in children_by_parent.get(parent_id, []):
            doc_id = normalize_text(child.get("doc_id"))
            if doc_id and doc_id not in found:
                found.add(doc_id)
                stack.append(doc_id)
    return found


def archived_doc_ids(children_by_parent: dict[str, list[dict[str, Any]]]) -> set[str]:
    return {"_archive", *descendant_ids(children_by_parent, "_archive")}


def expand_selected_doc_ids(context: ExportContext, selected_doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    expanded: list[str] = []
    include_descendants = bool(context.config.get("selection", {}).get("include_descendants"))
    for raw_doc_id in selected_doc_ids:
        doc_id = normalize_text(raw_doc_id)
        if not doc_id:
            continue
        ids = [doc_id]
        if include_descendants:
            ids.extend(
                child_doc_id
                for child_doc_id in context.docs_by_id
                if child_doc_id in descendant_ids(context.children_by_parent, doc_id)
            )
        for candidate in ids:
            if candidate not in seen:
                seen.add(candidate)
                expanded.append(candidate)
    return expanded


def selected_docs(
    context: ExportContext,
    *,
    selected_doc_ids: list[str],
    select_all: bool,
    missing_summary_only: bool | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
    selection = context.config.get("selection", {})
    mode = normalize_text(selection.get("mode"))
    skipped: list[dict[str, str]] = []
    errors: list[str] = []
    archive_ids = archived_doc_ids(context.children_by_parent) if selection.get("exclude_archived") else set()

    if mode == "all_matching" or select_all:
        requested_ids = [normalize_text(doc.get("doc_id")) for doc in context.docs]
    else:
        requested_ids = expand_selected_doc_ids(context, selected_doc_ids)
        if not requested_ids:
            errors.append("explicit_doc_ids selection requires at least one --doc-id, --doc-ids, or --all")

    selected: list[dict[str, Any]] = []
    for doc_id in requested_ids:
        doc = context.docs_by_id.get(doc_id)
        if doc is None:
            skipped.append({"doc_id": doc_id, "reason": "unknown_doc_id"})
            continue
        if doc_id in archive_ids:
            skipped.append({"doc_id": doc_id, "reason": "archived"})
            continue
        if selection.get("exclude_unpublished") and doc.get("published") is False:
            skipped.append({"doc_id": doc_id, "reason": "unpublished"})
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

    return selected, skipped, errors


def effective_missing_summary_only(config: dict[str, Any], override: bool | None) -> bool:
    selection = config.get("selection", {})
    if override is not None:
        if not selection.get("supports_missing_summary_only") and override:
            return False
        return override
    return bool(selection.get("default_missing_summary_only")) if selection.get("supports_missing_summary_only") else False


def collect_headings(content_html: str, title: str) -> list[str]:
    parser = HeadingCollector()
    parser.feed(content_html)
    parser.close()
    normalized_title = normalize_text(title)
    headings: list[str] = []
    for heading in parser.headings:
        if not headings and normalized_title and heading == normalized_title:
            continue
        headings.append(heading)
    return headings


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
    if source in {"doc_id", "title", "parent_id", "summary", "last_updated", "viewable", "published"}:
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
        payload = load_doc_payload(context, doc_id)
        return collect_headings(str(payload.get("content_html") or ""), normalize_text(doc.get("title")))
    if source == "source_text":
        raise NotImplementedError("source_text extraction is implemented in Task 4")
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


def build_document_record(context: ExportContext, doc: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    record: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []
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
            errors.append(f"{doc_id}: unsupported transform(s) before Task 4: {', '.join(unsupported)}")
            continue
        try:
            value = source_value(context, doc, source)
        except NotImplementedError as exc:
            errors.append(f"{doc_id}: {exc}")
            continue

        if value is None and "default" in mapping:
            value = copy.deepcopy(mapping.get("default"))
        if value is None:
            value = ""
        if mapping.get("required") and value in ("", [], {}):
            errors.append(f"{doc_id}: required field {source} is empty")
            continue
        if not mapping.get("include_if_empty", True) and value in ("", [], {}):
            continue
        if not output_path:
            errors.append(f"{doc_id}: field {source} has blank output_path")
            continue
        set_output_path(record, output_path, value)
    return record, warnings, errors


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
        "scope": context.scope,
        "generated_at": generated_at,
        "selected_doc_ids": selected_doc_ids,
        "source_last_updated": source_last_updated,
        "counts": counts,
    }
    return {key: value for key, value in values.items() if key in include}


def resolve_output_path(repo_root: Path, config: dict[str, Any], scope: str, timestamp: str) -> Path:
    config_id = normalize_text(config.get("id"))
    pattern = normalize_text(config.get("output", {}).get("path_pattern"))
    if not pattern:
        raise ValueError(f"Export config {config_id} is missing output.path_pattern")
    relative = Path(
        pattern.format(
            scope=scope,
            timestamp=timestamp,
            export_id=config_id,
        )
    )
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe export output path: {relative}")
    if relative.parts[:3] != OUTPUT_ROOT.parts:
        raise ValueError(f"Export output path must stay under {OUTPUT_ROOT}: {relative}")
    return repo_root / relative


def build_export_payload(
    context: ExportContext,
    *,
    selected: list[dict[str, Any]],
    records: list[dict[str, Any]],
    generated_at: str,
    counts: dict[str, int],
) -> dict[str, Any] | list[dict[str, Any]]:
    metadata = export_metadata(context, generated_at=generated_at, selected=selected, counts=counts)
    target = context.config.get("target", {})
    record_shape = normalize_text(target.get("record_shape"))
    include_metadata = bool(target.get("include_export_metadata", True))
    if record_shape == "envelope":
        payload: dict[str, Any] = {}
        if include_metadata:
            payload.update(metadata)
        document_array_path = normalize_text(target.get("document_array_path") or "documents")
        set_output_path(payload, document_array_path, records)
        return payload
    if record_shape == "document_rows":
        if not include_metadata:
            return records
        rows: list[dict[str, Any]] = []
        for record in records:
            row = {"_export": metadata}
            row.update(record)
            rows.append(row)
        return rows
    raise ValueError(f"Unsupported target.record_shape: {record_shape}")


def parse_doc_ids(values: list[str]) -> list[str]:
    doc_ids: list[str] = []
    for value in values:
        for item in str(value or "").split(","):
            doc_id = normalize_text(item)
            if doc_id:
                doc_ids.append(doc_id)
    return doc_ids


def build_export(
    *,
    repo_root: Path,
    config_id: str,
    scope: str,
    selected_doc_ids: list[str],
    select_all: bool,
    missing_summary_only: bool | None,
    write: bool,
    config_path: str | None = None,
) -> dict[str, Any]:
    generated_at_dt = dt.datetime.now(dt.timezone.utc)
    generated_at = generated_at_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    config_payload = load_config_file(repo_root, config_path)
    config = find_export_config(config_payload, config_id)
    if scope not in config.get("scopes", []):
        raise ValueError(f"Export config {config_id} does not support scope {scope}")
    if not config.get("enabled", False):
        raise ValueError(f"Export config {config_id} is disabled")

    docs = load_scope_index(repo_root, scope)
    docs_by_id = {normalize_text(doc.get("doc_id")): doc for doc in docs}
    context = ExportContext(
        repo_root=repo_root,
        scope=scope,
        config=config,
        docs=docs,
        docs_by_id=docs_by_id,
        children_by_parent=build_children_by_parent(docs),
        payload_cache={},
    )
    selected, skipped, selection_errors = selected_docs(
        context,
        selected_doc_ids=selected_doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
    )

    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = list(selection_errors)
    for doc in selected:
        record, doc_warnings, doc_errors = build_document_record(context, doc)
        warnings.extend(doc_warnings)
        errors.extend(doc_errors)
        if not doc_errors:
            records.append(record)

    counts = {
        "selected": len(selected),
        "exported": len(records),
        "skipped": len(skipped),
        "truncated": 0,
    }
    timestamp_format = normalize_text(config.get("output", {}).get("timestamp_format") or "%Y%m%d-%H%M%S")
    timestamp = generated_at_dt.strftime(timestamp_format)
    output_path = resolve_output_path(repo_root, config, scope, timestamp)
    relative_output = str(output_path.relative_to(repo_root))
    target_format = normalize_text(config.get("target", {}).get("format"))
    report: dict[str, Any] = {
        "ok": not errors,
        "dry_run": not write,
        "config_id": config_id,
        "scope": scope,
        "target_format": target_format,
        "output_file": relative_output,
        "counts": counts,
        "selected_doc_ids": [normalize_text(doc.get("doc_id")) for doc in selected],
        "exported_doc_ids": [normalize_text(record.get("doc_id")) for record in records if isinstance(record, dict)],
        "skipped": skipped,
        "warnings": warnings,
        "errors": errors,
    }

    if errors:
        report["output_written"] = False
        return report

    payload = build_export_payload(
        context,
        selected=selected,
        records=records,
        generated_at=generated_at,
        counts=counts,
    )
    if write:
        if target_format == "json":
            if not isinstance(payload, dict):
                raise ValueError("JSON envelope payload must be an object")
            write_json(output_path, payload)
        elif target_format == "jsonl":
            if not isinstance(payload, list):
                raise ValueError("JSONL document_rows payload must be an array")
            write_jsonl(output_path, payload)
        else:
            raise ValueError(f"Unsupported target.format: {target_format}")
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
        )
    except Exception as exc:
        print(f"docs_export: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
