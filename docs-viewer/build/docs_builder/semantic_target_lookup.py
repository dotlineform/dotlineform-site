from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from .common import load_docs_scope_configs, published_documents_path, read_text, write_text
from .semantic_registry import (
    SemanticReferenceKind,
    load_semantic_reference_registry,
    normalize_semantic_reference_id,
)


SEMANTIC_TARGET_LOOKUP_SCHEMA_VERSION = "docs_semantic_reference_target_lookup_v1"
DEFAULT_SEMANTIC_TARGET_LOOKUP_PATH = Path("docs-viewer/published/semantic-references/target-lookup.json")

CATALOGUE_KIND_SOURCES = {
    "work": {
        "filename": "works.json",
        "root_key": "works",
        "id_field": "work_id",
    },
    "series": {
        "filename": "series.json",
        "root_key": "series",
        "id_field": "series_id",
    },
}

DOCS_SCOPE_KIND_SOURCES = {
    "moment": {
        "scope_id": "moments",
    },
}


def compact_json_text(payload: Any) -> str:
    targets = payload.get("targets") if isinstance(payload, dict) else None
    if not isinstance(targets, list):
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    lines = [
        "{",
        f'  "schema_version": {json.dumps(payload.get("schema_version"), ensure_ascii=False)},',
        '  "targets": [',
    ]
    for index, target in enumerate(targets):
        suffix = "," if index < len(targets) - 1 else ""
        lines.append(f"    {json.dumps(target, ensure_ascii=False, separators=(',', ':'))}{suffix}")
    lines.extend(["  ]", "}"])
    return "\n".join(lines) + "\n"


def normalize_lookup_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def json_rows(payload: Any, root_key: str) -> list[dict[str, Any]]:
    records = payload.get(root_key) if isinstance(payload, dict) else None
    rows = records.values() if isinstance(records, dict) else records if isinstance(records, list) else []
    return [dict(row) for row in rows if isinstance(row, dict)]


def docs_index_rows(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def collect(records: Any) -> None:
        if not isinstance(records, list):
            return
        for record in records:
            if not isinstance(record, dict):
                continue
            rows.append(dict(record))
            collect(record.get("children"))

    if isinstance(payload, dict):
        collect(payload.get("docs"))
    return rows


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def is_published(record: dict[str, Any]) -> bool:
    return str(record.get("status") or "").strip().lower() == "published"


def display_date(record: dict[str, Any]) -> str:
    for field in ("year_display", "date_display", "year", "date"):
        value = str(record.get(field) or "").strip()
        if value:
            return value
    return ""


def series_titles_by_id(series_rows: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in series_rows:
        series_id = str(row.get("series_id") or "").strip()
        title = str(row.get("title") or "").strip()
        if series_id and title:
            out[series_id] = title
    return out


def first_series_title(record: dict[str, Any], series_titles: dict[str, str]) -> str:
    series_ids = record.get("series_ids")
    if not isinstance(series_ids, list):
        return ""
    for raw_id in series_ids:
        series_id = str(raw_id or "").strip()
        title = series_titles.get(series_id)
        if title:
            return title
    return ""


def target_meta(kind: str, record: dict[str, Any], *, series_titles: dict[str, str]) -> list[str]:
    meta: list[str] = []
    date_value = display_date(record)
    if date_value:
        meta.append(date_value)
    if kind == "work":
        series_title = first_series_title(record, series_titles)
        if series_title and series_title not in meta:
            meta.append(series_title)
    return meta


def docs_scope_target_meta(payload: dict[str, Any]) -> list[str]:
    meta: list[str] = []
    date_value = display_date(payload)
    if date_value:
        meta.append(date_value)
    return meta


def target_row(
    kind: SemanticReferenceKind,
    record: dict[str, Any],
    source: dict[str, Any],
    *,
    series_titles: dict[str, str],
) -> dict[str, Any] | None:
    if not is_published(record):
        return None
    id_field = str(source["id_field"])
    normalized_id = normalize_semantic_reference_id(str(record.get(id_field) or ""), kind.id)
    title = str(record.get("title") or "").strip()
    if not normalized_id or not title:
        return None
    return {
        "kind": kind.kind,
        "id": normalized_id,
        "title": title,
        "meta": target_meta(kind.kind, record, series_titles=series_titles),
    }


def docs_scope_target_row(
    kind: SemanticReferenceKind,
    index_row: dict[str, Any],
    source: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any] | None:
    non_loadable = source.get("non_loadable_doc_ids")
    if isinstance(non_loadable, set) and index_row.get("doc_id") in non_loadable:
        return None
    doc_id = str(index_row.get("doc_id") or "").strip()
    normalized_id = normalize_semantic_reference_id(doc_id, kind.id)
    title = str(index_row.get("title") or "").strip()
    if not normalized_id or not title:
        return None
    payload = load_json(repo_root / str(source["by_id"]) / f"{normalized_id}.json")
    return {
        "kind": kind.kind,
        "id": normalized_id,
        "title": title,
        "meta": docs_scope_target_meta(payload if isinstance(payload, dict) else {}),
    }


class SemanticTargetLookupBuilder:
    def __init__(self, *, repo_root: Path, output_path: Path | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self.output_path = self.repo_root / (output_path or DEFAULT_SEMANTIC_TARGET_LOOKUP_PATH)

    def run(self, *, write: bool) -> dict[str, Any]:
        payload = self.payload()
        text = compact_json_text(payload)
        changed = read_text(self.output_path) != text
        if write and changed:
            write_text(self.output_path, text)
        diagnostics = {
            "target_count": len(payload["targets"]),
            "changed": changed,
            "wrote": bool(write and changed),
            "output_path": self.output_path.relative_to(self.repo_root).as_posix(),
        }
        return {"payload": payload, "diagnostics": diagnostics}

    def payload(self) -> dict[str, Any]:
        registry = load_semantic_reference_registry(self.repo_root)
        targets: list[dict[str, Any]] = []
        if registry is None:
            return {
                "schema_version": SEMANTIC_TARGET_LOOKUP_SCHEMA_VERSION,
                "targets": [],
            }
        source_root = self.repo_root / "studio" / "data" / "canonical" / "catalogue"
        series_source = CATALOGUE_KIND_SOURCES["series"]
        series_payload = load_json(source_root / str(series_source["filename"]))
        series_titles = series_titles_by_id(json_rows(series_payload, str(series_source["root_key"])))
        for kind in registry.kinds:
            source = CATALOGUE_KIND_SOURCES.get(kind.kind)
            if source is not None:
                payload = load_json(source_root / str(source["filename"]))
                for record in json_rows(payload, str(source["root_key"])):
                    row = target_row(kind, record, source, series_titles=series_titles)
                    if row is not None:
                        targets.append(row)
                continue
            docs_source = DOCS_SCOPE_KIND_SOURCES.get(kind.kind)
            if docs_source is None:
                continue
            scope_config = load_docs_scope_configs(self.repo_root)[str(docs_source["scope_id"])]
            docs_root = published_documents_path(scope_config)
            payload = load_json(self.repo_root / docs_root / "index-tree.json")
            source_with_options = {
                **docs_source,
                "by_id": (docs_root / "by-id").as_posix(),
            }
            viewer_options = payload.get("viewer_options") if isinstance(payload, dict) else {}
            non_loadable_doc_ids = viewer_options.get("non_loadable_doc_ids") if isinstance(viewer_options, dict) else []
            source_with_options["non_loadable_doc_ids"] = set(non_loadable_doc_ids or [])
            for record in docs_index_rows(payload):
                row = docs_scope_target_row(kind, record, source_with_options, repo_root=self.repo_root)
                if row is not None:
                    targets.append(row)
        targets.sort(
            key=lambda row: (
                registry.kind(row["kind"]).order if registry.kind(row["kind"]) else 999,
                normalize_lookup_text(row["title"]),
                row["id"],
            )
        )
        return {
            "schema_version": SEMANTIC_TARGET_LOOKUP_SCHEMA_VERSION,
            "targets": targets,
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer semantic-reference target lookup data.")
    parser.add_argument("--output", help="Override semantic target lookup output path.")
    parser.add_argument("--write", action="store_true", help="Write generated lookup data.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    builder = SemanticTargetLookupBuilder(
        repo_root=Path.cwd(),
        output_path=Path(args.output) if args.output else None,
    )
    result = builder.run(write=args.write)
    diagnostics = result["diagnostics"]
    mode = "write" if args.write else "dry-run"
    verb = "wrote" if diagnostics["wrote"] else "would write" if diagnostics["changed"] else "unchanged"
    print(f"Semantic target lookup ({mode})")
    print(f"  targets total: {diagnostics['target_count']}")
    print(f"  output: {diagnostics['output_path']}")
    print(f"  status: {verb}")
    return 0
