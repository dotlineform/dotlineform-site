#!/usr/bin/env python3
"""Shared per-document planning and apply helpers for Docs Import."""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

from docs_import_content import (  # noqa: E402
    CONTENT_INTENT_EMPTY_NEW,
    CONTENT_INTENT_PRESERVE_EXISTING,
    CONTENT_INTENT_REPLACE,
    ImportContent,
)
from docs_import_media import ImportMediaPreparation, materialize_import_media  # noqa: E402
from docs_import_source_helpers import import_summary_text, relative_path, viewer_url_for  # noqa: E402
from docs_import_source_interactive import materialize_interactive_html_assets  # noqa: E402
from docs_management_document_target import ManagedDocumentCollection, committed_document_record  # noqa: E402
from docs_source_model import (  # noqa: E402
    SourceDoc,
    advance_doc_front_matter,
    advance_front_matter_for_recent_edit,
    allocate_doc_id,
    collection_supports_draft,
    parse_source_text,
    parse_collection_document_report,
    validate_document_status_front_matter,
    current_doc_timestamp,
    doc_id_matches_added_date,
    format_source,
    is_immutable_doc_id,
    report_source_contract_for_collection,
    slugify,
    write_text_atomic,
    write_text_atomic_new,
)
from docs_workspace_config import DocsStageConfig, DocsCollectionConfig, require_document_authoring  # noqa: E402
from docs_index_order import index_order_path, index_order_text, insert_node, read_index_order, tree_parent_ids  # noqa: E402
from markdown_renderer import normalize_markdown_blank_lines  # noqa: E402
from docs_report_source import RETIRED_REPORT_KEYS, parse_report_source  # noqa: E402
from docs_document_media_ownership import DocumentMediaChange, compare_document_media  # noqa: E402


IMPORT_DOCUMENT_CREATE = "create"
IMPORT_DOCUMENT_OVERWRITE = "overwrite"
IMPORT_DOCUMENT_OPERATIONS = {IMPORT_DOCUMENT_CREATE, IMPORT_DOCUMENT_OVERWRITE}

ALLOWED_IMPORT_FRONT_MATTER_FIELDS = ("title", "parent_id", "summary")


@dataclass(frozen=True)
class ImportDocumentMediaContext:
    """Staged-source inputs required to materialize one document's media."""

    staging_root: Path
    source_path: Path
    interactive_html_plans: tuple[dict[str, Any], ...] = ()
    allow_interactive_html_overwrite: bool = False


@dataclass(frozen=True)
class ImportDocumentPlan:
    """Carry validated content, prepared source and exact hierarchy through apply."""

    operation: str
    record: ImportContent
    target_path: Path
    source_text: str
    title: str
    parent_id: str
    import_preview: dict[str, Any]
    committed_record: dict[str, Any]
    index_order_path: Path | None
    document_config: DocsStageConfig | DocsCollectionConfig
    prepared_document: SourceDoc
    collection: str = ""
    target: SourceDoc | None = None
    media_change: DocumentMediaChange | None = None
    inline_media_bytes: dict[tuple[str, str], bytes] = field(default_factory=dict)

    @property
    def media_changes(self) -> list[tuple[str, Any, DocumentMediaChange]]:
        return [(self.doc_id, self.document_config, self.media_change)] if self.media_change is not None else []

    @property
    def doc_id(self) -> str:
        return self.record.doc_id

    @property
    def event_name(self) -> str:
        return f"docs-import-source-{self.operation}"

    @property
    def docs_doc_ids(self) -> list[str]:
        return [self.doc_id]

    @property
    def changed_paths(self) -> list[Path]:
        paths = [self.target_path]
        if self.index_order_path is not None:
            paths.append(self.index_order_path)
        return paths


@dataclass(frozen=True)
class ImportDocumentApplyResult:
    inline_media_written: tuple[dict[str, Any], ...] = ()
    interactive_html_written: tuple[dict[str, Any], ...] = ()
    parent_ids: dict[str, str] | None = None


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _explicit_front_matter(record: ImportContent) -> dict[str, Any]:
    if "viewable" in record.front_matter:
        raise ValueError("ImportContent legacy viewable front matter is not supported")
    if "publishable" in record.front_matter:
        raise ValueError("ImportContent publishable front matter is retired")
    retired_report_keys = sorted(RETIRED_REPORT_KEYS.intersection(record.front_matter))
    if retired_report_keys:
        raise ValueError(
            f"ImportContent retired report front matter is not supported: {retired_report_keys[0]}"
        )
    front_matter = {
        field: copy.deepcopy(record.front_matter[field])
        for field in ALLOWED_IMPORT_FRONT_MATTER_FIELDS
        if field in record.front_matter
    }
    for field_name in ("title", "parent_id", "summary"):
        if field_name in front_matter and not isinstance(front_matter[field_name], str):
            raise ValueError(f"ImportContent front_matter {field_name} must be a string")
    if "title" in front_matter and _clean_text(front_matter["title"]) != _clean_text(record.title):
        raise ValueError("ImportContent title must match front_matter title")
    declared_parent_id = _clean_text(front_matter.get("parent_id"))
    if "parent_id" in front_matter and declared_parent_id != _clean_text(record.parent_id):
        raise ValueError("ImportContent parent_id must match front_matter parent_id")
    return front_matter


def _replacement_body(import_preview: dict[str, Any], title: str) -> str:
    markdown = normalize_markdown_blank_lines(_clean_text(import_preview.get("markdown_preview")))
    if markdown:
        return markdown + "\n"
    return f"# {title}\n"


def _apply_explicit_front_matter(
    front_matter: dict[str, Any],
    explicit_front_matter: dict[str, Any],
) -> None:
    if "summary" in explicit_front_matter:
        summary = _clean_text(explicit_front_matter.get("summary"))
        if summary:
            front_matter["summary"] = summary
        else:
            front_matter.pop("summary", None)


def _create_source(
    record: ImportContent,
    collection: str,
    import_preview: dict[str, Any],
    explicit_front_matter: dict[str, Any],
    added_date: str,
) -> tuple[str, str]:
    if record.content_intent == CONTENT_INTENT_PRESERVE_EXISTING:
        raise ValueError("preserve-existing content requires an existing import target")
    parent_id = _clean_text(record.parent_id)
    front_matter_seed: dict[str, Any] = {
        "doc_id": record.doc_id,
        "title": record.title,
        "added_date": added_date,
    }
    if collection:
        if parent_id or "parent_id" in explicit_front_matter:
            raise ValueError("parent_id is not accepted for a collection import")
    front_matter = advance_doc_front_matter(
        front_matter_seed,
        timestamp=added_date,
    )
    _apply_explicit_front_matter(front_matter, explicit_front_matter)
    body = (
        _replacement_body(import_preview, record.title)
        if record.content_intent == CONTENT_INTENT_REPLACE
        else ""
    )
    return format_source(front_matter, body, collection=collection), parent_id


def _overwrite_source(
    record: ImportContent,
    target: SourceDoc,
    import_preview: dict[str, Any],
    explicit_front_matter: dict[str, Any],
    *,
    collection: str,
    preserve_collection_metadata: bool = False,
) -> tuple[str, str]:
    if record.content_intent == CONTENT_INTENT_EMPTY_NEW:
        raise ValueError("empty-new content cannot overwrite an existing import target")
    front_matter = dict(target.front_matter)
    front_matter["doc_id"] = target.doc_id
    front_matter["title"] = record.title

    if record.content_intent == CONTENT_INTENT_REPLACE and not preserve_collection_metadata:
        # Retain the ordinary single-source overwrite cleanup contract.
        front_matter.pop("sort_order", None)

    _apply_explicit_front_matter(front_matter, explicit_front_matter)
    parent_id = target.parent_id
    body = (
        _replacement_body(import_preview, record.title)
        if record.content_intent == CONTENT_INTENT_REPLACE
        else target.body
    )
    candidate_source = format_source(front_matter, body, collection=collection)
    if candidate_source == target.source_text:
        return target.source_text, parent_id
    front_matter = advance_front_matter_for_recent_edit(
        target.front_matter,
        target.body,
        front_matter,
        body,
    )
    return format_source(front_matter, body, collection=collection), parent_id


def plan_import_document(
    repo_root: Path,
    record: ImportContent,
    *,
    operation: str,
    docs: list[SourceDoc],
    target: SourceDoc | None = None,
    import_preview: dict[str, Any] | None = None,
    create_doc_id: str = "",
    create_added_date: str = "",
    media_preparation: ImportMediaPreparation | None = None,
    collection: ManagedDocumentCollection | None = None,
    preserve_collection_metadata: bool = False,
) -> ImportDocumentPlan:
    """Validate and plan one create or overwrite without writing."""

    if collection is None:
        raise ValueError("Import requires an exact configured collection")
    collection_id = collection.collection
    create_root = collection.source_root
    document_config = collection.document_config
    parent_config = collection.parent_config
    require_document_authoring(parent_config)
    if operation == IMPORT_DOCUMENT_OVERWRITE and slugify(record.doc_id) != record.doc_id:
        raise ValueError("ImportContent doc_id must be a safe normalized docs id")
    if operation not in IMPORT_DOCUMENT_OPERATIONS:
        raise ValueError("import document operation must be create or overwrite")
    if operation == IMPORT_DOCUMENT_CREATE and target is not None:
        raise ValueError(f"cannot create existing import target {target.doc_id!r}")
    if operation == IMPORT_DOCUMENT_OVERWRITE and target is None:
        raise ValueError("overwrite requires an existing import target")
    if target is not None and target.doc_id != record.doc_id:
        raise ValueError("overwrite target doc_id must match ImportContent doc_id")
    if operation == IMPORT_DOCUMENT_OVERWRITE and target is not None and target.report is not None:
        raise ValueError("Docs Import cannot replace a report-host document")
    if record.content_intent == CONTENT_INTENT_REPLACE and not isinstance(import_preview, dict):
        raise ValueError("replace content requires a normalized import preview")

    preview = copy.deepcopy(import_preview or {})
    if record.content_intent == CONTENT_INTENT_REPLACE:
        incoming_body = _replacement_body(preview, record.title)
        report_contract = report_source_contract_for_collection(
            repo_root,
            parent_config,
            document_config,
        )
        incoming_report = parse_report_source(
            incoming_body,
            front_matter={},
            source_name="Docs Import markdown preview",
            contract=report_contract,
        )
        if incoming_report is not None:
            raise ValueError("Docs Import cannot create report-host configuration")
    if operation == IMPORT_DOCUMENT_CREATE:
        if bool(create_doc_id) != bool(create_added_date):
            raise ValueError("planned create identity requires both doc_id and added_date")
        added_date = create_added_date or current_doc_timestamp()
        unavailable = {identity for doc in docs for identity in (doc.doc_id, doc.path.stem)}
        local_doc_id = create_doc_id or allocate_doc_id(added_date, unavailable)
        if not is_immutable_doc_id(local_doc_id):
            raise ValueError("new local document identity must use the immutable document ID format")
        if not doc_id_matches_added_date(local_doc_id, added_date):
            raise ValueError("new local document identity timestamp must match added_date")
        if local_doc_id in unavailable:
            raise ValueError(f"cannot create existing import target {local_doc_id!r}")
        source_doc_id = record.doc_id
        provenance = copy.deepcopy(record.provenance)
        if source_doc_id != local_doc_id:
            provenance["source_doc_id"] = source_doc_id
        record = replace(record, doc_id=local_doc_id, provenance=provenance)
        preview["source_doc_id"] = source_doc_id
        preview["proposed_doc_id"] = local_doc_id
        preview["proposed_doc_id_source"] = "allocated-local-identity"
        preview["planned_added_date"] = added_date
    else:
        added_date = ""

    explicit_front_matter = _explicit_front_matter(record)
    title = _clean_text(record.title)
    if operation == IMPORT_DOCUMENT_CREATE:
        target_path = create_root / f"{record.doc_id}.md"
        if any(doc.doc_id == record.doc_id or doc.path.stem == record.doc_id for doc in docs):
            raise ValueError(f"cannot create existing import target {record.doc_id!r}")
        if target_path.exists():
            raise ValueError(f"cannot create existing import target {record.doc_id!r}")
        source_text, parent_id = _create_source(
            record,
            collection_id,
            preview,
            explicit_front_matter,
            added_date,
        )
    else:
        assert target is not None
        target_path = target.path
        source_text, parent_id = _overwrite_source(
            record,
            target,
            preview,
            explicit_front_matter,
            collection=collection_id,
            preserve_collection_metadata=preserve_collection_metadata,
        )

    front_matter, candidate_body = parse_source_text(source_text)
    if collection_supports_draft(document_config) and operation == IMPORT_DOCUMENT_CREATE:
        front_matter["draft"] = True
        source_text = format_source(front_matter, candidate_body, collection=collection_id)
    validate_document_status_front_matter(
        front_matter, collection_config=document_config, source_name=target_path.name,
    )
    committed = committed_document_record(front_matter, record.doc_id, document_config, collection=collection_id, parent_id=parent_id)
    return ImportDocumentPlan(
        operation=operation,
        record=record,
        target_path=target_path,
        source_text=source_text,
        title=title,
        parent_id=parent_id,
        import_preview=preview,
        inline_media_bytes=media_preparation.inline_bytes if media_preparation is not None else {},
        committed_record=committed,
        index_order_path=index_order_path(parent_config) if operation == IMPORT_DOCUMENT_CREATE and not collection_id else None,
        document_config=document_config,
        prepared_document=SourceDoc(
            path=target_path, source_text=source_text, front_matter=front_matter,
            body=candidate_body, doc_id=record.doc_id, title=title,
            ui_status=front_matter.get("ui_status", ""), parent_id=parent_id,
            has_thumbnail=committed.get("has_thumbnail", False),
            report=parse_collection_document_report(
                repo_root, parent_config, document_config, source_text,
                front_matter=front_matter, body=candidate_body, source_name=target_path.name,
            ),
        ),
        collection=collection_id,
        target=target,
        media_change=compare_document_media(
            document_config, record.doc_id, previous_body=target.body, body=candidate_body,
        ) if target is not None else None,
    )


def apply_import_document(
    repo_root: Path,
    plan: ImportDocumentPlan,
    *,
    media_context: ImportDocumentMediaContext | None = None,
) -> ImportDocumentApplyResult:
    """Materialize planned media and atomically write one planned source file."""

    apply_result = materialize_import_document_media(
        repo_root,
        plan,
        media_context=media_context,
    )
    tree = apply_import_document_source(plan)
    return replace(apply_result, parent_ids=tree_parent_ids(tree) if tree is not None else None)


def materialize_import_document_media(
    repo_root: Path,
    plan: ImportDocumentPlan,
    *,
    media_context: ImportDocumentMediaContext | None = None,
) -> ImportDocumentApplyResult:
    """Materialize only one planned document's media and return safe write summaries."""

    inline_media_written: list[dict[str, Any]] = []
    interactive_html_written: list[dict[str, Any]] = []
    if media_context is not None:
        inline_media_written = materialize_import_media(
            repo_root,
            staging_root=media_context.staging_root,
            source_path=media_context.source_path,
            import_preview=plan.import_preview,
            inline_bytes=plan.inline_media_bytes,
            config=plan.document_config,
        )
        interactive_html_written = materialize_interactive_html_assets(
            repo_root,
            media_context.staging_root,
            list(media_context.interactive_html_plans),
            config=plan.document_config,
            allow_overwrite=media_context.allow_interactive_html_overwrite,
        )
    return ImportDocumentApplyResult(
        inline_media_written=tuple(inline_media_written),
        interactive_html_written=tuple(interactive_html_written),
    )


def apply_import_document_source(plan: ImportDocumentPlan) -> list[dict[str, Any]] | None:
    """Write exact source and return its completed ordinary tree when inserted."""

    if plan.operation == IMPORT_DOCUMENT_CREATE:
        tree = None
        if plan.index_order_path is not None:
            tree = read_index_order(plan.index_order_path)
            insert_node(tree, {"doc_id": plan.doc_id}, plan.parent_id, "inside")
        write_text_atomic_new(plan.target_path, plan.source_text)
        if tree is not None:
            write_text_atomic(plan.index_order_path, index_order_text(tree))
            return tree
    elif plan.target is not None and plan.source_text != plan.target.source_text:
        write_text_atomic(plan.target_path, plan.source_text)
    return None


def import_document_event(
    repo_root: Path,
    plan: ImportDocumentPlan,
    source_label: str,
    *,
    include_prompt_meta: bool,
) -> tuple[str, dict[str, Any]]:
    """Return the current per-document operation event name and details."""

    return (
        plan.event_name,
        {
            "staged_filename": source_label,
            "source_format": plan.import_preview.get("source_format"),
            "inline_media_count": len(plan.import_preview.get("media_plans") or []),
            "interactive_html_asset_count": len(
                plan.import_preview.get("interactive_html_plans") or []
            ),
            "doc_id": plan.doc_id,
            "path": relative_path(repo_root, plan.target_path),
            "include_prompt_meta": include_prompt_meta,
            **({"collection": plan.collection} if plan.collection else {}),
        },
    )


def import_document_result(
    repo_root: Path,
    plan: ImportDocumentPlan,
    *,
    source_label: str,
    apply_result: ImportDocumentApplyResult,
    rebuild: dict[str, Any] | None,
    dry_run: bool,
) -> dict[str, Any]:
    """Shape the shared successful per-document import result."""

    inline_media_written = list(apply_result.inline_media_written)
    interactive_html_written = list(apply_result.interactive_html_written)
    target = {"doc_id": plan.doc_id}
    if plan.collection:
        target["collection"] = plan.collection
    record = dict(plan.committed_record)
    result = {
        "operation": plan.operation,
        "doc_id": plan.doc_id,
        "path": relative_path(repo_root, plan.target_path),
        "title": plan.title,
        "target": target,
        "record": record,
        "inline_media_written": inline_media_written,
        "interactive_html_written": interactive_html_written,
        "rebuild": rebuild,
        "summary_text": import_summary_text(
            plan.operation,
            plan.doc_id,
            source_label,
            interactive_html_written,
        ),
        "dry_run": dry_run,
    }
    if plan.collection:
        result["collection"] = plan.collection
    else:
        result["viewer_url"] = viewer_url_for(plan.doc_id)
    return result


__all__ = [
    "ALLOWED_IMPORT_FRONT_MATTER_FIELDS",
    "IMPORT_DOCUMENT_CREATE",
    "IMPORT_DOCUMENT_OPERATIONS",
    "IMPORT_DOCUMENT_OVERWRITE",
    "ImportDocumentApplyResult",
    "ImportDocumentMediaContext",
    "ImportDocumentPlan",
    "apply_import_document",
    "apply_import_document_source",
    "import_document_event",
    "import_document_result",
    "materialize_import_document_media",
    "plan_import_document",
]
