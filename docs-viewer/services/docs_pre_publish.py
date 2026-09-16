"""Replace the read-only Pre-publish derivative from one Working source snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_workspace_config import load_docs_stage, document_source_path, resolve_workspace_path
from docs_publish import _files_from_root, _lifecycle_root, files_revision
from docs_source_model import SourceDoc, format_source, load_document_collection_docs_for_config
from docs_write_rebuild import rebuild_stage_outputs
from docs_collection_customisations import prepare_collection_publication
from docs_publication_ignore import read_publication_ignore_ids


def excluded_documents(docs: list[SourceDoc], *, ignored_ids: frozenset[str] = frozenset()) -> set[str]:
    """Exclude draft and explicitly ignored roots together with their descendants."""
    excluded = {
        doc.doc_id for doc in docs
        if doc.front_matter.get("draft", True) is True or doc.doc_id in ignored_ids
    }
    while True:
        descendants = {doc.doc_id for doc in docs if doc.parent_id in excluded}
        if descendants <= excluded:
            return excluded
        excluded.update(descendants)


def promoted_source(doc: SourceDoc, collection: Any) -> bytes:
    """Retain ordinary source bytes; only the collection owner can project its fields."""
    front_matter = prepare_collection_publication(
        getattr(collection, "collection_customisation", None), doc.front_matter,
    )
    if front_matter == doc.front_matter:
        return doc.path.read_bytes()
    return format_source(front_matter, doc.body).encode("utf-8")


def _plan(repo_root: Path, body: dict[str, Any]) -> tuple[dict[str, Any], dict[Path, bytes]]:
    if body.get("stage") != "working":
        raise ValueError("Pre-publish requires Working")
    if "scope" in body:
        raise ValueError("scope is retired; Pre-publish requires stage working")
    working = load_docs_stage(repo_root, "working")
    target = load_docs_stage(repo_root, "pre-publish")
    if {child.collection for child in working.collections} != {child.collection for child in target.collections}:
        raise ValueError("Working and Pre-publish must configure the same collections")
    source_root = _lifecycle_root(repo_root, working, "source")
    target_root = _lifecycle_root(repo_root, target, "source")
    generated_root = _lifecycle_root(repo_root, target, "generated")
    source_files = _files_from_root(source_root)
    source_revision = files_revision(source_files)
    ordinary = load_document_collection_docs_for_config(repo_root, working, working)
    ignored_ids = read_publication_ignore_ids(repo_root)
    ordinary_excluded = excluded_documents(ordinary, ignored_ids=ignored_ids)
    excluded = set(ordinary_excluded)
    hosts: dict[str, list[str]] = {}
    for doc in ordinary:
        if doc.report is not None and doc.report.id == "docs_collection":
            hosts.setdefault(str(doc.report.collection), []).append(doc.doc_id)
    desired: dict[Path, bytes] = {}
    counts: dict[str, int] = {}
    eligible: list[str] = []
    for collection in (working, *working.collections):
        child = str(getattr(collection, "collection", ""))
        docs = ordinary if not child else load_document_collection_docs_for_config(repo_root, working, collection)
        rejected = excluded_documents(docs) if child else set(ordinary_excluded)
        if child:
            report_hosts = hosts.get(child, [])
            if len(report_hosts) != 1:
                raise ValueError(f"Pre-publish requires exactly one report host for {child}")
            if report_hosts[0] in ordinary_excluded:
                rejected.update(doc.doc_id for doc in docs)
        excluded.update(rejected)
        accepted = [doc for doc in docs if doc.doc_id not in rejected]
        counts[child or "documents"] = len(accepted)
        eligible.extend(doc.doc_id for doc in accepted)
        for doc in accepted:
            desired[doc.path.relative_to(source_root)] = promoted_source(doc, collection)
        # Media is a collection-owned input. The ordinary Build resolves its outputs.
        prefix = Path("collections") / child / "media" if child else Path("media")
        if accepted:
            desired.update({path: data for path, data in source_files.items() if path.is_relative_to(prefix)})
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
        "ok": True, "stage": "working",
        "plan_revision": plan_revision, "source_revision": source_revision,
        "target_source_revision": target_revision,
        "document_count": len(eligible), "excluded_document_count": len(excluded),
        "collections": counts, "eligible_doc_ids": sorted(eligible),
        "excluded_doc_ids": sorted(excluded),
        "summary_text": f"Prepare {len(eligible)} documents; omit {len(excluded)} documents through draft and ignore-list exclusions.",
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
    config = load_docs_stage(repo_root, "pre-publish")
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
    for collection in (config, *config.collections):
        documents = resolve_workspace_path(repo_root, document_source_path(collection))
        documents.mkdir(parents=True, exist_ok=True)
        for media_type in ("img", "svg", "files", "html", "build-source/mermaid"):
            (documents.parent / "media" / media_type).mkdir(parents=True, exist_ok=True)
    if files_revision(_files_from_root(source_root)) != preview["target_source_revision"]:
        raise RuntimeError("Pre-publish source snapshot did not verify")
    build = rebuild_stage_outputs(repo_root, stage="pre-publish", include_search=True)
    return {
        **preview, "applied": True, "build": build,
        "summary_text": f"Pre-publish rebuilt: {preview['document_count']} documents and Search. Review Pre-publish before Publish.",
    }
