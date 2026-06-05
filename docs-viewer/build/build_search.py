#!/usr/bin/env python3
"""Build Docs Viewer search indexes without Ruby."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (BUILD_DIR, DOCS_SERVICES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_docs import (  # noqa: E402
    FrontMatterSyntaxError,
    extract_title,
    front_matter_boolean,
    humanize,
    parse_source,
)
from docs_scope_config import DocsScopeConfig, load_docs_scope_configs  # noqa: E402


DEFAULT_SCOPE = "studio"


@dataclass(frozen=True)
class SearchDocRecord:
    doc_id: str
    title: str
    last_updated: str
    parent_id: str
    viewer_url: str
    viewable: bool


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize(value: Any) -> str:
    return normalize_text(value).lower()


def normalize_search_text(value: Any) -> str:
    return re.sub(r"\s+", " ", normalize_text(value).lower()).strip()


def normalize_target_doc_ids(values: list[str] | tuple[str, ...] | None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values or []:
        for item in normalize_text(value).split(","):
            doc_id = normalize_text(item)
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                result.append(doc_id)
    return result


def boolean_field(row: dict[str, Any], key: str, default: bool) -> bool:
    if key not in row:
        return default
    value = row[key]
    if value is True or value is False:
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


def compact_join(*parts: Any) -> str:
    return " • ".join(part for part in (normalize_text(value) for value in parts) if part)


def build_search_tokens(*values: Any) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for value in values:
        items = value if isinstance(value, list) else [value]
        for item in items:
            normalized = normalize_search_text(item)
            if not normalized:
                continue
            candidates = [normalized, *re.sub(r"[^a-z0-9]+", " ", normalized).split()]
            for candidate in candidates:
                token = normalize_search_text(candidate)
                if token and token not in seen:
                    seen.add(token)
                    tokens.append(token)
    return tokens


def json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse JSON: {relative_path(path, REPO_ROOT)} ({exc})") from exc


def canonicalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonicalize_for_hash(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonicalize_for_hash(item) for item in value]
    return value


def blake2b_payload_hash(payload: Any) -> str:
    canonical = json.dumps(canonicalize_for_hash(payload), ensure_ascii=False, separators=(",", ":"))
    return hashlib.blake2b(canonical.encode("utf-8"), digest_size=64).digest()[:16].hex()


def relative_path(path: Path | None, repo_root: Path) -> str:
    if path is None:
        return "(unknown path)"
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


class DocsViewerSearchDataBuilder:
    def __init__(
        self,
        *,
        repo_root: Path,
        scope: str,
        output_path: Path | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.scope = normalize(scope)
        self.scope_config = self.docs_scope_config(self.scope)
        self.schema = f"search_index_{self.scope}_v1"
        self.output_path = self.resolve_path(output_path or self.scope_config.search_output)

    def run(
        self,
        *,
        write: bool,
        force: bool,
        only_doc_ids: list[str] | None = None,
        remove_missing: bool = False,
    ) -> dict[str, Any]:
        target_doc_ids = normalize_target_doc_ids(only_doc_ids)
        self.validate_targeted_options(target_doc_ids, remove_missing)
        payload, diagnostics = self.build_docs_payload(target_doc_ids=target_doc_ids, remove_missing=remove_missing)
        return self.write_payload(payload, write=write, force=force, diagnostics=diagnostics)

    def docs_scope_config(self, scope: str) -> DocsScopeConfig:
        try:
            configs = load_docs_scope_configs(self.repo_root)
        except ValueError as exc:
            raise SystemExit(f"Invalid Docs Viewer scope config: {exc}") from exc
        config = configs.get(scope)
        if config:
            return config
        available = ", ".join(sorted(configs))
        raise SystemExit(f"Unsupported docs search scope: {scope}. Current Docs Viewer scopes: {available}")

    def resolve_path(self, path: Path | str | None) -> Path | None:
        if path is None:
            return None
        return (self.repo_root / Path(path)).resolve()

    def build_docs_payload(
        self,
        *,
        target_doc_ids: list[str],
        remove_missing: bool,
    ) -> tuple[dict[str, Any], dict[str, int] | None]:
        docs = self.load_source_docs()
        entries = self.build_docs_entries(docs)
        if not target_doc_ids:
            return self.build_docs_search_payload(entries), None
        return self.build_targeted_docs_payload(entries, target_doc_ids, remove_missing)

    def load_source_docs(self) -> list[SearchDocRecord]:
        source_dir = (self.repo_root / self.scope_config.source).resolve()
        paths = sorted(source_dir.glob("**/*.md"))
        nested_paths = [path for path in paths if path.parent != source_dir]
        if nested_paths and not self.scope_config.allow_nested_source:
            nested = ", ".join(path.relative_to(source_dir).as_posix() for path in nested_paths)
            raise SystemExit(f"Nested markdown docs are not supported under {source_dir}; move these files to the scope root: {nested}")

        raw_records: list[dict[str, Any]] = []
        for path in paths:
            try:
                front_matter, body_markdown = parse_source(path)
            except FrontMatterSyntaxError as exc:
                raise SystemExit(str(exc)) from exc
            stem = path.stem
            doc_id = normalize_text(front_matter.get("doc_id") or stem)
            title = normalize_text(front_matter.get("title") or extract_title(body_markdown) or humanize(stem))
            if not doc_id or not title:
                continue
            raw_records.append(
                {
                    "doc_id": doc_id,
                    "title": title,
                    "last_updated": normalize_text(front_matter.get("last_updated")),
                    "parent_id": normalize_text(front_matter.get("parent_id") if "parent_id" in front_matter else ""),
                    "viewer_url": self.viewer_url_for(doc_id),
                    "viewable": front_matter_boolean(front_matter, "viewable", True),
                }
            )
        return self.search_records_from_source_rows(self.ordered_source_rows(raw_records))

    def viewer_url_for(self, doc_id: str) -> str:
        pairs: list[str] = []
        if self.scope_config.include_scope_param and self.scope:
            pairs.append(f"scope={quote(self.scope)}")
        pairs.append(f"doc={quote(str(doc_id))}")
        return f"{self.scope_config.viewer_base_url}?{'&'.join(pairs)}"

    def search_records_from_source_rows(self, rows: list[dict[str, Any]]) -> list[SearchDocRecord]:
        hidden_ids = self.hidden_doc_ids(rows)
        all_doc_ids = {normalize_text(row.get("doc_id")) for row in rows if isinstance(row, dict)}
        records: list[SearchDocRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            doc_id = normalize_text(row.get("doc_id"))
            title = normalize_text(row.get("title"))
            viewer_url = normalize_text(row.get("viewer_url"))
            if not doc_id or not title or not viewer_url:
                continue
            if doc_id in hidden_ids or not boolean_field(row, "viewable", True):
                continue
            parent_id = normalize_text(row.get("parent_id"))
            if parent_id and parent_id not in all_doc_ids:
                parent_id = ""
            records.append(
                SearchDocRecord(
                    doc_id=doc_id,
                    title=title,
                    last_updated=normalize_text(row.get("last_updated")),
                    parent_id=parent_id,
                    viewer_url=viewer_url,
                    viewable=True,
                )
            )
        return records

    def ordered_source_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_parent: dict[str, list[dict[str, Any]]] = {}
        ids = {normalize_text(row.get("doc_id")) for row in rows if isinstance(row, dict)}
        for row in rows:
            parent_id = normalize_text(row.get("parent_id"))
            if parent_id not in ids:
                parent_id = ""
            by_parent.setdefault(parent_id, []).append(row)
        for children in by_parent.values():
            children.sort(key=lambda row: (normalize(row.get("title")), normalize(row.get("doc_id"))))
        ordered: list[dict[str, Any]] = []
        seen: set[str] = set()

        def append_children(parent_id: str) -> None:
            for child in by_parent.get(parent_id, []):
                doc_id = normalize_text(child.get("doc_id"))
                if not doc_id or doc_id in seen:
                    continue
                seen.add(doc_id)
                ordered.append(child)
                append_children(doc_id)

        append_children("")
        for row in sorted(rows, key=lambda row: (normalize(row.get("title")), normalize(row.get("doc_id")))):
            doc_id = normalize_text(row.get("doc_id"))
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                ordered.append(row)
        return ordered

    def hidden_doc_ids(self, docs: list[Any]) -> set[str]:
        roots = [
            normalize_text(value)
            for value in self.scope_config.manage_only_tree_root_ids
        ]
        roots.extend(
            normalize_text(row.get("doc_id"))
            for row in docs
            if isinstance(row, dict) and not boolean_field(row, "viewable", True)
        )
        roots = [value for value in roots if value]
        if not roots:
            return set()
        by_parent: dict[str, list[str]] = {}
        for row in docs:
            if not isinstance(row, dict):
                continue
            doc_id = normalize_text(row.get("doc_id"))
            parent_id = normalize_text(row.get("parent_id"))
            if doc_id and parent_id:
                by_parent.setdefault(parent_id, []).append(doc_id)
        manage_only = set(roots)
        queue = list(roots)
        while queue:
            current = queue.pop(0)
            for child_id in by_parent.get(current, []):
                if child_id in manage_only:
                    continue
                manage_only.add(child_id)
                queue.append(child_id)
        return manage_only

    def build_docs_entries(self, docs: list[SearchDocRecord]) -> list[dict[str, Any]]:
        title_by_id = {doc.doc_id: doc.title for doc in docs}
        entries: list[dict[str, Any]] = []
        for doc in docs:
            parent_title = "" if not doc.parent_id else normalize_text(title_by_id.get(doc.parent_id))
            display_meta = compact_join(doc.last_updated, parent_title)
            search_terms = build_search_tokens(doc.doc_id, doc.title, parent_title, doc.last_updated)
            entry = {
                "id": doc.doc_id,
                "kind": "doc",
                "title": doc.title,
                "href": doc.viewer_url,
                "last_updated": doc.last_updated,
                "parent_id": doc.parent_id,
                "parent_title": parent_title,
                "display_meta": display_meta,
                "search_terms": search_terms,
                "search_text": " ".join(search_terms),
            }
            entries.append({key: value for key, value in entry.items() if not self.empty_scalar(value)})
        return entries

    def build_targeted_docs_payload(
        self,
        entries: list[dict[str, Any]],
        target_doc_ids: list[str],
        remove_missing: bool,
    ) -> tuple[dict[str, Any], dict[str, int]]:
        existing_payload = self.load_existing_search_payload()
        if not existing_payload or not isinstance(existing_payload.get("entries"), list):
            diagnostics = {"changed": len(entries), "removed": 0, "unchanged": 0, "full_fallback": 1}
            return self.build_docs_search_payload(entries), diagnostics

        existing_entries = existing_payload["entries"]
        entry_by_id = {normalize_text(entry.get("id")): entry for entry in entries}
        order_by_id = {normalize_text(entry.get("id")): index for index, entry in enumerate(entries)}
        existing_by_id: dict[str, dict[str, Any]] = {}
        for entry in existing_entries:
            if not isinstance(entry, dict):
                continue
            entry_id = normalize_text(entry.get("id"))
            if entry_id:
                existing_by_id[entry_id] = entry
        existing_order_by_id = {
            normalize_text(entry.get("id")): index for index, entry in enumerate(existing_entries)
            if isinstance(entry, dict)
        }

        changed = 0
        removed = 0
        unchanged = 0
        for doc_id in target_doc_ids:
            next_entry = entry_by_id.get(doc_id)
            current_entry = existing_by_id.get(doc_id)
            if next_entry is None:
                if not remove_missing:
                    raise SystemExit(
                        f"Targeted docs search update for {self.scope} requires --remove-missing "
                        "when affected ids may be missing or non-viewable"
                    )
                if current_entry is not None:
                    existing_by_id.pop(doc_id, None)
                    removed += 1
                else:
                    unchanged += 1
                continue
            if current_entry == next_entry:
                unchanged += 1
            else:
                existing_by_id[doc_id] = next_entry
                changed += 1

        merged_entries = sorted(
            existing_by_id.values(),
            key=lambda entry: (
                order_by_id.get(normalize_text(entry.get("id")), len(entries) + existing_order_by_id.get(normalize_text(entry.get("id")), 0)),
                existing_order_by_id.get(normalize_text(entry.get("id")), len(existing_entries)),
            ),
        )
        diagnostics = {"changed": changed, "removed": removed, "unchanged": unchanged, "full_fallback": 0}
        return self.build_docs_search_payload(merged_entries), diagnostics

    def build_docs_search_payload(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        version_payload = {"schema": self.schema, "entries": entries}
        version = f"blake2b-{blake2b_payload_hash(version_payload)}"
        return {
            "header": {
                "schema": self.schema,
                "scope": self.scope,
                "version": version,
                "generated_at_utc": utc_timestamp(),
                "count": len(entries),
            },
            "entries": entries,
        }

    def write_payload(
        self,
        payload: dict[str, Any],
        *,
        write: bool,
        force: bool,
        diagnostics: dict[str, int] | None,
    ) -> dict[str, Any]:
        count = payload.get("header", {}).get("count")
        relative_output_path = relative_path(self.output_path, self.repo_root)
        existing_version = self.extract_existing_version(self.output_path)
        payload_version = payload.get("header", {}).get("version")
        targeted_changes = diagnostics is not None and (
            int(diagnostics.get("changed", 0)) > 0 or int(diagnostics.get("removed", 0)) > 0
        )
        if existing_version == payload_version and not force and not targeted_changes:
            self.print_skip_message(relative_output_path, write, diagnostics)
            return payload
        if not write:
            self.print_dry_run_message(relative_output_path, count, diagnostics)
            return payload
        if self.output_path is None:
            raise SystemExit("Generated search index output path is required")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json_text(payload), encoding="utf-8")
        self.print_write_message(relative_output_path, count, diagnostics)
        return payload

    def print_skip_message(self, relative_output_path: str, write: bool, diagnostics: dict[str, int] | None) -> None:
        if diagnostics:
            verb = "Wrote" if write else "Would write"
            print(
                "Targeted search index JSON done. "
                f"{verb}: 0. Skipped: 1. Changed: {diagnostics['changed']}. "
                f"Removed: {diagnostics['removed']}. Unchanged: {diagnostics['unchanged']}. "
                f"Full fallback: {diagnostics['full_fallback']}. Path: {relative_output_path}"
            )
            return
        if write:
            print(f"Search index JSON done. Wrote: 0. Skipped: 1. Path: {relative_output_path}")
        else:
            print(f"Search index JSON done. Would write: 0. Skipped: 1. Path: {relative_output_path}")

    def print_dry_run_message(self, relative_output_path: str, count: int, diagnostics: dict[str, int] | None) -> None:
        if diagnostics:
            print(f"Targeted dry run: {count} {self.scope} search entries")
            print(
                f"Would write: 1. Skipped: 0. Changed: {diagnostics['changed']}. "
                f"Removed: {diagnostics['removed']}. Unchanged: {diagnostics['unchanged']}. "
                f"Full fallback: {diagnostics['full_fallback']}. Path: {relative_output_path}"
            )
            return
        print(f"Dry run: {count} {self.scope} search entries")
        print(f"Would write: {relative_output_path}")

    def print_write_message(self, relative_output_path: str, count: int, diagnostics: dict[str, int] | None) -> None:
        if diagnostics:
            print(
                "Targeted search index JSON done. "
                f"Wrote: 1. Skipped: 0. Changed: {diagnostics['changed']}. "
                f"Removed: {diagnostics['removed']}. Unchanged: {diagnostics['unchanged']}. "
                f"Full fallback: {diagnostics['full_fallback']}. Path: {relative_output_path}"
            )
            return
        print(f"Wrote {relative_output_path} with {count} {self.scope} search entries")

    def extract_existing_version(self, path: Path | None) -> str | None:
        if not path or not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        header = payload.get("header") if isinstance(payload, dict) else None
        return normalize_text(header.get("version")) if isinstance(header, dict) else None

    def load_existing_search_payload(self) -> dict[str, Any] | None:
        if not self.output_path or not self.output_path.exists():
            return None
        try:
            payload = json.loads(self.output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def validate_targeted_options(self, target_doc_ids: list[str], remove_missing: bool) -> None:
        if target_doc_ids or remove_missing:
            if not target_doc_ids:
                raise SystemExit("Targeted docs search updates require at least one doc id")

    def empty_scalar(self, value: Any) -> bool:
        return value is None or (hasattr(value, "__len__") and len(value) == 0)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer search indexes.")
    parser.add_argument("--scope", default=DEFAULT_SCOPE, help="Docs Viewer search scope to build.")
    parser.add_argument("--source-index", help=argparse.SUPPRESS)
    parser.add_argument("--output", help="Generated search index output path.")
    parser.add_argument("--only-doc-ids", action="append", default=[], help="Comma-separated doc ids for targeted docs-domain search updates.")
    parser.add_argument("--only-records", help="Catalogue-only targeted search records.")
    parser.add_argument("--remove-missing", action="store_true", help="Allow targeted docs-domain updates to remove missing or non-viewable ids.")
    parser.add_argument("--write", action="store_true", help="Persist generated files; default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Write even when the content version matches.")
    args = parser.parse_args(argv)
    if args.source_index is not None:
        raise SystemExit("Docs Viewer search no longer supports --source-index; source metadata comes from the configured docs source root")
    if args.only_records is not None:
        raise SystemExit("Docs Viewer search does not support --only-records")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path.cwd().resolve()
    builder = DocsViewerSearchDataBuilder(
        repo_root=repo_root,
        scope=args.scope,
        output_path=Path(args.output) if args.output else None,
    )
    builder.run(
        write=args.write,
        force=args.force,
        only_doc_ids=args.only_doc_ids,
        remove_missing=args.remove_missing,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
