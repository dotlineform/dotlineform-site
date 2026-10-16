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
from docs_builder.semantic_tokens import replace_semantic_tokens  # noqa: E402
from docs_builder.source import DocRecord  # noqa: E402
from docs_builder.summary_directive import omit_summary_directives  # noqa: E402
from docs_workspace_config import (  # noqa: E402
    DocsCollectionConfig,
    DocsStageConfig,
    load_docs_stage,
    document_source_path,
    generated_documents_path,
    generated_search_path,
    resolve_workspace_path,
)
from docs_discovery_selection import (  # noqa: E402
    DiscoverySelection, read_discovery_metadata, select_collection_documents, select_ordinary_documents,
)
from docs_document_identity import doc_updated_date, is_immutable_doc_id  # noqa: E402
from docs_publication_ignore import read_publication_ignore_ids  # noqa: E402
from docs_report_source import (  # noqa: E402
    ReportDescriptor,
    ReportSourceContractRequired,
    project_report_markdown,
)
from docs_source_model import (  # noqa: E402
    SourceDoc,
    parse_document_report,
    report_source_contract_for_collection,
)
from docs_front_matter import FRONT_MATTER_PATTERN, read_front_matter_fields  # noqa: E402
from docs_management_document_target import confined_document_path  # noqa: E402
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


def search_records_from_build(
    discovery: DiscoverySelection, documents: dict[str, list[DocRecord]],
) -> list[SearchDocRecord]:
    """Project loaded sources using the complete Build's shared discovery selection."""
    records = []
    owners = [(None, discovery.ordinary), *discovery.collections]
    for owner, selected in owners:
        collection = "" if owner is None else owner.collection
        source_by_id = {doc.doc_id: doc for doc in documents[collection]}
        for doc_id, row in selected.items():
            doc = source_by_id[doc_id]
            records.append(SearchDocRecord(
                doc_id=doc_id, title=row["title"],
                last_updated=doc.last_updated, parent_id=row["parent_id"] if owner is None else "",
                summary=doc.front_matter.get("summary", ""), body_markdown=doc.body_markdown,
                report=doc.report, collection=collection,
                report_doc_id="" if owner is None else owner.report_host_doc_id,
                collection_title="" if owner is None else owner.title,
            ))
    return records


def compact_join(*parts: str) -> str:
    return " • ".join(part for part in parts if part)


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
    """Build one stage-independent table/postings from completed display metadata."""
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
            document["id"],
            document.get("collection", ""),
            document.get("report_doc_id", ""),
        ),
    )
    docs = [
        {key: document[key] for key in doc_fields if key in document and (document[key] or key == "title")}
        for document in ordered_documents
    ]

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
        config: DocsStageConfig | None = None,
    ) -> None:
        if stage != "working":
            raise ValueError("Search builds require Working; Preview copies the existing index")
        self.repo_root = repo_root.resolve()
        self.config = load_docs_stage(self.repo_root, stage) if config is None else config
        self.content_search_enabled = bool(
            SEARCH_V2_CONTENT_FIELDS.intersection(self.config.search_fields)
        )
        self.output_path = self.resolve_path(output_path or generated_search_path(self.config))

    def run(
        self,
        *,
        write: bool,
        force: bool,
        documents: list[SearchDocRecord] | None = None,
    ) -> dict[str, Any]:
        """Return the complete payload and structured write/skip diagnostics.

        Prepared records come from the complete Working owner; standalone
        execution consumes saved metadata and reads its required selected sources.
        """
        payload = self.build_docs_v2_payload(documents=documents)
        result = self.write_payload(payload, write=write, force=force)
        if write:
            from docs_publication_preparation import queue_shared_file

            queue_shared_file(self.config, "search")
        return result

    def resolve_path(self, path: Path | str | None) -> Path | None:
        if path is None:
            return None
        return resolve_workspace_path(self.repo_root, Path(path))

    def select_ordinary_docs(self, ignored_ids: frozenset[str]) -> dict[str, dict[str, Any]]:
        """Read current Working tree metadata through the shared eligibility owner."""
        path = resolve_workspace_path(self.repo_root, generated_documents_path(self.config)) / "index-tree.json"
        tree = read_discovery_metadata(path)
        return select_ordinary_documents(tree["docs"], ignored_ids)

    def load_selected_sources(
        self, config: DocsStageConfig | DocsCollectionConfig, selected: dict[str, dict[str, Any]],
    ) -> dict[str, SourceDoc]:
        """Read exact selected source content without generated-data agreement audits."""
        if not selected:
            return {}
        root = resolve_workspace_path(self.repo_root, document_source_path(config)).resolve()
        collection = getattr(config, "collection", "")
        sources = {}
        report_contract = None
        for doc_id, row in selected.items():
            path = confined_document_path(root, doc_id)
            source_text = path.read_bytes().decode("utf-8")
            header = FRONT_MATTER_PATTERN.match(source_text)
            if header is None:
                raise ValueError(f"Search source front matter could not be parsed in {path.name}")
            metadata = {
                field.key: field.value
                for field in read_front_matter_fields(header.group(1), source_name=path.name)
            }
            if metadata["doc_id"] != doc_id:
                raise ValueError(f"Search source identity does not match its selected filename: {path.name}")
            body = source_text[header.end():]
            try:
                report = parse_document_report(
                    source_text, metadata, body, source_name=path.name, contract=report_contract,
                )
            except ReportSourceContractRequired:
                report_contract = report_source_contract_for_collection(self.repo_root, self.config, config)
                report = parse_document_report(
                    source_text, metadata, body, source_name=path.name, contract=report_contract,
                )
            sources[doc_id] = SourceDoc(
                path=path, source_text=source_text, front_matter=metadata, body=body,
                doc_id=doc_id, title=row["title"], ui_status="",
                parent_id=row["parent_id"] if not collection else "", report=report,
            )
        return sources

    def load_source_docs(self, selected: dict[str, dict[str, Any]]) -> list[SearchDocRecord]:
        source_by_id = self.load_selected_sources(self.config, selected)
        return [
            SearchDocRecord(
                doc_id=doc_id,
                title=row["title"],
                last_updated=source_by_id[doc_id].front_matter.get("last_updated", ""),
                parent_id=row["parent_id"],
                summary=source_by_id[doc_id].front_matter.get("summary", ""),
                body_markdown=source_by_id[doc_id].body,
                report=source_by_id[doc_id].report,
            )
            for doc_id, row in selected.items()
        ]

    def build_docs_v2_payload(
        self,
        *,
        generated_at_utc: str | None = None,
        documents: list[SearchDocRecord] | None = None,
    ) -> dict[str, Any]:
        if documents is None:
            ignored_ids = read_publication_ignore_ids(self.repo_root, config=self.config)
            ordinary_selection = self.select_ordinary_docs(ignored_ids)
            collection_selections = select_collection_documents(self.repo_root, self.config, set(ordinary_selection))
            documents = self.load_source_docs(ordinary_selection)
            for collection, selected in collection_selections:
                documents.extend(self.load_named_collection_docs(collection, selected))
        title_by_id = {doc.doc_id: doc.title for doc in documents if not doc.collection}
        records: list[dict[str, Any]] = []
        for doc in documents:
            parent_title = "" if not doc.parent_id else title_by_id.get(doc.parent_id, "")
            updated_date = doc_updated_date(doc.last_updated)
            record: dict[str, Any] = {
                "id": doc.doc_id,
                "title": doc.title,
                "summary": doc.summary,
                "last_updated": updated_date,
                "parent_id": doc.parent_id,
                "parent_title": parent_title,
                "display_meta": compact_join(
                    updated_date,
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
        self, collection: DocsCollectionConfig, selected: dict[str, dict[str, Any]],
    ) -> list[SearchDocRecord]:
        """Consume selected manifest metadata and required source content."""
        source_by_id = self.load_selected_sources(collection, selected)
        return [
            SearchDocRecord(
                doc_id=doc_id, title=row["title"],
                last_updated=source_by_id[doc_id].front_matter.get("last_updated", ""),
                parent_id="", summary=source_by_id[doc_id].front_matter.get("summary", ""),
                body_markdown=source_by_id[doc_id].body, report=source_by_id[doc_id].report,
                collection=collection.collection, report_doc_id=collection.report_host_doc_id,
                collection_title=collection.title,
            )
            for doc_id, row in selected.items()
        ]

    def searchable_markdown(self, doc: SearchDocRecord) -> str:
        markdown = project_report_markdown(
            doc.body_markdown,
            doc.report,
            include_host=False,
        )
        markdown = omit_summary_directives(markdown)
        markdown = replace_semantic_tokens(
            markdown,
            registry=None,
            replacer=lambda token: " " if token.family == "image" else html.escape(token.title),
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
            return {"payload": payload, "diagnostics": {"docs": count, "wrote": 0, "skipped": 1}}
        if not write:
            self.print_dry_run_message(relative_output_path, count)
            return {"payload": payload, "diagnostics": {"docs": count, "wrote": 0, "skipped": 0}}
        if self.output_path is None:
            raise ValueError("Generated search index output path is required")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json_text(payload), encoding="utf-8")
        self.print_write_message(relative_output_path, count)
        return {"payload": payload, "diagnostics": {"docs": count, "wrote": 1, "skipped": 0}}

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
        return header.get("version") if isinstance(header, dict) else None

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
