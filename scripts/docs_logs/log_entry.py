#!/usr/bin/env python3
"""Preview or append structured docs-log JSONL entries."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^change-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_RE = re.compile(r"[^a-z0-9]+")
DOC_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DOMAIN_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

STATUSES = {"implemented", "completed", "in-progress", "proposed", "decided", "superseded", "archived", "unknown"}
TYPES = {
    "implementation",
    "bugfix",
    "cleanup",
    "refactor",
    "documentation",
    "request",
    "decision",
    "verification",
    "migration",
    "maintenance",
    "other",
}

OPTIONAL_ARRAY_FIELDS = ("subjects", "related_docs", "related_files", "verification")
ALLOWED_FIELDS = {
    "id",
    "date",
    "title",
    "status",
    "type",
    "domains",
    "subjects",
    "change_request_doc_id",
    "related_docs",
    "related_files",
    "summary",
    "effect",
    "area",
    "affected",
    "verification",
    "body",
    "source",
    "migration",
}


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not find repo root containing _config.yml")


def split_values(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for part in value.split(","):
            text = part.strip()
            if text and text not in result:
                result.append(text)
    return result


def slugify(value: str) -> str:
    slug = SLUG_RE.sub("-", value.lower()).strip("-")
    return slug or "untitled"


def infer_domains(*values: str) -> list[str]:
    haystack = " ".join(value.lower() for value in values if value)
    candidates: list[tuple[str, tuple[str, ...]]] = [
        ("docs-viewer", ("docs-viewer", "docs viewer", "_docs", "docs/", "docs_")),
        ("search", ("search", "ranking", "normalisation", "normalization", "index")),
        ("catalogue", ("catalogue", "work editor", "series", "moment")),
        ("library", ("library", "_docs_library")),
        ("studio-ui", ("studio ui", "ui primitive", "modal", "css", "layout")),
        ("build", ("build", "generated", "payload", "jekyll")),
        ("scripts", ("script", "scripts/")),
        ("data-models", ("data model", "schema", "json")),
        ("config", ("config", "settings")),
        ("workflow", ("workflow", "change log", "docs log", "_docs_logs", "agents.md")),
        ("analytics", ("analytics", "tag")),
        ("runtime", ("runtime", "service", "server")),
    ]
    domains: list[str] = []
    for domain, keywords in candidates:
        if any(keyword in haystack for keyword in keywords):
            domains.append(domain)
    return domains


def parse_front_matter(text: str) -> tuple[dict[str, str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}, lines
    data: dict[str, str] = {}
    end_index = 0
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            end_index = index
            break
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        data[key.strip()] = raw_value.strip().strip('"')
    if not end_index:
        return {}, lines
    return data, lines[end_index + 1 :]


def find_doc_by_id(root: Path, doc_id: str) -> tuple[Path, dict[str, str], list[str]]:
    for path in sorted((root / "_docs").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        front_matter, body_lines = parse_front_matter(text)
        if front_matter.get("doc_id") == doc_id:
            return path, front_matter, body_lines
    raise ValueError(f"Could not find _docs source for doc_id: {doc_id}")


def section_lines(body_lines: list[str], heading: str) -> list[str]:
    start = None
    heading_text = f"## {heading}"
    for index, line in enumerate(body_lines):
        if line.strip().lower() == heading_text.lower():
            start = index + 1
            break
    if start is None:
        return []
    end = len(body_lines)
    for index in range(start, len(body_lines)):
        if body_lines[index].startswith("## "):
            end = index
            break
    return body_lines[start:end]


def first_paragraph(lines: list[str]) -> str:
    paragraph: list[str] = []
    for line in lines:
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
    return " ".join(paragraph)


def repo_relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def build_record(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    change_date = args.date or date.today().isoformat()
    title = args.title or ""
    summary = args.summary or ""
    source_file = args.source_file or ""
    source_line = args.source_line
    source_archive = args.source_archive or ""
    change_request_doc_id = args.change_request_doc_id or ""
    related_docs = split_values(args.related_doc)

    if args.from_change_request:
        doc_path, front_matter, body_lines = find_doc_by_id(root, args.from_change_request)
        change_request_doc_id = change_request_doc_id or args.from_change_request
        if args.from_change_request not in related_docs:
            related_docs.append(args.from_change_request)
        title = title or f"Completed {front_matter.get('title', args.from_change_request)}"
        summary = summary or first_paragraph(section_lines(body_lines, "Summary"))
        source_file = source_file or repo_relative(root, doc_path)
        source_archive = source_archive or "change-request"

    if not title:
        raise ValueError("--title is required unless --from-change-request can provide one")
    if not summary:
        raise ValueError("--summary is required unless --from-change-request has a Summary section")
    if not source_file:
        raise ValueError("--source-file is required for direct entries")

    entry_id = args.id or f"change-{change_date}-{slugify(title)}"
    domains = split_values(args.domain)
    if not domains:
        domains = infer_domains(
            title,
            summary,
            args.from_change_request or "",
            " ".join(related_docs),
            " ".join(split_values(args.related_file)),
            source_file,
        )
    record: dict[str, Any] = {
        "id": entry_id,
        "date": change_date,
        "title": title,
        "status": args.status,
        "type": args.type,
        "domains": domains,
        "summary": summary,
        "source": {"file": source_file},
    }
    if source_line:
        record["source"]["line"] = source_line
    if source_archive:
        record["source"]["archive"] = source_archive
    if args.subject:
        record["subjects"] = split_values(args.subject)
    if change_request_doc_id:
        record["change_request_doc_id"] = change_request_doc_id
    if related_docs:
        record["related_docs"] = related_docs
    related_files = split_values(args.related_file)
    if related_files:
        record["related_files"] = related_files
    if args.effect:
        record["effect"] = args.effect
    if args.area:
        record["area"] = args.area
    if args.body:
        record["body"] = args.body
    if args.verification:
        record["verification"] = split_values(args.verification)
    affected_files = split_values(args.affected_file)
    affected_docs = split_values(args.affected_doc)
    if affected_files or affected_docs:
        record["affected"] = {}
        if affected_files:
            record["affected"]["files"] = affected_files
        if affected_docs:
            record["affected"]["docs"] = affected_docs
    return record


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    unknown = sorted(set(record) - ALLOWED_FIELDS)
    if unknown:
        errors.append(f"unknown fields: {', '.join(unknown)}")
    for field in ("id", "date", "title", "status", "type", "domains", "summary", "source"):
        if field not in record:
            errors.append(f"missing required field: {field}")
    if "id" in record and not isinstance(record["id"], str) or ("id" in record and not ID_RE.match(record["id"])):
        errors.append("id must match change-YYYY-MM-DD-slug")
    if "date" in record:
        if not isinstance(record["date"], str) or not DATE_RE.match(record["date"]):
            errors.append("date must use YYYY-MM-DD")
        else:
            try:
                datetime.strptime(record["date"], "%Y-%m-%d")
            except ValueError:
                errors.append("date is not a valid calendar date")
    if record.get("status") not in STATUSES:
        errors.append(f"status must be one of: {', '.join(sorted(STATUSES))}")
    if record.get("type") not in TYPES:
        errors.append(f"type must be one of: {', '.join(sorted(TYPES))}")
    domains = record.get("domains")
    if not isinstance(domains, list) or not domains:
        errors.append("domains must be a non-empty list")
    elif len(domains) != len(set(domains)):
        errors.append("domains must be unique")
    else:
        for domain in domains:
            if not isinstance(domain, str) or not DOMAIN_RE.match(domain):
                errors.append(f"invalid domain: {domain!r}")
    for field in ("title", "summary"):
        if not isinstance(record.get(field), str) or not record.get(field, "").strip():
            errors.append(f"{field} must be a non-empty string")
    for field in OPTIONAL_ARRAY_FIELDS:
        value = record.get(field)
        if value is not None and (not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value)):
            errors.append(f"{field} must be a list of non-empty strings")
        if isinstance(value, list) and len(value) != len(set(value)):
            errors.append(f"{field} values must be unique")
    for field in ("change_request_doc_id",):
        value = record.get(field)
        if value is not None and (not isinstance(value, str) or not DOC_ID_RE.match(value)):
            errors.append(f"{field} must be a docs-style id")
    for field in ("related_docs",):
        for value in record.get(field, []):
            if not DOC_ID_RE.match(value):
                errors.append(f"{field} contains invalid doc id: {value}")
    source = record.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("file"), str) or not source.get("file"):
        errors.append("source.file is required")
    elif set(source) - {"file", "line", "archive"}:
        errors.append("source contains unknown fields")
    elif "line" in source and (not isinstance(source["line"], int) or source["line"] < 1):
        errors.append("source.line must be a positive integer")
    return errors


def jsonl_path(root: Path, change_date: str) -> Path:
    return root / "_docs_logs" / "entries" / f"{change_date[:7]}.jsonl"


def existing_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for path in (root / "_docs_logs" / "entries").glob("*.jsonl"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
            entry_id = row.get("id")
            if isinstance(entry_id, str):
                ids.add(entry_id)
    return ids


def append_record(root: Path, record: dict[str, Any]) -> Path:
    path = jsonl_path(root, record["date"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if record["id"] in existing_ids(root):
        raise ValueError(f"docs log entry already exists: {record['id']}")
    encoded = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    if path.exists() and path.read_text(encoding="utf-8") and not path.read_text(encoding="utf-8").endswith("\n"):
        prefix = "\n"
    else:
        prefix = ""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(prefix + encoded + "\n")
    return path


def update_change_request(root: Path, doc_id: str, entry_id: str, dry_run: bool) -> None:
    path, _, _ = find_doc_by_id(root, doc_id)
    text = path.read_text(encoding="utf-8")
    entry_line = f"- `{entry_id}`"
    if entry_line in text:
        print(f"change request already references {entry_id}: {repo_relative(root, path)}")
        return
    heading = "## Change Log Entries"
    if heading in text:
        updated = text.replace(heading, f"{heading}\n\n{entry_line}", 1)
    else:
        suffix = "" if text.endswith("\n") else "\n"
        updated = f"{text}{suffix}\n{heading}\n\n{entry_line}\n"
    if dry_run:
        print(f"would update change request: {repo_relative(root, path)}")
        return
    path.write_text(updated, encoding="utf-8")
    print(f"updated change request: {repo_relative(root, path)}")


def maybe_rebuild_generated(root: Path, dry_run: bool, skip: bool) -> None:
    if skip:
        return
    script = root / "scripts" / "docs_logs" / "build_indexes.py"
    if not script.exists():
        print("generated log rebuild skipped: scripts/docs_logs/build_indexes.py is not implemented yet", file=sys.stderr)
        return
    command = [sys.executable, str(script), "--write"]
    if dry_run:
        print("would run:", " ".join(command))
        return
    subprocess.run(command, cwd=root, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-change-request", help="Seed fields from a _docs change request doc_id.")
    parser.add_argument("--id", help="Explicit entry id. Defaults to change-<date>-<title-slug>.")
    parser.add_argument("--date", help="Change date in YYYY-MM-DD form. Defaults to today.")
    parser.add_argument("--title", help="Entry title.")
    parser.add_argument("--summary", help="Short factual summary.")
    parser.add_argument("--effect", help="Why the change matters.")
    parser.add_argument("--status", default="implemented", choices=sorted(STATUSES))
    parser.add_argument("--type", default="implementation", choices=sorted(TYPES))
    parser.add_argument("--domain", action="append", help="Domain id. Repeat or comma-separate.")
    parser.add_argument("--subject", action="append", help="Subject tag. Repeat or comma-separate.")
    parser.add_argument("--related-doc", action="append", help="Related Docs Viewer doc_id. Repeat or comma-separate.")
    parser.add_argument("--related-file", action="append", help="Related repo file. Repeat or comma-separate.")
    parser.add_argument("--affected-file", action="append", help="Affected file. Repeat or comma-separate.")
    parser.add_argument("--affected-doc", action="append", help="Affected doc id or title. Repeat or comma-separate.")
    parser.add_argument("--change-request-doc-id", help="Explicit originating change request doc_id.")
    parser.add_argument("--source-file", help="Best source trace for this entry.")
    parser.add_argument("--source-line", type=int, help="Source line for the entry trace.")
    parser.add_argument("--source-archive", help="Source archive or bucket label.")
    parser.add_argument("--area", help="Legacy changelog area text.")
    parser.add_argument("--body", help="Preserved prose when structured fields are insufficient.")
    parser.add_argument("--verification", action="append", help="Verification note. Repeat or comma-separate.")
    parser.add_argument("--write", action="store_true", help="Append the JSONL row. Default is preview only.")
    parser.add_argument("--update-change-request", action="store_true", help="Add the entry id to the source change request doc.")
    parser.add_argument("--no-rebuild-generated", action="store_true", help="Do not run the generated index rebuild hook after writing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = repo_root()
        record = build_record(args, root)
        errors = validate_record(record)
        if errors:
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
            return 2
        print(json.dumps(record, indent=2, ensure_ascii=False))
        if not args.write:
            print("preview only; pass --write to append this entry")
            if args.update_change_request and record.get("change_request_doc_id"):
                update_change_request(root, record["change_request_doc_id"], record["id"], dry_run=True)
            return 0
        path = append_record(root, record)
        print(f"appended: {repo_relative(root, path)}")
        if args.update_change_request and record.get("change_request_doc_id"):
            update_change_request(root, record["change_request_doc_id"], record["id"], dry_run=False)
        maybe_rebuild_generated(root, dry_run=False, skip=args.no_rebuild_generated)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
