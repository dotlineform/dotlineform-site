"""Prepare one read-only Preview snapshot from captured eligible Working content."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import subprocess
import sys
import tempfile

from docs_workspace_config import (
    CONFIG_REL_PATH, load_docs_stage, load_docs_workspace_config, select_workspace_stage,
    document_source_path, generated_documents_path,
)
from docs_preview_snapshot import (
    _files_from_root, _lifecycle_root, _validate_generated_manifest, files_revision,
    build_preview_snapshot_files, write_preview_snapshot,
)
from docs_source_model import SourceDoc, format_source, load_document_collection_docs_for_config
from docs_collection_customisations import prepare_collection_publication
from docs_publication_ignore import read_publication_ignore_ids


def excluded_documents(docs: list[SourceDoc], *, ignored_ids: frozenset[str] = frozenset()) -> set[str]:
    """Exclude draft and explicitly ignored roots together with their descendants."""
    excluded = {
        doc.doc_id for doc in docs
        if doc.front_matter["draft"] or doc.doc_id in ignored_ids
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
    if body.get("stage") != "working" or "scope" in body:
        raise ValueError("Prepare Preview requires stage working")
    working = load_docs_stage(repo_root, "working")
    source_root = _lifecycle_root(repo_root, working, "source")
    source_files = _files_from_root(source_root)
    source_revision = files_revision(source_files)
    ordinary = load_document_collection_docs_for_config(repo_root, working, working)
    ordinary_excluded = excluded_documents(ordinary, ignored_ids=read_publication_ignore_ids(repo_root))
    excluded = set(ordinary_excluded)
    desired: dict[Path, bytes] = {}
    counts: dict[str, int] = {}
    eligible: list[str] = []
    for collection in (working, *working.collections):
        child = str(getattr(collection, "collection", ""))
        docs = ordinary if not child else load_document_collection_docs_for_config(repo_root, working, collection)
        rejected = excluded_documents(docs) if child else set(ordinary_excluded)
        if child and collection.report_host_doc_id in ordinary_excluded:
            rejected.update(doc.doc_id for doc in docs)
        excluded.update(rejected)
        accepted = [doc for doc in docs if doc.doc_id not in rejected]
        counts[child or "documents"] = len(accepted)
        eligible.extend(doc.doc_id for doc in accepted)
        for doc in accepted:
            desired[doc.path.relative_to(source_root)] = promoted_source(doc, collection)
        prefix = Path("collections") / child / "media" if child else Path("media")
        if accepted:
            desired.update({path: data for path, data in source_files.items() if path.is_relative_to(prefix)})
    if files_revision(_files_from_root(source_root)) != source_revision:
        raise ValueError("Working changed during Preview planning; try again")
    preview_root = working.workspace_root.path / "preview"
    if preview_root.is_symlink() or (preview_root.exists() and not preview_root.is_dir()):
        raise ValueError("Preview root must be a directory without symlinks")
    current = _files_from_root(preview_root) if preview_root.is_dir() else {}
    plan_revision = files_revision({
        Path("working"): source_revision.encode(),
        Path("preview"): files_revision(current).encode(),
        Path("configuration"): (repo_root / CONFIG_REL_PATH).read_bytes(),
        Path("prepared-source"): files_revision(desired).encode(),
    })
    return {
        "ok": True, "stage": "working", "plan_revision": plan_revision,
        "source_revision": source_revision, "document_count": len(eligible),
        "excluded_document_count": len(excluded), "collections": counts,
        "eligible_doc_ids": sorted(eligible), "excluded_doc_ids": sorted(excluded),
        "summary_text": f"Prepare Preview with {len(eligible)} documents.",
    }, desired


def plan_prepare_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Describe the captured source selection and bind confirmation to current state."""
    preview, _files = _plan(repo_root, body)
    return preview


def apply_prepare_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Build temporary inputs synchronously, then replace the complete Preview."""
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to prepare Preview")
    plan, desired = _plan(repo_root, body)
    if body.get("plan_revision") != plan["plan_revision"]:
        raise ValueError("Prepare Preview plan is stale; preview again")
    build_parent = repo_root / "var"
    build_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="preview-build-", dir=build_parent) as directory:
        build_root = Path(directory)
        config = select_workspace_stage(load_docs_workspace_config(repo_root, docs_base_dir=build_root), "preview")
        source_root = config.source.location.path
        generated_root = config.generated.documents.location.path.parent
        for relative, data in desired.items():
            path = source_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for collection in (config, *config.collections):
            documents = document_source_path(collection)
            documents.mkdir(parents=True, exist_ok=True)
            generated_documents_path(collection).mkdir(parents=True, exist_ok=True)
            for media_type in ("img", "svg", "files", "html", "build-source/mermaid"):
                (documents.parent / "media" / media_type).mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [sys.executable, str(repo_root / "docs-viewer/build/build_preview.py"), "--docs-base-dir", str(build_root)],
            cwd=repo_root, capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise RuntimeError("Preview build failed: " + (result.stderr or result.stdout).strip())
        build_manifest, generated_files = _validate_generated_manifest(generated_root, "preview")
        files, _eligibility = build_preview_snapshot_files(repo_root, config, generated_files)
        current = plan_prepare_preview(repo_root, {"stage": "working"})
        if current["plan_revision"] != plan["plan_revision"]:
            raise ValueError("Working, configuration or Preview changed during preparation; prepare again")
        manifest = write_preview_snapshot(
            repo_root, files=files, generated_revision=build_manifest["generated_revision"],
            source_revision=plan["source_revision"],
        )
    return {
        **plan, "applied": True, "preview_manifest": manifest,
        "summary_text": f"Preview prepared: {plan['document_count']} documents and Search. Review Preview before Deploy Repo.",
    }
