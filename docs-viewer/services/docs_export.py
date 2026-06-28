#!/usr/bin/env python3
"""Export Docs Viewer source data through configured prepare profiles.

Run:
  ./docs-viewer/services/docs_export.py --config-id document-content --scope library
  ./docs-viewer/services/docs_export.py --config-id document-content --scope library --write
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from docs_export_common import (
    data_sharing_header_row,
    export_id_from_generated_at,
    normalize_text,
    package_context_sidecar_path,
    package_metadata_path,
    write_json,
    write_jsonl,
)
from docs_export_config import (
    SUPPORTED_TARGET_FORMATS,
    find_export_config,
    load_config_file,
    supported_target_formats,
    validate_config_payload,
    validate_export_config,
)
from docs_export_payloads import (
    build_document_tree_payload,
    build_export_payload,
    build_external_context,
    export_metadata,
    resolve_output_path,
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
from docs_export_transforms import build_document_record


ZERO_EXPORT_COUNTS = {"selected": 0, "exported": 0, "skipped": 0, "failed": 0, "truncated": 0}


@dataclasses.dataclass(frozen=True)
class ExportOutputPaths:
    output_path: Path | None = None
    output_file: str = ""
    metadata_path: Path | None = None
    metadata_file: str = ""
    context_path: Path | None = None
    context_file: str = ""


@dataclasses.dataclass(frozen=True)
class ExportRecordBuild:
    records: list[dict[str, Any]]
    warnings: list[str]
    errors: list[str]
    failed_count: int
    truncated_count: int


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


def empty_export_report(
    *,
    write: bool,
    export_id: str,
    config_id: str,
    scope: str,
    target_format: str,
    paths: ExportOutputPaths | None = None,
    warnings: list[str],
    errors: list[str],
    supported_formats: list[str] | None = None,
) -> dict[str, Any]:
    output_paths = paths or ExportOutputPaths()
    report: dict[str, Any] = {
        "ok": False,
        "dry_run": not write,
        "export_id": export_id,
        "config_id": config_id,
        "scope": scope,
        "target_format": target_format,
        "output_file": output_paths.output_file,
        "metadata_file": output_paths.metadata_file,
        "context_file": output_paths.context_file,
        "counts": dict(ZERO_EXPORT_COUNTS),
        "selected_doc_ids": [],
        "exported_doc_ids": [],
        "skipped": [],
        "skipped_summary": {},
        "warnings": warnings,
        "errors": errors,
        "issue_counts": {"errors": len(errors), "warnings": len(warnings)},
        "output_written": False,
    }
    if supported_formats is not None:
        report["supported_target_formats"] = supported_formats
    return report


def resolve_export_paths(
    *,
    repo_root: Path,
    config: dict[str, Any],
    config_id: str,
    data_domain: str,
    export_id: str,
    timestamp: str,
    target_format: str,
    output_root: Path | str | None,
) -> tuple[ExportOutputPaths, list[str]]:
    try:
        output_path = resolve_output_path(repo_root, config, data_domain, export_id, timestamp, target_format, output_root)
        metadata_path = package_metadata_path(repo_root, export_id)
        context_path = package_context_sidecar_path(output_path)
    except ValueError as exc:
        return ExportOutputPaths(), [f"config {config_id}: {exc}"]
    return (
        ExportOutputPaths(
            output_path=output_path,
            output_file=str(output_path.relative_to(repo_root)),
            metadata_path=metadata_path,
            metadata_file=str(metadata_path.relative_to(repo_root)),
            context_path=context_path,
            context_file=str(context_path.relative_to(repo_root)),
        ),
        [],
    )


def build_records_for_export(
    *,
    context: ExportContext,
    selected: list[dict[str, Any]],
    record_shape: str,
    config_id: str,
) -> ExportRecordBuild:
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
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
    return ExportRecordBuild(
        records=records,
        warnings=warnings,
        errors=errors,
        failed_count=failed_count,
        truncated_count=truncated_count,
    )


def write_export_outputs(
    *,
    paths: ExportOutputPaths,
    target_format: str,
    export_id: str,
    payload: dict[str, Any] | list[dict[str, Any]],
    metadata: dict[str, Any],
    external_context: dict[str, Any],
) -> None:
    if paths.output_path is None:
        raise ValueError("Export output path was not resolved")
    if target_format == "json":
        write_json(paths.output_path, payload)
    elif target_format == "jsonl":
        if not isinstance(payload, list):
            raise ValueError("JSONL document_rows payload must be an array")
        write_jsonl(paths.output_path, [data_sharing_header_row(export_id), *payload])
    else:
        raise ValueError(f"Unsupported target.format: {target_format}")
    if paths.metadata_path is not None:
        write_json(paths.metadata_path, metadata)
    if paths.context_path is not None:
        write_json(paths.context_path, external_context)


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
        return empty_export_report(
            write=write,
            export_id=export_id,
            config_id=config_id,
            scope=scope,
            target_format="",
            warnings=payload_warnings,
            errors=payload_errors,
        )
    try:
        config = find_export_config(config_payload, config_id)
    except ValueError as exc:
        return empty_export_report(
            write=write,
            export_id=export_id,
            config_id=config_id,
            scope=scope,
            target_format="",
            warnings=payload_warnings,
            errors=[str(exc)],
        )
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
    paths, path_errors = resolve_export_paths(
        repo_root=repo_root,
        config=config,
        config_id=config_id,
        data_domain=data_domain,
        export_id=export_id,
        timestamp=timestamp,
        target_format=resolved_target_format,
        output_root=output_root,
    )
    errors.extend(path_errors)
    if write and paths.metadata_path is not None and paths.metadata_path.exists():
        errors.append(f"export_id {export_id}: metadata file already exists")

    if errors:
        return empty_export_report(
            write=write,
            export_id=export_id,
            config_id=config_id,
            scope=scope,
            target_format=resolved_target_format,
            paths=paths,
            warnings=warnings,
            errors=errors,
        )

    try:
        source_context, docs = load_source_export_context(repo_root, scope)
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        return empty_export_report(
            write=write,
            export_id=export_id,
            config_id=config_id,
            scope=scope,
            target_format=resolved_target_format,
            paths=paths,
            warnings=warnings,
            errors=[f"source metadata: {exc}"],
            supported_formats=supported_formats,
        )
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

    warnings.extend(selection_warnings)
    warnings.extend(skipped_summary_warnings(skipped))
    record_build = build_records_for_export(
        context=context,
        selected=selected,
        record_shape=record_shape,
        config_id=config_id,
    )
    warnings.extend(record_build.warnings)
    errors = [*selection_errors, *record_build.errors]

    counts = {
        "selected": len(selected),
        "exported": len(record_build.records),
        "skipped": len(skipped),
        "failed": record_build.failed_count,
        "truncated": record_build.truncated_count,
    }
    report: dict[str, Any] = {
        "ok": not errors,
        "dry_run": not write,
        "export_id": export_id,
        "config_id": config_id,
        "scope": scope,
        "target_format": resolved_target_format,
        "supported_target_formats": supported_formats,
        "output_file": paths.output_file,
        "metadata_file": paths.metadata_file,
        "context_file": paths.context_file,
        "counts": counts,
        "selected_doc_ids": [normalize_text(doc.get("doc_id")) for doc in selected],
        "exported_doc_ids": [normalize_text(record.get("doc_id")) for record in record_build.records if isinstance(record, dict)],
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
            records=record_build.records,
            target_format=resolved_target_format,
        )
    external_context = build_external_context(config, resolved_target_format)
    if write:
        write_export_outputs(
            paths=paths,
            target_format=resolved_target_format,
            export_id=export_id,
            payload=payload,
            metadata=metadata,
            external_context=external_context,
        )
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
