#!/usr/bin/env python3
"""Shared per-document planning and apply helpers for Docs Import."""

from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from docs_import_content import (
    CONTENT_INTENT_EMPTY_NEW,
    CONTENT_INTENT_PRESERVE_EXISTING,
    CONTENT_INTENT_REPLACE,
    ImportContent,
)
from docs_import_media import materialize_inline_raster_media
from docs_import_source_helpers import import_summary_text, relative_path, viewer_url_for
from docs_import_source_interactive import materialize_interactive_html_assets
from docs_management_mutations import metadata_search_doc_ids
from docs_source_model import (
    ScopeDoc,
    advance_doc_front_matter,
    advance_front_matter_for_recent_edit,
    allocate_doc_id,
    current_doc_timestamp,
    default_viewable_for_scope,
    doc_id_matches_added_date,
    format_source,
    is_immutable_doc_id,
    normalize_scope,
    scope_root,
    slugify,
    write_text_atomic,
)


IMPORT_DOCUMENT_CREATE = "create"
IMPORT_DOCUMENT_OVERWRITE = "overwrite"
IMPORT_DOCUMENT_OPERATIONS = {IMPORT_DOCUMENT_CREATE, IMPORT_DOCUMENT_OVERWRITE}

ALLOWED_IMPORT_FRONT_MATTER_FIELDS = ("title", "parent_id", "summary", "viewable")


@dataclass(frozen=True)
class ImportDocumentMediaContext:
    """Staged-source inputs required to materialize one document's media."""

    staging_root: Path
    workspace_root: Path
    source_path: Path
    include_prompt_meta: bool = False
    interactive_html_plans: tuple[dict[str, Any], ...] = ()
    allow_interactive_html_overwrite: bool = False
    source_markdown: str = ""


@dataclass(frozen=True)
class ImportDocumentPlan:
    """Validated source and asset plan for one normalized import record."""

    scope: str
    operation: str
    record: ImportContent
    target_path: Path
    source_text: str
    title: str
    parent_id: str
    viewable: bool
    search_doc_ids: tuple[str, ...]
    import_preview: dict[str, Any]
    target: ScopeDoc | None = None

    @property
    def doc_id(self) -> str:
        return self.record.doc_id

    @property
    def suppression_reason(self) -> str:
        return f"docs-import-source-{self.operation}"

    @property
    def docs_doc_ids(self) -> list[str]:
        return [self.doc_id]

    @property
    def changed_paths(self) -> list[Path]:
        return [self.target_path]


@dataclass(frozen=True)
class ImportDocumentApplyResult:
    inline_media_written: tuple[dict[str, Any], ...] = ()
    interactive_html_written: tuple[dict[str, Any], ...] = ()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _explicit_front_matter(record: ImportContent) -> dict[str, Any]:
    front_matter = {
        field: copy.deepcopy(record.front_matter[field])
        for field in ALLOWED_IMPORT_FRONT_MATTER_FIELDS
        if field in record.front_matter
    }
    for field in ("title", "parent_id", "summary"):
        if field in front_matter and not isinstance(front_matter[field], str):
            raise ValueError(f"ImportContent front_matter {field} must be a string")
    if "viewable" in front_matter and not isinstance(front_matter["viewable"], bool):
        raise ValueError("ImportContent front_matter viewable must be a boolean")
    if "title" in front_matter and _clean_text(front_matter["title"]) != _clean_text(record.title):
        raise ValueError("ImportContent title must match front_matter title")
    declared_parent_id = _clean_text(front_matter.get("parent_id"))
    if "parent_id" in front_matter and declared_parent_id != _clean_text(record.parent_id):
        raise ValueError("ImportContent parent_id must match front_matter parent_id")
    return front_matter


def _viewable_value(front_matter: dict[str, Any], default: bool) -> bool:
    if "viewable" not in front_matter:
        return default
    value = front_matter["viewable"]
    if isinstance(value, bool):
        return value
    return _clean_text(value).lower() not in {"false", "0", "no", "off"}


def _replacement_body(import_preview: dict[str, Any], title: str) -> str:
    markdown = _clean_text(import_preview.get("markdown_preview"))
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
    if "parent_id" in explicit_front_matter:
        front_matter["parent_id"] = _clean_text(explicit_front_matter.get("parent_id"))
    if "viewable" in explicit_front_matter:
        if _viewable_value(explicit_front_matter, True):
            front_matter.pop("viewable", None)
        else:
            front_matter["viewable"] = False


def _create_source(
    record: ImportContent,
    scope: str,
    import_preview: dict[str, Any],
    explicit_front_matter: dict[str, Any],
    added_date: str,
) -> tuple[str, str, bool]:
    if record.content_intent == CONTENT_INTENT_PRESERVE_EXISTING:
        raise ValueError("preserve-existing content requires an existing import target")
    parent_id = _clean_text(record.parent_id)
    default_viewable = default_viewable_for_scope(scope)
    front_matter: dict[str, Any] = advance_doc_front_matter({
        "doc_id": record.doc_id,
        "title": record.title,
        "added_date": added_date,
        "parent_id": parent_id,
    }, timestamp=added_date)
    if not default_viewable:
        front_matter["viewable"] = False
    _apply_explicit_front_matter(front_matter, explicit_front_matter)
    viewable = _viewable_value(front_matter, True)
    body = (
        _replacement_body(import_preview, record.title)
        if record.content_intent == CONTENT_INTENT_REPLACE
        else ""
    )
    return format_source(front_matter, body), parent_id, viewable


def _overwrite_source(
    record: ImportContent,
    target: ScopeDoc,
    import_preview: dict[str, Any],
    explicit_front_matter: dict[str, Any],
) -> tuple[str, str, bool]:
    if record.content_intent == CONTENT_INTENT_EMPTY_NEW:
        raise ValueError("empty-new content cannot overwrite an existing import target")
    front_matter = dict(target.front_matter)
    front_matter["doc_id"] = target.doc_id
    front_matter["title"] = record.title

    if record.content_intent == CONTENT_INTENT_REPLACE:
        # Retain the ordinary single-source overwrite cleanup contract.
        front_matter["parent_id"] = target.parent_id
        front_matter.pop("sort_order", None)
        front_matter.pop("viewable", None)
        if not target.viewable:
            front_matter["viewable"] = False

    _apply_explicit_front_matter(front_matter, explicit_front_matter)
    parent_id = _clean_text(front_matter.get("parent_id"))
    viewable = _viewable_value(front_matter, True)
    body = (
        _replacement_body(import_preview, record.title)
        if record.content_intent == CONTENT_INTENT_REPLACE
        else target.body
    )
    candidate_source = format_source(front_matter, body)
    if candidate_source == target.source_text:
        return target.source_text, parent_id, viewable
    front_matter = advance_front_matter_for_recent_edit(
        target.front_matter,
        target.body,
        front_matter,
        body,
    )
    return format_source(front_matter, body), parent_id, viewable


def plan_import_document(
    repo_root: Path,
    scope: str,
    record: ImportContent,
    *,
    operation: str,
    docs: list[ScopeDoc],
    target: ScopeDoc | None = None,
    import_preview: dict[str, Any] | None = None,
    create_doc_id: str = "",
    create_added_date: str = "",
) -> ImportDocumentPlan:
    """Validate and plan one create or overwrite without writing."""

    normalized_scope = normalize_scope(scope)
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
    if record.content_intent == CONTENT_INTENT_REPLACE and not isinstance(import_preview, dict):
        raise ValueError("replace content requires a normalized import preview")

    preview = copy.deepcopy(import_preview or {})
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
        target_path = scope_root(repo_root, normalized_scope) / f"{record.doc_id}.md"
        if any(doc.doc_id == record.doc_id or doc.path.stem == record.doc_id for doc in docs):
            raise ValueError(f"cannot create existing import target {record.doc_id!r}")
        if target_path.exists():
            raise ValueError(f"cannot create existing import target {record.doc_id!r}")
        source_text, parent_id, viewable = _create_source(
            record,
            normalized_scope,
            preview,
            explicit_front_matter,
            added_date,
        )
        search_doc_ids = (record.doc_id,)
    else:
        assert target is not None
        target_path = target.path
        source_text, parent_id, viewable = _overwrite_source(
            record,
            target,
            preview,
            explicit_front_matter,
        )
        search_doc_ids = tuple(
            metadata_search_doc_ids(
                docs,
                target.doc_id,
                title_changed=title != target.title,
            )
        )

    return ImportDocumentPlan(
        scope=normalized_scope,
        operation=operation,
        record=record,
        target_path=target_path,
        source_text=source_text,
        title=title,
        parent_id=parent_id,
        viewable=viewable,
        search_doc_ids=search_doc_ids,
        import_preview=preview,
        target=target,
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
    apply_import_document_source(plan)
    return apply_result


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
        inline_media_written = materialize_inline_raster_media(
            repo_root,
            staging_root=media_context.staging_root,
            workspace_root=media_context.workspace_root,
            source_path=media_context.source_path,
            import_preview=plan.import_preview,
            include_prompt_meta=media_context.include_prompt_meta,
            source_markdown=media_context.source_markdown,
        )
        interactive_html_written = materialize_interactive_html_assets(
            repo_root,
            media_context.staging_root,
            list(media_context.interactive_html_plans),
            allow_overwrite=media_context.allow_interactive_html_overwrite,
        )
    return ImportDocumentApplyResult(
        inline_media_written=tuple(inline_media_written),
        interactive_html_written=tuple(interactive_html_written),
    )


def apply_import_document_source(plan: ImportDocumentPlan) -> None:
    """Atomically write only one already-validated planned source."""

    if plan.target is None or plan.source_text != plan.target.source_text:
        write_text_atomic(plan.target_path, plan.source_text)


def import_document_activity(
    repo_root: Path,
    plan: ImportDocumentPlan,
    source_label: str,
    *,
    include_prompt_meta: bool,
) -> tuple[str, dict[str, Any]]:
    """Return the current per-document activity event name and details."""

    return (
        plan.suppression_reason,
        {
            "scope": plan.scope,
            "staged_filename": source_label,
            "source_format": plan.import_preview.get("source_format"),
            "inline_media_count": len(plan.import_preview.get("media_plans") or []),
            "interactive_html_asset_count": len(
                plan.import_preview.get("interactive_html_plans") or []
            ),
            "doc_id": plan.doc_id,
            "path": relative_path(repo_root, plan.target_path),
            "include_prompt_meta": include_prompt_meta,
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
    return {
        "operation": plan.operation,
        "doc_id": plan.doc_id,
        "path": relative_path(repo_root, plan.target_path),
        "viewer_url": viewer_url_for(plan.scope, plan.doc_id),
        "title": plan.title,
        "record": {
            "doc_id": plan.doc_id,
            "title": plan.title,
            "parent_id": plan.parent_id,
            "viewable": plan.viewable,
        },
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
    "import_document_activity",
    "import_document_result",
    "materialize_import_document_media",
    "plan_import_document",
]
