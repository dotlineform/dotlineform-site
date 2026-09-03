#!/usr/bin/env python3
"""Build Docs Viewer search indexes without Ruby."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote

from docs_builder.runtime_bootstrap import (
    apply_projects_base_dir_override,
    apply_repo_local_env,
    projects_base_dir_from_argv,
)

if __name__ == "__main__":
    apply_repo_local_env(projects_base_dir=projects_base_dir_from_argv(sys.argv[1:]))


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
for path in (BUILD_DIR, DOCS_SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_docs import (  # noqa: E402
    FrontMatterSyntaxError,
    HTML_MEDIA_TOKEN_PATTERN,
    MEDIA_TOKEN_PATTERN,
    extract_title,
    front_matter_boolean,
    humanize,
)
from docs_builder.semantic_tokens import replace_semantic_tokens  # noqa: E402
from docs_builder.source import parse_source_text  # noqa: E402
from docs_scope_config import (  # noqa: E402
    DocsScopeConfig,
    DocsSubScopeConfig,
    document_source_path,
    load_docs_scope_configs,
    generated_documents_path,
    generated_search_path,
    resolve_scope_path,
)
from docs_document_location import sub_scope_report_placement  # noqa: E402
from docs_document_identity import is_immutable_doc_id  # noqa: E402
from docs_report_source import (  # noqa: E402
    ReportDescriptor,
    ReportSourceContractRequired,
    project_report_markdown,
)
from docs_source_model import (  # noqa: E402
    load_document_collection_docs_for_config,
    parse_document_report,
    report_source_contract_for_collection,
    validate_publishable_front_matter,
)
from markdown_renderer import extract_markdown_search_fields  # noqa: E402


DEFAULT_SCOPE = "studio"
SEARCH_INDEX_V2_SCHEMA = "docs_viewer_search_index_v2"
SEARCH_V2_STOP_WORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "that", "the", "to", "with",
})
SEARCH_V2_FILE_EXTENSIONS = frozenset({
    "css", "gif", "htm", "html", "jpeg", "jpg", "js", "json", "md",
    "mjs", "pdf", "png", "py", "svg", "ts", "txt", "webp", "yaml", "yml",
})
SEARCH_V2_EXACT_FIELDS = frozenset({"identity", "last_updated"})
SEARCH_V2_CONTENT_FIELDS = frozenset({"heading", "body", "code"})
SEARCH_V2_EXCLUDED_SPANS = re.compile(r"(?:https?://|www\.)\S+|(?:[/\\][^\s]+)+|<[^>]+>", re.IGNORECASE)
SEARCH_V2_TOKEN = re.compile(r"[^\W_]+(?:[._-][^\W_]+)*", re.UNICODE)
SEARCH_V2_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
SEARCH_V2_CONTENT_HASH = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SearchDocRecord:
    doc_id: str
    title: str
    last_updated: str
    parent_id: str
    viewer_url: str
    summary: str = ""
    body_markdown: str = ""
    report: ReportDescriptor | None = None
    sub_scope: str = ""
    report_doc_id: str = ""
    collection_title: str = ""


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize(value: Any) -> str:
    return normalize_text(value).lower()


def boolean_field(row: dict[str, Any], key: str, default: bool) -> bool:
    if key not in row:
        return default
    value = row[key]
    if value is True or value is False:
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


def compact_join(*parts: Any) -> str:
    return " • ".join(part for part in (normalize_text(value) for value in parts) if part)


def normalize_search_value_v2(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).lower()
    return re.sub(r"\s+", " ", normalized).strip()


def tokenize_search_value_v2(value: Any) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    text = SEARCH_V2_EXCLUDED_SPANS.sub(" ", unicodedata.normalize("NFKC", str(value or "")))
    for token in SEARCH_V2_TOKEN.findall(text):
        normalized_token = normalize_search_value_v2(token)
        if is_immutable_doc_id(normalized_token) or SEARCH_V2_CONTENT_HASH.fullmatch(normalized_token):
            continue
        derived = [normalized_token]
        segments = re.split(r"[._-]+", token)
        has_file_extension = "." in token and normalize_search_value_v2(segments[-1]) in SEARCH_V2_FILE_EXTENSIONS
        for index, segment in enumerate(segments):
            if has_file_extension and index == len(segments) - 1:
                continue
            derived.extend(SEARCH_V2_CAMEL_BOUNDARY.sub(" ", segment).split())
        for candidate in derived:
            term = normalize_search_value_v2(candidate).strip("._-")
            useful = (
                len(term) >= 2
                and term not in SEARCH_V2_STOP_WORDS
                and any(character.isalpha() for character in term)
                and not is_immutable_doc_id(term)
                and not SEARCH_V2_CONTENT_HASH.fullmatch(term)
            )
            if useful and term not in seen:
                seen.add(term)
                terms.append(term)
    return terms


def search_field_values_v2(document: Mapping[str, Any], field: str) -> list[Any]:
    value = document.get("id") if field == "identity" else document.get(field)
    return list(value) if isinstance(value, (list, tuple)) else [value]


def build_search_index_v2(
    *,
    scope: str,
    documents: list[Mapping[str, Any]],
    search_fields: tuple[str, ...],
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    doc_fields = (
        "id",
        "title",
        "href",
        "last_updated",
        "parent_id",
        "parent_title",
        "display_meta",
        "sub_scope",
        "report_doc_id",
        "collection_title",
    )
    ordered_documents = sorted(
        documents,
        key=lambda document: (
            normalize(document.get("id")),
            normalize(document.get("sub_scope")),
            normalize(document.get("report_doc_id")),
        ),
    )
    docs = [
        {
            key: normalize_text(document.get(key))
            for key in doc_fields
            if normalize_text(document.get(key))
        }
        for document in ordered_documents
    ]
    document_targets = [
        (
            normalize_text(document.get("sub_scope")),
            normalize_text(document.get("id")),
        )
        for document in docs
    ]
    if (
        any(not doc_id for _sub_scope, doc_id in document_targets)
        or len(document_targets) != len(set(document_targets))
    ):
        raise ValueError("v2 search documents require unique non-empty exact targets")
    if any(not normalize_text(document.get("title")) or not normalize_text(document.get("href")) for document in docs):
        raise ValueError("v2 search documents require title and href")
    for document in docs:
        sub_scope = normalize_text(document.get("sub_scope"))
        if sub_scope and (
            not normalize_text(document.get("report_doc_id"))
            or not normalize_text(document.get("collection_title"))
        ):
            raise ValueError(
                "v2 sub-scope search documents require report_doc_id and collection_title"
            )

    postings: dict[str, dict[str, set[int]]] = {}
    for position, document in enumerate(ordered_documents):
        for field in search_fields:
            for value in search_field_values_v2(document, field):
                terms = (
                    [normalize_search_value_v2(value)]
                    if field in SEARCH_V2_EXACT_FIELDS
                    else tokenize_search_value_v2(value)
                )
                for term in set(filter(None, terms)):
                    postings.setdefault(term, {}).setdefault(field, set()).add(position)

    terms = {
        term: {
            field: sorted(postings[term][field])
            for field in search_fields
            if field in postings[term]
        }
        for term in sorted(postings)
    }
    version_payload = {
        "schema": SEARCH_INDEX_V2_SCHEMA,
        "scope": normalize(scope),
        "fields": list(search_fields),
        "docs": docs,
        "terms": terms,
    }
    return {
        "header": {
            "schema": SEARCH_INDEX_V2_SCHEMA,
            "scope": normalize(scope),
            "version": f"blake2b-{blake2b_payload_hash(version_payload)}",
            "generated_at_utc": generated_at_utc or utc_timestamp(),
            "count": len(docs),
        },
        "fields": list(search_fields),
        "docs": docs,
        "terms": terms,
    }


def json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


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
        self.content_search_enabled = bool(
            SEARCH_V2_CONTENT_FIELDS.intersection(self.scope_config.search_fields)
        )
        self.report_source_contract = None
        self.output_path = self.resolve_path(output_path or generated_search_path(self.scope_config))

    def run(
        self,
        *,
        write: bool,
        force: bool,
    ) -> dict[str, Any]:
        payload = self.build_docs_v2_payload()
        return self.write_payload(payload, write=write, force=force)

    def docs_scope_config(self, scope: str) -> DocsScopeConfig:
        try:
            configs = load_docs_scope_configs(
                self.repo_root,
                scope_ids=(scope,),
            )
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
        return resolve_scope_path(self.repo_root, Path(path))

    def load_source_docs(self) -> list[SearchDocRecord]:
        source_dir = resolve_scope_path(self.repo_root, document_source_path(self.scope_config))
        paths = sorted(source_dir.glob("**/*.md"))
        nested_paths = [path for path in paths if path.parent != source_dir]
        if nested_paths:
            nested = ", ".join(path.relative_to(source_dir).as_posix() for path in nested_paths)
            raise SystemExit(f"Nested markdown docs are not supported under {source_dir}; move these files to the scope root: {nested}")

        raw_records: list[dict[str, Any]] = []
        for path in paths:
            source_text = path.read_text(encoding="utf-8")
            source_name = path.relative_to(source_dir).as_posix()
            try:
                front_matter, body_markdown = parse_source_text(
                    source_text,
                    source_name=source_name,
                )
            except FrontMatterSyntaxError as exc:
                raise SystemExit(str(exc)) from exc
            stem = path.stem
            doc_id = normalize_text(front_matter.get("doc_id") or stem)
            title = normalize_text(front_matter.get("title") or extract_title(body_markdown) or humanize(stem))
            if not doc_id or not title:
                continue
            try:
                validate_publishable_front_matter(
                    front_matter,
                    collection_config=self.scope_config,
                    source_name=source_name,
                )
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
            try:
                try:
                    report = parse_document_report(
                        source_text,
                        front_matter,
                        body_markdown,
                        source_name=source_name,
                        contract=self.report_source_contract,
                    )
                except ReportSourceContractRequired:
                    self.report_source_contract = report_source_contract_for_collection(
                        self.repo_root,
                        self.scope_config,
                        self.scope_config,
                    )
                    report = parse_document_report(
                        source_text,
                        front_matter,
                        body_markdown,
                        source_name=source_name,
                        contract=self.report_source_contract,
                    )
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
            raw_records.append(
                {
                    "doc_id": doc_id,
                    "title": title,
                    "summary": normalize_text(front_matter.get("summary")),
                    "last_updated": normalize_text(front_matter.get("last_updated")),
                    "parent_id": normalize_text(front_matter.get("parent_id") if "parent_id" in front_matter else ""),
                    "viewer_url": self.viewer_url_for(doc_id),
                    "publishable": front_matter_boolean(front_matter, "publishable", True),
                    "body_markdown": body_markdown,
                    "report": report,
                }
            )
        return self.search_records_from_source_rows(raw_records)

    def viewer_url_for(self, doc_id: str) -> str:
        pairs: list[str] = []
        if self.scope_config.include_scope_param and self.scope:
            pairs.append(f"scope={quote(self.scope)}")
        pairs.append(f"doc={quote(str(doc_id))}")
        return f"{self.scope_config.viewer_base_url}?{'&'.join(pairs)}"

    def search_records_from_source_rows(self, rows: list[dict[str, Any]]) -> list[SearchDocRecord]:
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
                    summary=normalize_text(row.get("summary")),
                    body_markdown=str(row.get("body_markdown") or ""),
                    report=row.get("report") if isinstance(row.get("report"), ReportDescriptor) else None,
                )
            )
        return records

    def hidden_doc_ids(self, docs: list[Any]) -> set[str]:
        roots = [
            normalize_text(value)
            for value in self.scope_config.manage_only_tree_root_ids
        ]
        roots.extend(
            normalize_text(row.get("doc_id"))
            for row in docs
            if isinstance(row, dict) and not boolean_field(row, "publishable", True)
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

    def build_docs_v2_payload(
        self,
        *,
        generated_at_utc: str | None = None,
    ) -> dict[str, Any]:
        docs = self.load_source_docs()
        title_by_id = {doc.doc_id: doc.title for doc in docs}
        combined_docs = [*docs, *self.load_sub_scope_docs(docs)]
        records: list[dict[str, Any]] = []
        for doc in combined_docs:
            parent_title = "" if not doc.parent_id else normalize_text(title_by_id.get(doc.parent_id))
            record: dict[str, Any] = {
                "id": doc.doc_id,
                "title": doc.title,
                "summary": doc.summary,
                "href": doc.viewer_url,
                "last_updated": doc.last_updated,
                "parent_id": doc.parent_id,
                "parent_title": parent_title,
                "display_meta": compact_join(
                    doc.last_updated,
                    doc.collection_title or parent_title,
                ),
            }
            if doc.sub_scope:
                record.update(
                    {
                        "sub_scope": doc.sub_scope,
                        "report_doc_id": doc.report_doc_id,
                        "collection_title": doc.collection_title,
                    }
                )
            if self.content_search_enabled:
                fields = extract_markdown_search_fields(
                    self.searchable_markdown(doc),
                    title=doc.title,
                )
                record.update(
                    {
                        "heading": fields.headings,
                        "body": fields.body,
                        "code": fields.code,
                    }
                )
            records.append(record)
        return build_search_index_v2(
            scope=self.scope,
            documents=records,
            search_fields=self.scope_config.search_fields,
            generated_at_utc=generated_at_utc,
        )

    def load_sub_scope_docs(
        self,
        parent_docs: list[SearchDocRecord],
    ) -> list[SearchDocRecord]:
        """Load the manifest-owned child corpus for every exact visible placement."""

        eligible_parent_doc_ids = {document.doc_id for document in parent_docs}
        records: list[SearchDocRecord] = []
        for sub_scope in sorted(
            self.scope_config.sub_scopes,
            key=lambda item: item.sub_scope,
        ):
            try:
                _config, _sub_scope, report_doc_id = sub_scope_report_placement(
                    self.repo_root,
                    self.scope,
                    sub_scope.sub_scope,
                    eligible_parent_doc_ids=eligible_parent_doc_ids,
                    require_public=False,
                )
                records.extend(
                    self.load_sub_scope_collection_docs(
                        sub_scope,
                        report_doc_id=report_doc_id,
                    )
                )
            except (OSError, ValueError) as exc:
                raise SystemExit(str(exc)) from exc
        return records

    def load_sub_scope_collection_docs(
        self,
        sub_scope: DocsSubScopeConfig,
        *,
        report_doc_id: str,
    ) -> list[SearchDocRecord]:
        output_root = resolve_scope_path(
            self.repo_root,
            generated_documents_path(sub_scope),
        )
        manifest_path = output_root / "manage-manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Docs Viewer search requires readable sub-scope manifest: {manifest_path}"
            ) from exc
        manifest_rows = manifest.get("docs") if isinstance(manifest, dict) else None
        if not isinstance(manifest_rows, list):
            raise ValueError(
                f"Docs Viewer search sub-scope manifest docs must be an array: {manifest_path}"
            )

        source_docs = load_document_collection_docs_for_config(
            self.repo_root,
            self.scope_config,
            sub_scope,
        )
        source_by_id = {document.doc_id: document for document in source_docs}
        seen_doc_ids: set[str] = set()
        collection_title = normalize_text(sub_scope.title)
        records: list[SearchDocRecord] = []
        for index, raw_row in enumerate(manifest_rows):
            field = f"{manifest_path}.docs[{index}]"
            if not isinstance(raw_row, dict):
                raise ValueError(f"{field} must be an object")
            doc_id = normalize_text(raw_row.get("doc_id"))
            title = normalize_text(raw_row.get("title"))
            if not is_immutable_doc_id(doc_id):
                raise ValueError(f"{field}.doc_id must use immutable document identity")
            if not title:
                raise ValueError(f"{field}.title must not be empty")
            if doc_id in seen_doc_ids:
                raise ValueError(f"{manifest_path} contains duplicate doc_id {doc_id!r}")
            seen_doc_ids.add(doc_id)

            source_doc = source_by_id.get(doc_id)
            if source_doc is None:
                raise ValueError(
                    f"sub-scope manifest document {self.scope}/{sub_scope.sub_scope}/{doc_id} "
                    "has no source document"
                )
            by_id_path = output_root / "by-id" / f"{doc_id}.json"
            try:
                by_id = json.loads(by_id_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"Docs Viewer search requires readable sub-scope by-id payload: {by_id_path}"
                ) from exc
            if not isinstance(by_id, dict):
                raise ValueError(f"sub-scope by-id payload must be an object: {by_id_path}")

            expected_url = f"{self.viewer_url_for(report_doc_id)}&subdoc={quote(doc_id)}"
            source_title = normalize_text(source_doc.title)
            by_id_title = normalize_text(by_id.get("title"))
            if title != source_title or title != by_id_title:
                raise ValueError(
                    f"sub-scope manifest, source, and by-id titles must match for "
                    f"{self.scope}/{sub_scope.sub_scope}/{doc_id}"
                )
            if (
                normalize_text(by_id.get("doc_id")) != doc_id
                or normalize_text(by_id.get("viewer_url")) != expected_url
            ):
                raise ValueError(
                    f"sub-scope by-id identity or viewer_url is stale for "
                    f"{self.scope}/{sub_scope.sub_scope}/{doc_id}"
                )
            last_updated = normalize_text(by_id.get("last_updated"))
            if last_updated != normalize_text(source_doc.front_matter.get("last_updated")):
                raise ValueError(
                    f"sub-scope source and by-id last_updated must match for "
                    f"{self.scope}/{sub_scope.sub_scope}/{doc_id}"
                )
            records.append(
                SearchDocRecord(
                    doc_id=doc_id,
                    title=title,
                    last_updated=last_updated,
                    parent_id="",
                    viewer_url=expected_url,
                    summary=normalize_text(source_doc.front_matter.get("summary")),
                    body_markdown=source_doc.body,
                    report=source_doc.report,
                    sub_scope=sub_scope.sub_scope,
                    report_doc_id=report_doc_id,
                    collection_title=collection_title,
                )
            )
        return records

    def searchable_markdown(self, doc: SearchDocRecord) -> str:
        markdown = project_report_markdown(
            doc.body_markdown,
            doc.report,
            include_host=False,
        )
        markdown = replace_semantic_tokens(
            markdown,
            registry=None,
            replacer=lambda token: html.escape(token.title),
        )
        markdown = HTML_MEDIA_TOKEN_PATTERN.sub("", markdown)
        return MEDIA_TOKEN_PATTERN.sub("", markdown)

    def write_payload(
        self,
        payload: dict[str, Any],
        *,
        write: bool,
        force: bool,
    ) -> dict[str, Any]:
        count = payload.get("header", {}).get("count")
        relative_output_path = relative_path(self.output_path, self.repo_root)
        existing_version = self.extract_existing_version(self.output_path)
        payload_version = payload.get("header", {}).get("version")
        if existing_version == payload_version and not force:
            self.print_skip_message(relative_output_path, write)
            return payload
        if not write:
            self.print_dry_run_message(relative_output_path, count)
            return payload
        if self.output_path is None:
            raise SystemExit("Generated search index output path is required")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json_text(payload), encoding="utf-8")
        self.print_write_message(relative_output_path, count)
        return payload

    def print_skip_message(self, relative_output_path: str, write: bool) -> None:
        if write:
            print(f"Search index JSON done. Wrote: 0. Skipped: 1. Path: {relative_output_path}")
        else:
            print(f"Search index JSON done. Would write: 0. Skipped: 1. Path: {relative_output_path}")

    def print_dry_run_message(self, relative_output_path: str, count: int) -> None:
        print(f"Dry run: {count} {self.scope} search docs")
        print(f"Would write: {relative_output_path}")

    def print_write_message(self, relative_output_path: str, count: int) -> None:
        print(f"Wrote {relative_output_path} with {count} {self.scope} search docs")

    def extract_existing_version(self, path: Path | None) -> str | None:
        if not path or not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        header = payload.get("header") if isinstance(payload, dict) else None
        return normalize_text(header.get("version")) if isinstance(header, dict) else None

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer search indexes.")
    parser.add_argument("--scope", default=DEFAULT_SCOPE, help="Docs Viewer search scope to build.")
    parser.add_argument(
        "--projects-base-dir",
        help="Override DOTLINEFORM_PROJECTS_BASE_DIR for this build after loading .env.local.",
    )
    parser.add_argument("--output", help="Generated search index output path.")
    parser.add_argument("--only-records", help="Catalogue-only targeted search records.")
    parser.add_argument("--write", action="store_true", help="Persist generated files; default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Write even when the content version matches.")
    args = parser.parse_args(argv)
    if args.only_records is not None:
        raise SystemExit("Docs Viewer search does not support --only-records")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.projects_base_dir:
        apply_projects_base_dir_override(args.projects_base_dir)
    repo_root = Path.cwd().resolve()
    builder = DocsViewerSearchDataBuilder(
        repo_root=repo_root,
        scope=args.scope,
        output_path=Path(args.output) if args.output else None,
    )
    builder.run(
        write=args.write,
        force=args.force,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
