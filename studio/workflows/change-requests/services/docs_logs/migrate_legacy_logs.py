#!/usr/bin/env python3
"""Parse legacy Markdown change logs into structured docs-log records."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

try:
    from log_entry import STATUSES, infer_domains, slugify, validate_record
except ModuleNotFoundError:  # pragma: no cover - package import path for tests
    from docs_logs.log_entry import STATUSES, infer_domains, slugify, validate_record


ENTRY_HEADING_RE = re.compile(r"^## \[([0-9]{4}-[0-9]{2}-[0-9]{2})\]\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^\*\*([^:*]+):\*\*(?:\s*(.*))?$")
DOC_LINK_RE = re.compile(r"\]\(/docs/\?scope=[^)#&\s]+&doc=([a-z0-9]+(?:-[a-z0-9]+)*)[^)]*\)")
PATH_TOKEN_RE = re.compile(r"`([^`]+)`")
WHITESPACE_RE = re.compile(r"\s+")

DEFAULT_SOURCE_FILES = (
    "studio/docs-viewer/source/studio/site-change-log.md",
    "studio/docs-viewer/source/studio/site-change-log-2026-05.md",
    "studio/docs-viewer/source/studio/site-change-log-2026-04.md",
    "studio/docs-viewer/source/studio/site-change-log-2026-03-and-earlier.md",
    "studio/docs-viewer/source/studio/search-change-log.md",
)

FIELD_ALIASES = {
    "affected files/docs": "affected",
    "affected files": "affected",
    "affected docs": "affected",
}


@dataclass(frozen=True)
class LegacyEntry:
    source_file: str
    start_line: int
    end_line: int
    date: str
    title: str
    body: str


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not find repo root containing _config.yml")


def repo_relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def normalize_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def first_paragraph(value: str) -> str:
    paragraph: list[str] = []
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith(("-", "#", "```")):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    return normalize_text(" ".join(paragraph))


def parse_entries(path: Path, root: Path) -> list[LegacyEntry]:
    lines = path.read_text(encoding="utf-8").splitlines()
    source_file = repo_relative(root, path)
    headings: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines, start=1):
        match = ENTRY_HEADING_RE.match(line)
        if match:
            headings.append((index, match.group(1), normalize_text(match.group(2))))

    entries: list[LegacyEntry] = []
    for heading_index, (start_line, change_date, title) in enumerate(headings):
        end_line = headings[heading_index + 1][0] - 1 if heading_index + 1 < len(headings) else len(lines)
        body_lines = lines[start_line:end_line]
        body = "\n".join(body_lines).strip()
        entries.append(
            LegacyEntry(
                source_file=source_file,
                start_line=start_line,
                end_line=end_line,
                date=change_date,
                title=title,
                body=body,
            )
        )
    return entries


def parse_field_blocks(body: str) -> dict[str, str]:
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = FIELD_RE.match(line.strip())
        if match:
            label = match.group(1).strip().lower()
            label = FIELD_ALIASES.get(label, label)
            current = label
            fields.setdefault(current, [])
            inline = (match.group(2) or "").strip()
            if inline:
                fields[current].append(inline)
            continue
        if current:
            fields[current].append(line)
    return {key: "\n".join(value).strip() for key, value in fields.items()}


def extract_doc_ids(*values: str) -> list[str]:
    docs: list[str] = []
    for value in values:
        for match in DOC_LINK_RE.finditer(value):
            doc_id = match.group(1)
            if doc_id not in docs:
                docs.append(doc_id)
    return docs


def is_repo_path(value: str) -> bool:
    candidate = value.strip().strip(".,:;")
    if not candidate or " " in candidate:
        return False
    if candidate.startswith(("./", "_", "assets/", "scripts/", "tests/", "studio/", "data/", "var/", "bin/")):
        return True
    suffixes = (".md", ".rb", ".py", ".js", ".css", ".json", ".yml", ".yaml", ".html", ".txt")
    return any(candidate.endswith(suffix) for suffix in suffixes)


def normalize_path_token(value: str) -> str:
    return value.strip().strip(".,:;").removeprefix("./")


def extract_paths(*values: str) -> list[str]:
    paths: list[str] = []
    for value in values:
        for match in PATH_TOKEN_RE.finditer(value):
            path = normalize_path_token(match.group(1))
            if is_repo_path(path) and path not in paths:
                paths.append(path)
    return paths


def source_archive(source_file: str) -> str:
    if source_file == "studio/docs-viewer/source/studio/search-change-log.md":
        return "search"
    match = re.search(r"site-change-log-([0-9]{4}-[0-9]{2}(?:-and-earlier)?)\.md$", source_file)
    if match:
        return match.group(1)
    return "current"


def normalize_status(value: str) -> str:
    status = normalize_text(value).lower().replace(" ", "-")
    return status if status in STATUSES else "unknown"


def infer_type(title: str, fields: dict[str, str]) -> str:
    haystack = f"{title} {fields.get('area', '')} {fields.get('summary', '')}".lower()
    candidates: list[tuple[str, tuple[str, ...]]] = [
        ("bugfix", ("fixed", "fix ", "bug", "regression")),
        ("cleanup", ("retired", "removed", "cleanup", "pruned")),
        ("refactor", ("refactor", "extracted", "split", "moved")),
        ("documentation", ("documented", "documentation", "guidance", "readme")),
        ("verification", ("verified", "smoke", "test")),
        ("migration", ("migrated", "migration", "converted")),
        ("maintenance", ("maintenance", "backup", "retention")),
    ]
    for entry_type, keywords in candidates:
        if any(keyword in haystack for keyword in keywords):
            return entry_type
    return "implementation"


def infer_request_doc_id(related_docs: list[str]) -> tuple[str | None, list[str]]:
    request_docs = [doc_id for doc_id in related_docs if doc_id.startswith("site-request-") or doc_id.startswith("ui-request-")]
    if len(request_docs) == 1:
        return request_docs[0], []
    if len(request_docs) > 1:
        return None, ["multiple candidate change request docs"]
    return None, []


def build_record(entry: LegacyEntry, duplicate_index: int = 1) -> tuple[dict[str, Any], list[str]]:
    fields = parse_field_blocks(entry.body)
    warnings: list[str] = []
    summary = first_paragraph(fields.get("summary", "")) or first_paragraph(entry.body)
    if not summary:
        summary = entry.title
        warnings.append("summary inferred from title")

    area = normalize_text(fields.get("area", ""))
    affected = fields.get("affected", "")
    related_docs = extract_doc_ids(entry.body)
    related_files = extract_paths(affected, entry.body)
    domains = infer_domains(entry.title, summary, area, affected, " ".join(related_docs), " ".join(related_files))
    if source_archive(entry.source_file) == "search" and "search" not in domains:
        domains.insert(0, "search")
    if not domains:
        domains = ["site"]
        warnings.append("domain fallback used")

    change_request_doc_id, request_warnings = infer_request_doc_id(related_docs)
    warnings.extend(request_warnings)

    record_id = f"change-{entry.date}-{slugify(entry.title)}"
    if duplicate_index > 1:
        record_id = f"{record_id}-{duplicate_index}"
        warnings.append("duplicate generated id; numeric suffix added")

    record: dict[str, Any] = {
        "id": record_id,
        "date": entry.date,
        "title": entry.title,
        "status": normalize_status(fields.get("status", "")),
        "type": infer_type(entry.title, fields),
        "domains": domains,
        "summary": summary,
        "source": {
            "file": entry.source_file,
            "line": entry.start_line,
            "archive": source_archive(entry.source_file),
        },
        "body": entry.body,
        "migration": {
            "confidence": "high",
            "warnings": [],
        },
    }
    if area:
        record["area"] = area
    effect = first_paragraph(fields.get("effect", "")) or first_paragraph(fields.get("reason", ""))
    if effect:
        record["effect"] = effect
    if related_docs:
        record["related_docs"] = related_docs
    if related_files:
        record["related_files"] = related_files
    if change_request_doc_id:
        record["change_request_doc_id"] = change_request_doc_id
    affected_files = extract_paths(affected)
    affected_docs = extract_doc_ids(affected)
    if affected_files or affected_docs:
        record["affected"] = {}
        if affected_files:
            record["affected"]["files"] = affected_files
        if affected_docs:
            record["affected"]["docs"] = affected_docs
    verification = first_paragraph(fields.get("verification", ""))
    if verification:
        record["verification"] = [verification]

    validation_errors = validate_record(record)
    warnings.extend(validation_errors)
    confidence = "high"
    if validation_errors or record["status"] == "unknown" or "domain fallback used" in warnings:
        confidence = "low"
    elif warnings or not record.get("effect"):
        confidence = "medium"
    record["migration"] = {"confidence": confidence, "warnings": warnings}
    return record, warnings


def build_records(entries: list[LegacyEntry]) -> list[dict[str, Any]]:
    base_ids = [f"change-{entry.date}-{slugify(entry.title)}" for entry in entries]
    total_counts = Counter(base_ids)
    seen_counts: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    for entry, base_id in zip(entries, base_ids):
        seen_counts[base_id] += 1
        duplicate_index = seen_counts[base_id] if total_counts[base_id] > 1 else 1
        record, _ = build_record(entry, duplicate_index=duplicate_index)
        records.append(record)
    return records


def entry_path(root: Path, entry_id: str) -> Path:
    return root / "studio/workflows/change-requests" / "logs" / "entries" / f"{entry_id}.json"


def build_report(records: list[dict[str, Any]], source_files: list[str]) -> dict[str, Any]:
    by_source = Counter(str(record["source"]["file"]) for record in records)
    by_month = Counter(str(record["date"])[:7] for record in records)
    by_domain: Counter[str] = Counter()
    warnings: list[dict[str, Any]] = []
    for record in records:
        by_domain.update(record.get("domains", []))
        migration = record.get("migration", {})
        record_warnings = migration.get("warnings", [])
        if record_warnings or migration.get("confidence") != "high":
            warnings.append(
                {
                    "id": record["id"],
                    "source": record["source"],
                    "confidence": migration.get("confidence"),
                    "warnings": record_warnings,
                }
            )
    duplicate_ids = sorted(entry_id for entry_id, count in Counter(record["id"] for record in records).items() if count > 1)
    return {
        "generated_on": date.today().isoformat(),
        "source_files": source_files,
        "summary": {
            "entries": len(records),
            "sources": dict(sorted(by_source.items())),
            "months": dict(sorted(by_month.items())),
            "domains": dict(sorted(by_domain.items())),
            "warnings": len(warnings),
            "duplicate_ids": duplicate_ids,
        },
        "entries": [
            {
                "id": record["id"],
                "date": record["date"],
                "title": record["title"],
                "status": record["status"],
                "type": record["type"],
                "domains": record["domains"],
                "related_docs": record.get("related_docs", []),
                "related_files": record.get("related_files", []),
                "change_request_doc_id": record.get("change_request_doc_id"),
                "source": record["source"],
                "migration": record.get("migration", {}),
            }
            for record in records
        ],
        "review": warnings,
    }


def write_entry_records(root: Path, records: list[dict[str, Any]], replace: bool = False) -> list[str]:
    duplicate_ids = sorted(entry_id for entry_id, count in Counter(str(record["id"]) for record in records).items() if count > 1)
    if duplicate_ids:
        raise ValueError(f"duplicate generated ids: {', '.join(duplicate_ids)}")

    paths: dict[Path, dict[str, Any]] = {}
    for record in records:
        paths[entry_path(root, str(record["id"]))] = record

    written: list[str] = []
    for path, record in sorted(paths.items()):
        if path.exists() and path.read_text(encoding="utf-8").strip() and not replace:
            raise FileExistsError(f"{repo_relative(root, path)} already exists; pass --replace to overwrite migration output")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(repo_relative(root, path))
    return written


def load_entries(root: Path, source_files: list[str]) -> list[LegacyEntry]:
    entries: list[LegacyEntry] = []
    for source in source_files:
        path = (root / source).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Missing source changelog: {source}")
        entries.extend(parse_entries(path, root))
    return entries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-file", action="append", help="Legacy changelog Markdown file. Repeatable.")
    parser.add_argument("--write", action="store_true", help="Write per-entry JSON records and migration report.")
    parser.add_argument("--replace", action="store_true", help="Overwrite existing per-entry migration JSON outputs.")
    parser.add_argument("--report-path", default="studio/workflows/change-requests/reports/migration-review.json", help="Migration report path.")
    parser.add_argument("--json", action="store_true", help="Print the full migration report as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = repo_root()
        source_files = args.source_file or list(DEFAULT_SOURCE_FILES)
        entries = load_entries(root, source_files)
        records = build_records(entries)
        report = build_report(records, source_files)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            summary = report["summary"]
            print(f"parsed entries: {summary['entries']}")
            print(f"source files: {len(source_files)}")
            print(f"months: {len(summary['months'])}")
            print(f"domains: {len(summary['domains'])}")
            print(f"entries needing review: {summary['warnings']}")
        if not args.write:
            print("preview only; pass --write to create JSON records and the migration report")
            return 0
        written = write_entry_records(root, records, replace=args.replace)
        report_path = root / args.report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("wrote:")
        for path in [*written, repo_relative(root, report_path)]:
            print(f"- {path}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
