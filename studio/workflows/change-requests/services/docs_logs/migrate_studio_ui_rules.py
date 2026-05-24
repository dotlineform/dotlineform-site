#!/usr/bin/env python3
"""Migrate the legacy Studio UI rule log into structured docs-log entries."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from log_entry import slugify, validate_record
except ModuleNotFoundError:  # pragma: no cover - package import path for tests
    from docs_logs.log_entry import slugify, validate_record


SOURCE_DOC = Path("docs-viewer/source/studio/studio-ui-rules.md")
ENTRY_HEADING_RE = re.compile(r"^## UI Rule Log (?P<date>\d{4}-\d{2}-\d{2}) / (?P<ui_id>UI-[A-Z0-9]+)\s*$", re.MULTILINE)
TOP_LEVEL_FIELD_RE = re.compile(r"^- (?P<key>[A-Za-z][A-Za-z ]+):\s*(?P<value>.*)$")
DOC_LINK_RE = re.compile(r"/docs/\?scope=studio&doc=([a-z0-9]+(?:-[a-z0-9]+)*)")


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


def parse_front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def docs_by_source(root: Path) -> dict[str, str]:
    docs: dict[str, str] = {}
    for path in sorted((root / "docs-viewer/source/studio").glob("*.md")):
        front_matter = parse_front_matter(path.read_text(encoding="utf-8"))
        doc_id = front_matter.get("doc_id")
        if doc_id:
            docs[repo_relative(root, path)] = doc_id
            docs[path.name] = doc_id
    return docs


def split_entries(text: str) -> list[dict[str, Any]]:
    matches = list(ENTRY_HEADING_RE.finditer(text))
    entries: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        entries.append(
            {
                "date": match.group("date"),
                "ui_id": match.group("ui_id"),
                "line": text.count("\n", 0, match.start()) + 1,
                "body": text[start:end].strip(),
            }
        )
    return entries


def parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, list[str]] = {}
    current_key = ""
    for line in body.splitlines():
        match = TOP_LEVEL_FIELD_RE.match(line)
        if match:
            current_key = match.group("key").strip().lower()
            fields[current_key] = []
            value = match.group("value").strip()
            if value:
                fields[current_key].append(value)
            continue
        if current_key:
            fields[current_key].append(line)
    return {key: "\n".join(value).strip() for key, value in fields.items()}


def strip_markdown(value: str) -> str:
    text = value.replace("`", "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def first_sentence(value: str, *, fallback: str) -> str:
    text = strip_markdown(value)
    if not text:
        return fallback
    parts = re.split(r"(?<=[.!?])\s+", text)
    first = parts[0].strip()
    return first or fallback


def truncate_words(value: str, limit: int) -> str:
    words = value.split()
    if len(words) <= limit:
        return value
    return " ".join(words[:limit]).rstrip(".,;:") + "..."


def extract_list_items(value: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    for line in value.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            if current:
                items.append(" ".join(current).strip())
            current = [stripped[2:].strip()]
        elif current and stripped:
            current.append(stripped)
    if current:
        items.append(" ".join(current).strip())
    return [item for item in items if item]


def infer_domains(text: str, files: list[str]) -> list[str]:
    haystack = " ".join([text, *files]).lower()
    domains = ["studio-ui"]
    checks: list[tuple[str, tuple[str, ...]]] = [
        ("docs-viewer", ("docs-viewer", "docs viewer", "/docs/", "docs-viewer/source/studio/", "docs/", "library/", "analysis/")),
        ("catalogue", ("catalogue", "work editor", "series editor", "moment", "work-detail", "work_detail")),
        ("search", ("search", "ranking", "search index")),
        ("library", ("library", "docs-viewer/source/library")),
        ("build", ("build", "generated", "payload", "jekyll")),
        ("scripts", ("scripts/", "server.py", ".rb", ".py")),
        ("config", ("config", "settings", "studio_config", "ui_text")),
        ("data-models", ("schema", "data model", ".json")),
        ("analytics", ("analytics", "activity")),
        ("runtime", ("runtime", "server", "service")),
    ]
    for domain, needles in checks:
        if domain not in domains and any(needle in haystack for needle in needles):
            domains.append(domain)
    return domains


def status_for(raw_status: str) -> str:
    normalized = raw_status.strip().lower()
    if "superseded" in normalized:
        return "superseded"
    if normalized == "adopted":
        return "implemented"
    return "unknown"


def build_title(ui_id: str, fields: dict[str, str]) -> str:
    source = fields.get("outcome") or fields.get("issue") or fields.get("reasoning") or "Studio UI rule"
    text = first_sentence(source, fallback="Studio UI rule")
    for prefix in ("the ", "changed ", "added ", "updated "):
        if text.lower().startswith(prefix):
            break
    return f"{ui_id}: {truncate_words(text, 12)}"


def unique_entry_id(date: str, title: str, ui_id: str, body: str, used: Counter[str], existing: set[str]) -> str:
    base_slug = slugify(f"studio-ui-rule-{ui_id.lower()}-{title.split(':', 1)[-1]}")
    words = base_slug.split("-")
    base_slug = "-".join(words[:14]).strip("-")
    entry_id = f"change-{date}-{base_slug}"
    if entry_id not in existing and not used[entry_id]:
        used[entry_id] += 1
        return entry_id
    issue_slug = slugify(first_sentence(body, fallback=ui_id))
    entry_id = f"change-{date}-{base_slug}-line-{slugify(str(len(body)))}"
    if entry_id not in existing and not used[entry_id]:
        used[entry_id] += 1
        return entry_id
    counter = 2
    while True:
        candidate = f"change-{date}-{base_slug}-{counter}"
        if candidate not in existing and not used[candidate]:
            used[candidate] += 1
            return candidate
        counter += 1


def related_docs_for(body: str, files: list[str], docs_map: dict[str, str]) -> list[str]:
    related: list[str] = []
    for doc_id in DOC_LINK_RE.findall(body):
        if doc_id not in related and doc_id != "studio-ui-rules":
            related.append(doc_id)
    for file_path in files:
        doc_id = docs_map.get(file_path) or docs_map.get(Path(file_path).name)
        if doc_id and doc_id not in related and doc_id != "studio-ui-rules":
            related.append(doc_id)
    return related


def build_record(entry: dict[str, Any], docs_map: dict[str, str], used: Counter[str], existing: set[str]) -> dict[str, Any]:
    fields = parse_fields(entry["body"])
    files = extract_list_items(fields.get("files changed", ""))
    verification = extract_list_items(fields.get("local verification", ""))
    ui_id = entry["ui_id"]
    title = build_title(ui_id, fields)
    issue = first_sentence(fields.get("issue", ""), fallback="Studio UI rule was recorded.")
    outcome = first_sentence(fields.get("outcome", ""), fallback="")
    summary = f"{issue} Outcome: {outcome}" if outcome else issue
    effect = first_sentence(fields.get("reasoning", ""), fallback="")
    route = strip_markdown(fields.get("route", ""))
    triage = strip_markdown(fields.get("triage", ""))
    subjects = ["studio-ui-rule", ui_id]
    for value in (route, triage):
        if value and value not in subjects:
            subjects.append(value)
    body = f"## UI Rule Log {entry['date']} / {ui_id}\n\n{entry['body'].strip()}\n"
    warnings: list[str] = []
    for key in ("issue", "outcome", "reasoning"):
        if not fields.get(key):
            warnings.append(f"missing {key} field")
    record: dict[str, Any] = {
        "id": unique_entry_id(entry["date"], title, ui_id, entry["body"], used, existing),
        "date": entry["date"],
        "title": title,
        "status": status_for(fields.get("status", "")),
        "type": "decision",
        "domains": infer_domains(entry["body"], files),
        "subjects": subjects,
        "summary": summary,
        "source": {
            "file": SOURCE_DOC.as_posix(),
            "line": entry["line"],
            "archive": "studio-ui-rules",
        },
        "body": body,
        "migration": {
            "confidence": "high" if not warnings else "medium",
            "warnings": warnings,
        },
    }
    if effect:
        record["effect"] = effect
    if triage or route:
        record["area"] = " / ".join(part for part in [route, triage] if part)
    related_docs = related_docs_for(entry["body"], files, docs_map)
    if related_docs:
        record["related_docs"] = related_docs
    if files:
        record["related_files"] = files
        record["affected"] = {"files": files}
        if related_docs:
            record["affected"]["docs"] = related_docs
    if verification:
        record["verification"] = verification
    return record


def existing_entry_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for path in (root / "studio/workflows/change-requests" / "logs" / "entries").glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        entry_id = record.get("id")
        if isinstance(entry_id, str):
            ids.add(entry_id)
    return ids


def write_records(root: Path, records: list[dict[str, Any]]) -> list[str]:
    written: list[str] = []
    entries_dir = root / "studio/workflows/change-requests" / "logs" / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        path = entries_dir / f"{record['id']}.json"
        if path.exists():
            raise ValueError(f"entry already exists: {repo_relative(root, path)}")
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(repo_relative(root, path))
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write migrated JSON entries.")
    parser.add_argument("--no-rebuild-generated", action="store_true", help="Skip docs-log generated index rebuild after writing.")
    parser.add_argument("--json", action="store_true", help="Print summary as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = repo_root()
        source_path = root / SOURCE_DOC
        if not source_path.exists():
            raise ValueError(f"missing source doc: {SOURCE_DOC}")
        text = source_path.read_text(encoding="utf-8")
        docs_map = docs_by_source(root)
        existing = existing_entry_ids(root)
        used: Counter[str] = Counter()
        records = [build_record(entry, docs_map, used, existing) for entry in split_entries(text)]
        errors: list[str] = []
        for record in records:
            record_errors = validate_record(record)
            if record_errors:
                errors.append(f"{record['id']}: {'; '.join(record_errors)}")
        if errors:
            raise ValueError("\n".join(errors))
        summary = {
            "source": SOURCE_DOC.as_posix(),
            "entry_count": len(records),
            "date_range": [records[-1]["date"], records[0]["date"]] if records else [],
            "domains": sorted({domain for record in records for domain in record["domains"]}),
            "status_counts": dict(sorted(Counter(record["status"] for record in records).items())),
            "type_counts": dict(sorted(Counter(record["type"] for record in records).items())),
            "sample_ids": [record["id"] for record in records[:5]],
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False) if args.json else f"migrated entries: {len(records)}")
        if not args.write:
            print("preview only; pass --write to create entries")
            return 0
        written = write_records(root, records)
        print(f"wrote {len(written)} entries")
        if not args.no_rebuild_generated:
            subprocess.run(
                [sys.executable, "studio/workflows/change-requests/services/docs_logs/build_indexes.py", "--write"],
                cwd=root,
                check=True,
            )
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
