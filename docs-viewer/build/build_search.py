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
from pathlib import Path
from typing import Any, Callable, Mapping

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

from docs_builder.common import (  # noqa: E402
    HTML_MEDIA_TOKEN_PATTERN,
    MEDIA_TOKEN_PATTERN,
)
from docs_builder.page_break_directive import (  # noqa: E402
    PAGE_BREAK_COLLECTIONS, PAGE_BREAK_DIRECTIVE, PAGE_BREAK_TOKEN, install_page_break_rule,
)
from docs_builder.source_tokens import replace_source_tokens  # noqa: E402
from docs_builder.source import DocRecord  # noqa: E402
from docs_builder.summary_directive import SUMMARY_DIRECTIVE, SUMMARY_TOKEN, install_summary_rule  # noqa: E402
from docs_workspace_config import (  # noqa: E402
    DocsCollectionConfig,
    DocsStageConfig,
    DocsWorkspaceConfig,
    load_docs_workspace_config,
    select_workspace_stage,
    document_source_path,
    generated_search_path,
)
from docs_discovery_selection import (  # noqa: E402
    DiscoverySelection, read_discovery_galleries, read_discovery_selection,
)
from docs_document_identity import is_immutable_doc_id  # noqa: E402
from docs_publication_paths import confined  # noqa: E402
from docs_search_scopes import COLLECTION_SEARCH_SCOPES, PORTFOLIO_DOCUMENT_COLLECTIONS, PORTFOLIO_HOST_COLLECTIONS, search_artifact  # noqa: E402
from docs_publication_ignore import read_publication_ignore_ids  # noqa: E402
from docs_report_source import (  # noqa: E402
    ReportDescriptor,
    ReportSourceContractRequired,
    project_report_markdown,
)
from docs_source_model import (  # noqa: E402
    parse_document_report,
    report_source_contract_for_collection,
    write_text_atomic,
)
from docs_front_matter import FRONT_MATTER_PATTERN, read_front_matter_fields  # noqa: E402
from docs_management_document_target import confined_document_path  # noqa: E402
from markdown_renderer import build_markdown_renderer, extract_markdown_search_fields, normalize_markdown_blank_lines  # noqa: E402


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
SEARCH_V2_GROUPED_INTEGER = re.compile(r"(?<![\w.-])(?<![0-9],)[0-9]{1,3}(?:,[0-9]{3})+(?![^\W_]|[._-][^\W_]|,[0-9])")
SEARCH_V2_INTEGER = re.compile(r"[0-9]+")
SEARCH_V2_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
SEARCH_V2_CONTENT_HASH = re.compile(r"^[0-9a-f]{64}$")


def omit_search_directives(markdown: str, *, page_breaks: bool) -> str:
    """Omit authored boundaries and duplicate Summary text while keeping literal examples."""
    has_summary = SUMMARY_DIRECTIVE in markdown
    has_page_break = page_breaks and PAGE_BREAK_DIRECTIVE in markdown
    if not has_summary and not has_page_break:
        return markdown
    normalized = normalize_markdown_blank_lines(markdown)
    renderer = build_markdown_renderer()
    directives = {}
    if has_summary:
        install_summary_rule(renderer, summary_html="")
        directives[SUMMARY_TOKEN] = SUMMARY_DIRECTIVE
    if has_page_break:
        install_page_break_rule(renderer)
        directives[PAGE_BREAK_TOKEN] = PAGE_BREAK_DIRECTIVE
    lines = normalized.splitlines(keepends=True)
    for token in renderer.parse(normalized):
        if directive := directives.get(token.type):
            line = token.map[0]
            lines[line] = lines[line].replace(directive, "", 1)
    return "".join(lines)


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def compact_join(*parts: str) -> str:
    return " • ".join(part for part in parts if part)


def normalize_search_value_v2(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).lower()
    return re.sub(r"\s+", " ", normalized).strip()


def tokenize_search_value_v2(value: Any, *, include_numbers: bool = False) -> list[str]:
    terms: dict[str, None] = {}
    text = SEARCH_V2_EXCLUDED_SPANS.sub(" ", unicodedata.normalize("NFKC", str(value or "")))
    if include_numbers:
        text = SEARCH_V2_GROUPED_INTEGER.sub(lambda match: match[0].replace(",", ""), text)
    for token in SEARCH_V2_TOKEN.findall(text):
        normalized_token = normalize_search_value_v2(token)
        if is_immutable_doc_id(normalized_token) or SEARCH_V2_CONTENT_HASH.fullmatch(normalized_token):
            continue
        if include_numbers and SEARCH_V2_INTEGER.fullmatch(normalized_token):
            terms[normalized_token] = None
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
            if useful:
                terms[term] = None
    return list(terms)


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
        "kind",
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
                    else tokenize_search_value_v2(value, include_numbers=field == "title")
                )
                for term in filter(None, terms):
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


def relative_path(path: Path, repo_root: Path) -> str:
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

    def __init__(self, *, repo_root: Path, workspace: DocsWorkspaceConfig, config: DocsStageConfig) -> None:
        self.repo_root = repo_root
        self.workspace = workspace
        self.config = config

    def run(
        self,
        selection: DiscoverySelection,
        galleries: dict[str, Any] | None,
        *,
        write: bool,
        force: bool = False,
        documents: Mapping[str, list[DocRecord]] | None = None,
        on_written: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Write each completed scope and hand its exact selection to the workflow."""
        root = generated_search_path(self.config).parent
        collection_rows = {owner.collection: (owner, rows) for owner, rows in selection.collections}
        results = {}
        portfolio = self.portfolio_rows(selection, galleries)
        for scope in ("portfolio", *COLLECTION_SEARCH_SCOPES):
            if scope == "portfolio":
                rows, fields = portfolio, ("title",)
            else:
                fields = ("title", "summary") if scope in ("library", "book") else self.config.search_fields
                owner_rows = collection_rows.get(scope)
                rows = self.collection_rows(*owner_rows, fields=fields, documents=documents) if owner_rows else []
            output, filename = search_artifact(scope)
            path = confined(root, filename)
            payload = build_search_index(documents=rows, search_fields=fields)
            result = self.write_payload(path, payload, write=write, force=force)
            if result["wrote"] and on_written is not None:
                on_written(output)
            results[scope] = result
        return {key: sum(result[key] for result in results.values()) for key in ("docs", "wrote", "skipped")} | {"scopes": results}

    def portfolio_rows(self, selection: DiscoverySelection, galleries: dict[str, Any] | None) -> list[dict[str, Any]]:
        reference_hosts = {owner.report_host_doc_id for owner in self.config.collections
                           if owner.collection not in PORTFOLIO_HOST_COLLECTIONS}
        rows = [
            {"id": doc_id, "title": row["title"], "parent_id": row["parent_id"]}
            for doc_id, row in selection.ordinary.items() if doc_id not in reference_hosts
        ]
        for owner, selected in selection.collections:
            if owner.collection in PORTFOLIO_DOCUMENT_COLLECTIONS:
                rows.extend(self.collection_entry(owner, doc_id, row) for doc_id, row in selected.items())
        if galleries is not None:
            rows.extend({"id": gallery_id, "title": title, "kind": "catalogue-gallery"}
                        for gallery_id, title in galleries["galleries"].items())
        return rows

    def collection_entry(self, owner: DocsCollectionConfig, doc_id: str, row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": doc_id, "title": row["title"], "collection": owner.collection,
            "report_doc_id": owner.report_host_doc_id, "collection_title": owner.title,
            "last_updated": row["last_updated"], "display_meta": compact_join(row["last_updated"], owner.title),
        }

    def source_fields(self, root: Path, doc_id: str) -> tuple[str, dict[str, Any], str]:
        path = confined_document_path(root, doc_id)
        source = path.read_bytes().decode("utf-8")
        header = FRONT_MATTER_PATTERN.match(source)
        if header is None:
            raise ValueError(f"Search source front matter could not be parsed in {path.name}")
        fields = {field.key: field.value for field in read_front_matter_fields(header.group(1), source_name=path.name)}
        if fields["doc_id"] != doc_id:
            raise ValueError(f"Search source identity does not match its selected filename: {path.name}")
        return source, fields, source[header.end():]

    def collection_rows(
        self,
        owner: DocsCollectionConfig,
        selected: Mapping[str, dict[str, Any]],
        *,
        fields: tuple[str, ...],
        documents: Mapping[str, list[DocRecord]] | None,
    ) -> list[dict[str, Any]]:
        needs_body = not SEARCH_V2_CONTENT_FIELDS.isdisjoint(fields)
        page_breaks = owner.collection in PAGE_BREAK_COLLECTIONS
        by_id = None if documents is None else {doc.doc_id: doc for doc in documents[owner.collection]}
        root = document_source_path(owner).resolve() if by_id is None else None
        report_contract = None
        rows = []
        for doc_id, row in selected.items():
            record = self.collection_entry(owner, doc_id, row)
            report = None
            if by_id is not None:
                doc = by_id[doc_id]
                metadata, body, report = doc.front_matter, doc.body_markdown, doc.report
            else:
                source, metadata, body = self.source_fields(root, doc_id)
                if needs_body:
                    try:
                        report = parse_document_report(source, metadata, body, source_name=f"{doc_id}.md", contract=report_contract)
                    except ReportSourceContractRequired:
                        report_contract = report_source_contract_for_collection(self.repo_root, self.config, owner)
                        report = parse_document_report(source, metadata, body, source_name=f"{doc_id}.md", contract=report_contract)
            record["summary"] = metadata.get("summary", "")
            if needs_body:
                markdown = self.searchable_markdown(body, report, page_breaks=page_breaks)
                content = extract_markdown_search_fields(markdown, title=row["title"])
                record.update(heading=content.headings, body=content.body, code=content.code)
            rows.append(record)
        return rows

    def searchable_markdown(self, body: str, report: ReportDescriptor | None, *, page_breaks: bool) -> str:
        markdown = project_report_markdown(
            body,
            report,
            include_host=False,
        )
        markdown = omit_search_directives(markdown, page_breaks=page_breaks)
        markdown = replace_source_tokens(
            markdown,
            replacer=lambda token: " " if token.family == "image" or not token.visible else html.escape(token.title),
        )
        markdown = HTML_MEDIA_TOKEN_PATTERN.sub("", markdown)
        return MEDIA_TOKEN_PATTERN.sub("", markdown)

    def write_payload(
        self, path: Path, payload: dict[str, Any], *, write: bool, force: bool,
    ) -> dict[str, int]:
        count = payload["header"]["count"]
        relative_output_path = relative_path(path, self.repo_root)
        if not force and self.extract_existing_version(path) == payload["header"]["version"]:
            self.print_skip_message(relative_output_path, write)
            return {"docs": count, "wrote": 0, "skipped": 1}
        if not write:
            self.print_dry_run_message(relative_output_path, count)
            return {"docs": count, "wrote": 0, "skipped": 0}
        path.parent.mkdir(parents=True, exist_ok=True)
        write_text_atomic(path, json_text(payload))
        self.print_write_message(relative_output_path, count)
        return {"docs": count, "wrote": 1, "skipped": 0}

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

    def extract_existing_version(self, path: Path) -> str | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        header = payload.get("header") if isinstance(payload, dict) else None
        return header.get("version") if isinstance(header, dict) else None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer search indexes.")
    parser.add_argument("--stage", required=True, choices=("working",), help="Working owns Search generation.")
    add_workspace_arguments(parser)
    parser.add_argument("--write", action="store_true", help="Persist generated files; default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Write even when the content version matches.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    apply_workspace_overrides(args)
    repo_root = Path.cwd().resolve()
    try:
        workspace = load_docs_workspace_config(repo_root)
        config = select_workspace_stage(workspace, args.stage)
        builder = DocsViewerSearchDataBuilder(repo_root=repo_root, workspace=workspace, config=config)
        selection = read_discovery_selection(repo_root, config, read_publication_ignore_ids(repo_root, config=config))
        galleries = read_discovery_galleries(repo_root, workspace, config, selection.ordinary)
        if args.write:
            from docs_publication_queue import read_queue, select_shared, save_queue
            pending = read_queue(workspace)

            def on_written(output: str) -> None:
                select_shared(pending, "workspace", output)
                save_queue(workspace, pending)
        else:
            on_written = None
        builder.run(selection, galleries, write=args.write, force=args.force, on_written=on_written)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Search build failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
