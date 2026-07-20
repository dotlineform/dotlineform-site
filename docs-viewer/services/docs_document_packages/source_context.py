#!/usr/bin/env python3
"""Docs source context loading for document-package workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
if str(DOCS_BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_BUILD_DIR))

from build_docs import DocsDataBuilder, DocRecord, parse_source  # noqa: E402
from docs_scope_config import DocsScopeConfig, document_source_path, load_docs_scope_configs, resolve_scope_path  # noqa: E402
from docs_document_packages.rendered_content import doc_content_text  # noqa: E402
from docs_document_packages.source_records import (  # noqa: E402
    DocumentPackageSourceRecord,
    front_matter_bool,
    source_record_from_doc,
)


@dataclass
class DocumentPackageSourceContext:
    repo_root: Path
    scope: str
    scope_config: DocsScopeConfig
    source_root: Path
    builder: DocsDataBuilder
    source_docs: list[DocRecord]
    records: list[DocumentPackageSourceRecord]
    records_by_id: dict[str, DocumentPackageSourceRecord]
    source_docs_by_id: dict[str, DocRecord]
    children_by_parent: dict[str, list[DocumentPackageSourceRecord]]
    render_cache: dict[str, str]


def source_file_path(context: DocumentPackageSourceContext, doc: DocRecord) -> Path:
    path = (context.source_root / doc.source_path).resolve()
    try:
        path.relative_to(context.source_root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"docs source path escapes scope source root: {path}") from exc
    return path


def load_document_package_source_context(repo_root: Path, scope: str) -> DocumentPackageSourceContext:
    root = repo_root.resolve()
    configs = load_docs_scope_configs(root)
    normalized_scope = str(scope or "").strip().lower()
    config = configs.get(normalized_scope)
    if config is None:
        raise ValueError(f"unknown docs scope for document package source context: {scope}")

    source_root = resolve_scope_path(root, document_source_path(config))
    if not source_root.exists() or not source_root.is_dir():
        raise RuntimeError(
            f"missing source root for scope {normalized_scope}: {document_source_path(config).as_posix()}"
        )

    builder = DocsDataBuilder(repo_root=root, config=config)
    source_docs = builder.load_docs()
    builder.validate_docs(source_docs)

    source_docs_by_id = {doc.doc_id: doc for doc in source_docs}
    records: list[DocumentPackageSourceRecord] = []
    context = DocumentPackageSourceContext(
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
        content_text = doc_content_text(context, doc.doc_id)
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
    children_by_parent: dict[str, list[DocumentPackageSourceRecord]] = {}
    for record in records:
        children_by_parent.setdefault(record.parent_id, []).append(record)
    context.children_by_parent = children_by_parent
    return context


def load_document_package_source_records(repo_root: Path, scope: str) -> list[DocumentPackageSourceRecord]:
    return load_document_package_source_context(repo_root, scope).records
