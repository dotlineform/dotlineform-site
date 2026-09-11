"""Replace the read-only Pre-publish derivative from one Working source snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_scope_config import load_docs_scope_stage, document_source_path, resolve_scope_path
from docs_scope_publish import _files_from_root, _lifecycle_root, files_revision
from docs_source_model import ScopeDoc, format_source, load_document_collection_docs_for_config
from docs_write_rebuild import rebuild_scope_outputs
from docs_document_subjects import AUTHORING_SUBJECT_FIELDS, SUBJECT_KIND_BY_FIELD, project_reader_subject


def excluded_documents(docs: list[ScopeDoc], *, ordinary: bool) -> set[str]:
    """Apply readiness and intent, then exclude descendants in the same collection."""
    excluded = {
        doc.doc_id for doc in docs
        if not doc.publishable or doc.front_matter.get("draft", True) is True
        or (ordinary and doc.report is not None and doc.report.access == "local"
            and doc.report.id != "docs_subscope")
    }
    while True:
        descendants = {doc.doc_id for doc in docs if doc.parent_id in excluded}
        if descendants <= excluded:
            return excluded
        excluded.update(descendants)


def promoted_source(doc: ScopeDoc) -> bytes:
    front_matter = dict(doc.front_matter)
    subject = project_reader_subject(front_matter)
    for field in ("draft", "publishable", *AUTHORING_SUBJECT_FIELDS):
        front_matter.pop(field, None)
    if subject is not None:
        field = next(field for field, kind in SUBJECT_KIND_BY_FIELD.items() if kind == subject["kind"])
        front_matter[field] = subject["key"]
    body = doc.body
    if doc.report is not None and doc.report.access == "local":
        span = doc.report.source_range
        declaration = body[span.start:span.end]
        replacement = (
            declaration.replace("access: local", "access: public")
            if doc.report.id == "docs_subscope" else ""
        )
        body = body[:span.start] + replacement + body[span.end:]

    return format_source(front_matter, body).encode("utf-8")


def _plan(repo_root: Path, body: dict[str, Any]) -> tuple[dict[str, Any], dict[Path, bytes]]:
    if body.get("scope") != "analysis" or body.get("stage") != "working":
        raise ValueError("Pre-publish requires Analysis Working")
    working = load_docs_scope_stage(repo_root, "analysis", "working")
    target = load_docs_scope_stage(repo_root, "analysis", "pre-publish")
    if {child.sub_scope for child in working.sub_scopes} != {child.sub_scope for child in target.sub_scopes}:
        raise ValueError("Working and Pre-publish must configure the same collections")
    source_root = _lifecycle_root(repo_root, working, "source")
    target_root = _lifecycle_root(repo_root, target, "source")
    generated_root = _lifecycle_root(repo_root, target, "generated")
    source_files = _files_from_root(source_root)
    source_revision = files_revision(source_files)
    ordinary = load_document_collection_docs_for_config(repo_root, working, working)
    excluded = excluded_documents(ordinary, ordinary=True)
    hosts: dict[str, list[str]] = {}
    for doc in ordinary:
        if doc.report is not None and doc.report.id == "docs_subscope":
            hosts.setdefault(str(doc.report.sub_scope), []).append(doc.doc_id)
    desired: dict[Path, bytes] = {}
    counts: dict[str, int] = {}
    eligible: list[str] = []
    for collection in (working, *working.sub_scopes):
        child = str(getattr(collection, "sub_scope", ""))
        docs = ordinary if not child else load_document_collection_docs_for_config(repo_root, working, collection)
        rejected = excluded_documents(docs, ordinary=not child)
        if child:
            report_hosts = hosts.get(child, [])
            if len(report_hosts) != 1:
                raise ValueError(f"Pre-publish requires exactly one report host for {child}")
            if report_hosts[0] in excluded:
                rejected.update(doc.doc_id for doc in docs)
        excluded.update(rejected)
        accepted = [doc for doc in docs if doc.doc_id not in rejected]
        counts[child or "documents"] = len(accepted)
        eligible.extend(doc.doc_id for doc in accepted)
        for doc in accepted:
            desired[doc.path.relative_to(source_root)] = promoted_source(doc)
        # Media is a collection-owned input. The ordinary Build resolves its outputs.
        prefix = Path("sub-scopes") / child / "media" if child else Path("media")
        if accepted:
            desired.update({path: data for path, data in source_files.items() if path.is_relative_to(prefix)})
    if target.default_doc_id not in eligible:
        raise ValueError("The Pre-publish default document is excluded; choose a ready, publishable default")
    if files_revision(_files_from_root(source_root)) != source_revision:
        raise ValueError("Working changed during Pre-publish planning; try again")
    current_revision = files_revision(_files_from_root(target_root))
    generated_revision = files_revision(_files_from_root(generated_root))
    target_revision = files_revision(desired)
    plan_revision = files_revision({
        Path("working"): source_revision.encode(),
        Path("current-source"): current_revision.encode(),
        Path("current-generated"): generated_revision.encode(),
        Path("target"): target_revision.encode(),
    })
    return {
        "ok": True, "scope": "analysis", "stage": "working",
        "plan_revision": plan_revision, "source_revision": source_revision,
        "target_source_revision": target_revision,
        "document_count": len(eligible), "excluded_document_count": len(excluded),
        "collections": counts, "eligible_doc_ids": sorted(eligible),
        "excluded_doc_ids": sorted(excluded),
        "summary_text": f"Prepare {len(eligible)} documents; omit {len(excluded)} draft, excluded or local documents and their descendants.",
    }, desired


def preview_pre_publish(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    preview, _files = _plan(repo_root, body)
    return preview


def apply_pre_publish(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to replace Pre-publish")
    preview, desired = _plan(repo_root, body)
    if body.get("plan_revision") != preview["plan_revision"]:
        raise ValueError("Pre-publish preview is stale; preview again")
    config = load_docs_scope_stage(repo_root, "analysis", "pre-publish")
    source_root = _lifecycle_root(repo_root, config, "source")
    generated_root = _lifecycle_root(repo_root, config, "generated")
    # These are replaceable derivatives. Invalidate completion before any write;
    # a failed build remains visibly incomplete and is recovered by Pre-publish.
    for relative in _files_from_root(generated_root):
        (generated_root / relative).unlink()
    for relative in _files_from_root(source_root):
        if relative not in desired:
            (source_root / relative).unlink()
    for relative, data in desired.items():
        path = source_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for collection in (config, *config.sub_scopes):
        documents = resolve_scope_path(repo_root, document_source_path(collection))
        documents.mkdir(parents=True, exist_ok=True)
        for media_type in ("img", "svg", "files", "html", "build-source/mermaid"):
            (documents.parent / "media" / media_type).mkdir(parents=True, exist_ok=True)
    if files_revision(_files_from_root(source_root)) != preview["target_source_revision"]:
        raise RuntimeError("Pre-publish source snapshot did not verify")
    build = rebuild_scope_outputs(repo_root, "analysis", stage="pre-publish", include_search=True)
    return {
        **preview, "applied": True, "build": build,
        "summary_text": f"Pre-publish rebuilt: {preview['document_count']} documents and Search. Review Pre-publish before Publish.",
    }
