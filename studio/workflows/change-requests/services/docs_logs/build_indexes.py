#!/usr/bin/env python3
"""Build generated indexes from structured docs-log JSON entries."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    from log_entry import validate_record
except ModuleNotFoundError:  # pragma: no cover - package import path for tests
    from docs_logs.log_entry import validate_record


GENERATED_FILES = {
    "search_index": "search-index.json",
}


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


def read_entries(root: Path) -> list[dict[str, Any]]:
    entries_dir = root / "studio/workflows/change-requests" / "logs" / "entries"
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in sorted(entries_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{repo_relative(root, path)}: invalid JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{repo_relative(root, path)}: expected JSON object")
        errors = validate_record(record)
        if errors:
            raise ValueError(f"{repo_relative(root, path)}: {'; '.join(errors)}")
        entry_id = record["id"]
        if path.stem != entry_id:
            raise ValueError(f"{repo_relative(root, path)}: filename must match id: {entry_id}")
        if entry_id in seen_ids:
            raise ValueError(f"{repo_relative(root, path)}: duplicate id: {entry_id}")
        seen_ids.add(entry_id)
        records.append(record)
    return sort_records(records)


def sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda record: (record["date"], record["title"], record["id"]), reverse=True)


def entry_summary(record: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "id": record["id"],
        "date": record["date"],
        "title": record["title"],
        "status": record["status"],
        "type": record["type"],
        "domains": record.get("domains", []),
        "subjects": record.get("subjects", []),
        "summary": record["summary"],
    }
    for key in ("effect", "change_request_doc_id", "related_docs", "related_files", "source"):
        if key in record:
            summary[key] = record[key]
    return summary


def generated_meta(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_on": date.today().isoformat(),
        "entry_count": len(records),
    }


def weighted_search_text(record: dict[str, Any]) -> dict[str, str]:
    title_parts = [record["title"], record["date"], *record.get("domains", []), *record.get("subjects", [])]
    trace_parts = [
        *record.get("related_docs", []),
        *record.get("related_files", []),
        record.get("change_request_doc_id", ""),
    ]
    body_parts = [record.get("area", ""), record.get("body", "")]
    return {
        "title": " ".join(part for part in title_parts if part),
        "trace": " ".join(part for part in trace_parts if part),
        "summary": " ".join(part for part in [record.get("summary", ""), record.get("effect", "")] if part),
        "body": " ".join(part for part in body_parts if part),
    }


def build_search_index(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **generated_meta(records),
        "weights": {
            "title": 5,
            "trace": 4,
            "summary": 3,
            "body": 1,
        },
        "entries": [
            {
                **entry_summary(record),
                "search_text": weighted_search_text(record),
            }
            for record in records
        ],
    }


def build_outputs(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "search_index": build_search_index(records),
    }


def unique_list_values(records: list[dict[str, Any]], field: str) -> list[str]:
    values: set[str] = set()
    for record in records:
        raw_values = record.get(field, [])
        if isinstance(raw_values, str):
            raw_values = [raw_values]
        if not isinstance(raw_values, list):
            continue
        values.update(str(value) for value in raw_values if value)
    return sorted(values)


def unique_field_values(records: list[dict[str, Any]], field: str) -> list[str]:
    return sorted(str(record[field]) for record in records if record.get(field))


def write_outputs(root: Path, outputs: dict[str, dict[str, Any]]) -> list[str]:
    generated_dir = root / "studio/workflows/change-requests" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for key, filename in GENERATED_FILES.items():
        path = generated_dir / filename
        path.write_text(json.dumps(outputs[key], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(repo_relative(root, path))
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated index JSON files.")
    parser.add_argument("--json", action="store_true", help="Print build summary as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = repo_root()
        records = read_entries(root)
        outputs = build_outputs(records)
        summary = {
            "entry_count": len(records),
            "generated_files": list(GENERATED_FILES.values()),
            "domains": unique_list_values(records, "domains"),
            "related_docs": len(unique_list_values(records, "related_docs")),
            "related_files": len(unique_list_values(records, "related_files")),
            "change_requests": len(unique_field_values(records, "change_request_doc_id")),
        }
        if args.json:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            print(f"docs-log entries: {summary['entry_count']}")
            print(f"domains: {len(summary['domains'])}")
            print(f"related docs: {summary['related_docs']}")
            print(f"related files: {summary['related_files']}")
            print(f"change requests: {summary['change_requests']}")
        if not args.write:
            print("preview only; pass --write to update generated docs-log indexes")
            return 0
        written = write_outputs(root, outputs)
        print("wrote:")
        for path in written:
            print(f"- {path}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
