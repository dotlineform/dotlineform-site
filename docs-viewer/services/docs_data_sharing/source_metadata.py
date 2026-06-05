#!/usr/bin/env python3
"""Source-derived docs metadata for Data Sharing document workflows."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
for path in (DOCS_BUILD_DIR, SHARED_PYTHON_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_docs import DocsDataBuilder, DocRecord, parse_source  # noqa: E402
from docs_scope_config import DocsScopeConfig, load_docs_scope_configs  # noqa: E402
from markdown_renderer import plain_text_from_html  # noqa: E402


@dataclass(frozen=True)
class DataSharingDocsSourceRecord:
    doc_id: str
    scope: str
    title: str
    published: bool
    summary: str
    added_date: str
    last_updated: str
    parent_id: str
    parent_title: str
    viewable: bool
    ui_status: str
    source_path: str
    viewer_url: str
    content_text_length: int


@dataclass
class DataSharingDocsSourceContext:
    repo_root: Path
    scope: str
    scope_config: DocsScopeConfig
    source_root: Path
    builder: DocsDataBuilder
    source_docs: list[DocRecord]
    records: list[DataSharingDocsSourceRecord]
    records_by_id: dict[str, DataSharingDocsSourceRecord]
    source_docs_by_id: dict[str, DocRecord]
    children_by_parent: dict[str, list[DataSharingDocsSourceRecord]]
    render_cache: dict[str, str]


class HeadingCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[str] = []
        self._current_tag = ""
        self._current_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        if tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_tag = tag_name
            self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        if not self._current_tag or tag.lower() != self._current_tag:
            return
        text = normalize_text("".join(self._current_parts))
        if text:
            self.headings.append(text)
        self._current_tag = ""
        self._current_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_tag:
            self._current_parts.append(data)


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def front_matter_bool(front_matter: dict[str, Any], key: str, default: bool) -> bool:
    if key not in front_matter:
        return default
    value = front_matter[key]
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


def source_path_for_record(repo_root: Path, source_root: Path, doc: DocRecord) -> str:
    path = (source_root / doc.source_path).resolve()
    try:
        return path.relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"docs source path escapes repo root: {path}") from exc


def source_file_path(context: DataSharingDocsSourceContext, doc: DocRecord) -> Path:
    path = (context.source_root / doc.source_path).resolve()
    try:
        path.relative_to(context.source_root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"docs source path escapes scope source root: {path}") from exc
    return path


def source_record_from_doc(
    *,
    repo_root: Path,
    source_root: Path,
    scope: str,
    doc: DocRecord,
    parent_title: str,
    published: bool,
    content_text_length: int,
) -> DataSharingDocsSourceRecord:
    return DataSharingDocsSourceRecord(
        doc_id=doc.doc_id,
        scope=scope,
        title=doc.title,
        published=published,
        summary=doc.summary,
        added_date=doc.added_date,
        last_updated=doc.last_updated,
        parent_id=doc.parent_id,
        parent_title=parent_title,
        viewable=doc.viewable,
        ui_status=doc.ui_status,
        source_path=source_path_for_record(repo_root, source_root, doc),
        viewer_url=doc.viewer_url,
        content_text_length=content_text_length,
    )


def load_data_sharing_docs_source_context(repo_root: Path, scope: str) -> DataSharingDocsSourceContext:
    root = repo_root.resolve()
    configs = load_docs_scope_configs(root)
    normalized_scope = str(scope or "").strip().lower()
    config = configs.get(normalized_scope)
    if config is None:
        raise ValueError(f"unknown docs scope for Data Sharing source metadata: {scope}")

    source_root = (root / config.source).resolve()
    if not source_root.exists() or not source_root.is_dir():
        raise RuntimeError(f"missing source root for scope {normalized_scope}: {config.source.as_posix()}")

    builder = DocsDataBuilder(repo_root=root, config=config)
    source_docs = builder.load_docs()
    builder.validate_docs(source_docs)

    source_docs_by_id = {doc.doc_id: doc for doc in source_docs}
    records: list[DataSharingDocsSourceRecord] = []
    context = DataSharingDocsSourceContext(
        repo_root=root,
        scope=normalized_scope,
        scope_config=config,
        source_root=source_root,
        builder=builder,
        source_docs=source_docs,
        records=[],
        records_by_id={},
        source_docs_by_id=source_docs_by_id,
        children_by_parent={},
        render_cache={},
    )

    for doc in builder.ordered_docs_for_index(source_docs):
        front_matter, _body = parse_source(source_file_path(context, doc))
        parent = source_docs_by_id.get(doc.parent_id)
        content_text = data_sharing_doc_content_text(context, doc.doc_id)
        records.append(
            source_record_from_doc(
                repo_root=root,
                source_root=source_root,
                scope=normalized_scope,
                doc=doc,
                parent_title=parent.title if parent else "",
                published=front_matter_bool(front_matter, "published", True),
                content_text_length=len(content_text),
            )
        )

    context.records = records
    context.records_by_id = {record.doc_id: record for record in records}
    children_by_parent: dict[str, list[DataSharingDocsSourceRecord]] = {}
    for record in records:
        children_by_parent.setdefault(record.parent_id, []).append(record)
    context.children_by_parent = children_by_parent
    return context


def load_data_sharing_docs_source_records(repo_root: Path, scope: str) -> list[DataSharingDocsSourceRecord]:
    return load_data_sharing_docs_source_context(repo_root, scope).records


def source_doc_for_id(context: DataSharingDocsSourceContext, doc_id: str) -> DocRecord:
    normalized_doc_id = str(doc_id or "").strip()
    doc = context.source_docs_by_id.get(normalized_doc_id)
    if doc is None:
        raise ValueError(f"unknown doc_id for Data Sharing source metadata: {normalized_doc_id}")
    return doc


def render_data_sharing_doc_html(context: DataSharingDocsSourceContext, doc_id: str) -> str:
    normalized_doc_id = str(doc_id or "").strip()
    if normalized_doc_id not in context.render_cache:
        doc = source_doc_for_id(context, normalized_doc_id)
        payload = context.builder.item_entry(doc, context.source_docs, {})
        context.render_cache[normalized_doc_id] = str(payload.get("content_html") or "")
    return context.render_cache[normalized_doc_id]


def data_sharing_doc_content_text(context: DataSharingDocsSourceContext, doc_id: str) -> str:
    doc = source_doc_for_id(context, doc_id)
    return plain_text_from_html(render_data_sharing_doc_html(context, doc.doc_id), title=doc.title)


def data_sharing_doc_headings(context: DataSharingDocsSourceContext, doc_id: str) -> list[str]:
    doc = source_doc_for_id(context, doc_id)
    parser = HeadingCollector()
    parser.feed(render_data_sharing_doc_html(context, doc.doc_id))
    parser.close()
    headings = list(parser.headings)
    if headings and normalize_text(headings[0]) == normalize_text(doc.title):
        headings.pop(0)
    return headings
