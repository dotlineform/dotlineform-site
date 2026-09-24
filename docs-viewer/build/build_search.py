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
    add_workspace_arguments,
    apply_workspace_overrides,
    apply_repo_local_env,
    workspace_overrides_from_argv,
)

if __name__ == "__main__":
    apply_repo_local_env(**workspace_overrides_from_argv(sys.argv[1:]))


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
for path in (BUILD_DIR, DOCS_SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_docs import (  # noqa: E402
    HTML_MEDIA_TOKEN_PATTERN,
    MEDIA_TOKEN_PATTERN,
)
from docs_builder.common import DOCS_INDEX_TREE_SCHEMA_VERSION  # noqa: E402
from docs_builder.semantic_tokens import replace_semantic_tokens  # noqa: E402
from docs_workspace_config import (  # noqa: E402
    DocsCollectionConfig,
    DocsStageConfig,
    load_docs_stage,
    generated_documents_path,
    generated_search_path,
    resolve_workspace_path,
)
from docs_document_identity import is_immutable_doc_id  # noqa: E402
from docs_publication_ignore import read_publication_ignore_ids  # noqa: E402
from docs_report_source import (  # noqa: E402
    ReportDescriptor,
    project_report_markdown,
)
from docs_source_model import (  # noqa: E402
    SourceDoc,
    load_document_collection_docs_for_config,
)
from markdown_renderer import extract_markdown_search_fields  # noqa: E402


SEARCH_INDEX_SCHEMA = "docs_viewer_search_index_v4"
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
    summary: str = ""
    body_markdown: str = ""
    report: ReportDescriptor | None = None
    collection: str = ""
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


def build_search_index(
    *,
    documents: list[Mapping[str, Any]],
    search_fields: tuple[str, ...],
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build one stage-independent document table and its atomic term postings."""
    doc_fields = (
        "id",
        "title",
        "last_updated",
        "parent_id",
        "parent_title",
        "display_meta",
        "collection",
        "report_doc_id",
        "collection_title",
    )
    ordered_documents = sorted(
        documents,
        key=lambda document: (
            normalize(document.get("id")),
            normalize(document.get("collection")),
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
            normalize_text(document.get("collection")),
            normalize_text(document.get("id")),
        )
        for document in docs
    ]
    if (
        any(not doc_id for _collection, doc_id in document_targets)
        or len(document_targets) != len(set(document_targets))
    ):
        raise ValueError("Search documents require unique non-empty exact targets")
    if any(not normalize_text(document.get("title")) for document in docs):
        raise ValueError("Search documents require title")
    for document in docs:
        collection = normalize_text(document.get("collection"))
        if collection and (
            not normalize_text(document.get("report_doc_id"))
            or not normalize_text(document.get("collection_title"))
        ):
            raise ValueError(
                "Collection search documents require report_doc_id and collection_title"
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
        "schema": SEARCH_INDEX_SCHEMA,
        "fields": list(search_fields),
        "docs": docs,
        "terms": terms,
    }
    return {
        "header": {
            "schema": SEARCH_INDEX_SCHEMA,
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
    """Build the Working source corpus; downstream snapshots copy its index.

    Working tree and management metadata select eligible IDs before any content
    reads. Configuration owns collection coverage and exact host placements.
    The index contains document identity and searchable data; readers own routes.
    """

    def __init__(
        self,
        *,
        repo_root: Path,
        output_path: Path | None = None,
        stage: str,
    ) -> None:
        if stage != "working":
            raise ValueError("Search builds require Working; Preview copies the existing index")
        self.repo_root = repo_root.resolve()
        self.config = load_docs_stage(self.repo_root, stage)
        self.content_search_enabled = bool(
            SEARCH_V2_CONTENT_FIELDS.intersection(self.config.search_fields)
        )
        self.output_path = self.resolve_path(output_path or generated_search_path(self.config))

    def run(
        self,
        *,
        write: bool,
        force: bool,
    ) -> dict[str, Any]:
        payload = self.build_docs_v2_payload()
        return self.write_payload(payload, write=write, force=force)

    def resolve_path(self, path: Path | str | None) -> Path | None:
        if path is None:
            return None
        return resolve_workspace_path(self.repo_root, Path(path))

    def read_metadata(self, path: Path) -> dict[str, Any]:
        """Require current Working metadata; never fall back to source discovery."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"Docs Viewer search requires readable Working metadata: {path}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("docs"), list):
            raise ValueError(f"Docs Viewer search metadata docs must be an array: {path}")
        return payload

    def validate_metadata_row(self, row: Any, *, field: str, seen_ids: set[str]) -> str:
        if not isinstance(row, dict):
            raise ValueError(f"{field} must be an object")
        doc_id = row.get("doc_id")
        if not isinstance(doc_id, str) or not is_immutable_doc_id(doc_id) or doc_id != doc_id.strip():
            raise ValueError(f"{field}.doc_id must use exact immutable document identity")
        if doc_id in seen_ids:
            raise ValueError(f"{field} contains duplicate doc_id {doc_id!r}")
        seen_ids.add(doc_id)
        if not isinstance(row.get("title"), str) or not row["title"].strip():
            raise ValueError(f"{field}.title must not be empty")
        if not isinstance(row.get("draft"), bool):
            raise ValueError(f"{field}.draft must be an explicit boolean")
        return doc_id

    def select_ordinary_docs(self, ignored_ids: frozenset[str]) -> dict[str, dict[str, Any]]:
        """Prune draft and unpublishable ordinary branches in one tree traversal."""
        path = resolve_workspace_path(self.repo_root, generated_documents_path(self.config)) / "index-tree.json"
        tree = self.read_metadata(path)
        if tree.get("schema") != DOCS_INDEX_TREE_SCHEMA_VERSION:
            raise ValueError(f"Docs Viewer search requires {DOCS_INDEX_TREE_SCHEMA_VERSION}: {path}")
        selected: dict[str, dict[str, Any]] = {}
        seen_ids: set[str] = set()

        def visit(rows: list[Any], parent_id: str) -> None:
            for row in rows:
                doc_id = self.validate_metadata_row(row, field=str(path), seen_ids=seen_ids)
                if row["draft"] or doc_id in ignored_ids:
                    continue
                selected[doc_id] = {**row, "parent_id": parent_id}
                children = row.get("children", [])
                if not isinstance(children, list):
                    raise ValueError(f"{path}: children must be an array for {doc_id}")
                visit(children, doc_id)

        visit(tree["docs"], "")
        return selected

    def select_collection_docs(
        self, ordinary_ids: set[str],
    ) -> list[tuple[DocsCollectionConfig, dict[str, dict[str, Any]]]]:
        """Read only included, eligible-host manifests and filter their flat entries."""
        selections = []
        for collection in sorted(self.config.site_search_collections, key=lambda item: item.collection):
            if collection.report_host_doc_id not in ordinary_ids:
                continue
            path = resolve_workspace_path(self.repo_root, generated_documents_path(collection)) / "manage-manifest.json"
            manifest = self.read_metadata(path)
            selected: dict[str, dict[str, Any]] = {}
            seen_ids: set[str] = set()
            for index, row in enumerate(manifest["docs"]):
                field = f"{path}.docs[{index}]"
                doc_id = self.validate_metadata_row(row, field=field, seen_ids=seen_ids)
                if row["draft"]:
                    continue
                if not isinstance(row.get("last_updated"), str):
                    raise ValueError(f"{field}.last_updated must be a string")
                selected[doc_id] = row
            selections.append((collection, selected))
        return selections

    def load_selected_sources(
        self, config: DocsStageConfig | DocsCollectionConfig, selected: dict[str, dict[str, Any]],
    ) -> dict[str, SourceDoc]:
        """Load exact selected IDs and fail on missing or stale selected sources.

        The shared filename loader omits deleted files for watcher use. Search
        requires every selected file and does not infer replacements or scan.
        """
        if not selected:
            return {}
        sources = load_document_collection_docs_for_config(
            self.repo_root, self.config, config,
            filenames=[f"{doc_id}.md" for doc_id in selected],
        )
        source_by_id = {document.doc_id: document for document in sources}
        for doc_id, row in selected.items():
            document = source_by_id.get(doc_id)
            target = f"working/{getattr(config, 'collection', 'documents')}/{doc_id}"
            if document is None:
                raise ValueError(f"Search selected document has no source: {target}")
            if (
                document.front_matter.get("doc_id") != doc_id
                or normalize_text(document.title) != normalize_text(row["title"])
                or document.front_matter["draft"] is not False
            ):
                raise ValueError(f"Search metadata and source identity, title or draft are stale: {target}")
            if isinstance(config, DocsStageConfig) and document.parent_id != row["parent_id"]:
                raise ValueError(f"Search tree and source parent_id are stale: {target}")
        return source_by_id

    def load_source_docs(self, selected: dict[str, dict[str, Any]]) -> list[SearchDocRecord]:
        source_by_id = self.load_selected_sources(self.config, selected)
        return [
            SearchDocRecord(
                doc_id=doc_id,
                title=normalize_text(row["title"]),
                last_updated=normalize_text(source_by_id[doc_id].front_matter.get("last_updated")),
                parent_id=row["parent_id"],
                summary=normalize_text(source_by_id[doc_id].front_matter.get("summary")),
                body_markdown=source_by_id[doc_id].body,
                report=source_by_id[doc_id].report,
            )
            for doc_id, row in selected.items()
        ]

    def viewer_url_for(self, doc_id: str) -> str:
        """Resolve generated by-ID input URLs for source/output consistency checks."""
        pairs: list[str] = []
        pairs.append(f"stage={quote(self.config.stage)}")
        pairs.append(f"doc={quote(str(doc_id))}")
        return f"/docs/?{'&'.join(pairs)}"

    def build_docs_v2_payload(
        self,
        *,
        generated_at_utc: str | None = None,
    ) -> dict[str, Any]:
        ignored_ids = read_publication_ignore_ids(self.repo_root)
        ordinary_selection = self.select_ordinary_docs(ignored_ids)
        collection_selections = self.select_collection_docs(set(ordinary_selection))
        docs = self.load_source_docs(ordinary_selection)
        title_by_id = {doc.doc_id: doc.title for doc in docs}
        combined_docs = list(docs)
        for collection, selected in collection_selections:
            combined_docs.extend(self.load_named_collection_docs(collection, selected))
        records: list[dict[str, Any]] = []
        for doc in combined_docs:
            parent_title = "" if not doc.parent_id else normalize_text(title_by_id.get(doc.parent_id))
            record: dict[str, Any] = {
                "id": doc.doc_id,
                "title": doc.title,
                "summary": doc.summary,
                "last_updated": doc.last_updated,
                "parent_id": doc.parent_id,
                "parent_title": parent_title,
                "display_meta": compact_join(
                    doc.last_updated,
                    doc.collection_title or parent_title,
                ),
            }
            if doc.collection:
                record.update(
                    {
                        "collection": doc.collection,
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
        return build_search_index(
            documents=records,
            search_fields=self.config.search_fields,
            generated_at_utc=generated_at_utc,
        )

    def load_named_collection_docs(
        self,
        collection: DocsCollectionConfig,
        selected: dict[str, dict[str, Any]],
    ) -> list[SearchDocRecord]:
        """Retain selected subdoc source/manifest/by-ID consistency before indexing."""
        output_root = resolve_workspace_path(
            self.repo_root,
            generated_documents_path(collection),
        )
        source_by_id = self.load_selected_sources(collection, selected)
        report_doc_id = collection.report_host_doc_id
        collection_title = normalize_text(collection.title)
        records: list[SearchDocRecord] = []
        for doc_id, row in selected.items():
            title = normalize_text(row["title"])
            source_doc = source_by_id[doc_id]
            by_id_path = output_root / "by-id" / f"{doc_id}.json"
            try:
                by_id = json.loads(by_id_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise ValueError(
                    f"Docs Viewer search requires readable collection by-id payload: {by_id_path}"
                ) from exc
            if not isinstance(by_id, dict):
                raise ValueError(f"collection by-id payload must be an object: {by_id_path}")

            expected_url = f"{self.viewer_url_for(report_doc_id)}&subdoc={quote(doc_id)}"
            by_id_title = normalize_text(by_id.get("title"))
            if title != by_id_title:
                raise ValueError(
                    f"collection manifest, source, and by-id titles must match for "
                    f"{self.config.stage}/{collection.collection}/{doc_id}"
                )
            if (
                by_id.get("doc_id") != doc_id
                or by_id.get("viewer_url") != expected_url
            ):
                raise ValueError(
                    f"collection by-id identity or viewer_url is stale for "
                    f"{self.config.stage}/{collection.collection}/{doc_id}"
                )
            last_updated = normalize_text(by_id.get("last_updated"))
            if (
                last_updated != normalize_text(source_doc.front_matter.get("last_updated"))
                or last_updated != normalize_text(row["last_updated"])
            ):
                raise ValueError(
                    f"collection manifest, source and by-id last_updated must match for "
                    f"{self.config.stage}/{collection.collection}/{doc_id}"
                )
            records.append(
                SearchDocRecord(
                    doc_id=doc_id,
                    title=title,
                    last_updated=last_updated,
                    parent_id="",
                    summary=normalize_text(source_doc.front_matter.get("summary")),
                    body_markdown=source_doc.body,
                    report=source_doc.report,
                    collection=collection.collection,
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
        print(f"Dry run: {count} {self.config.stage} search docs")
        print(f"Would write: {relative_output_path}")

    def print_write_message(self, relative_output_path: str, count: int) -> None:
        print(f"Wrote {relative_output_path} with {count} {self.config.stage} search docs")

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
    parser.add_argument("--stage", required=True, choices=("working",), help="Working owns Search generation.")
    add_workspace_arguments(parser)
    parser.add_argument("--output", help="Generated search index output path.")
    parser.add_argument("--write", action="store_true", help="Persist generated files; default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Write even when the content version matches.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    apply_workspace_overrides(args)
    repo_root = Path.cwd().resolve()
    try:
        builder = DocsViewerSearchDataBuilder(
            repo_root=repo_root,
            stage=args.stage,
            output_path=Path(args.output) if args.output else None,
        )
        builder.run(
            write=args.write,
            force=args.force,
        )
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Search build failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
