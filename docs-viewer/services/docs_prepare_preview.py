"""Prepare one read-only Preview snapshot from captured eligible Working content."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import subprocess
import sys
import tempfile

from docs_workspace_config import (
    CONFIG_REL_PATH, load_docs_stage, load_docs_workspace_config, select_workspace_stage,
    document_source_path, generated_documents_path, generated_search_path,
)
from docs_preview_snapshot import (
    _files_from_root, _lifecycle_root, _validate_generated_manifest, _validate_prepared_index, files_revision,
    build_preview_snapshot_files, write_preview_snapshot,
)
from docs_source_model import SourceDoc, format_source, load_document_collection_docs_for_config
from docs_collection_customisations import prepare_collection_publication
from docs_publication_ignore import read_publication_ignore_ids
from docs_catalogue_artifacts import (
    CONFIG_REL_PATH as CATALOGUE_CONFIG_REL_PATH, load_catalogue_artifact_inventory,
    read_catalogue_artifacts, catalogue_asset_references,
)


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


def _plan(repo_root: Path, body: dict[str, Any]) -> tuple[dict[str, Any], dict[Path, bytes], bytes, bytes, dict[str, bytes]]:
    if body.get("stage") != "working" or "scope" in body:
        raise ValueError("Prepare Preview requires stage working")
    working = load_docs_stage(repo_root, "working")
    search_path = generated_search_path(working)
    if search_path.is_symlink() or not search_path.is_file():
        raise FileNotFoundError("Working Search index is unavailable; rebuild Search in Working before preparing Preview")
    search_index = search_path.read_bytes()
    _validate_prepared_index(Path("search/index.json"), search_index, "working")
    recent_path = generated_documents_path(working) / "recent.json"
    if recent_path.is_symlink() or not recent_path.is_file():
        raise FileNotFoundError("Working Recents is unavailable; run a full Working Build before preparing Preview")
    recent_payload = recent_path.read_bytes()
    _validate_prepared_index(Path("documents/recent.json"), recent_payload, "working")
    workspace = load_docs_workspace_config(repo_root)
    catalogue = read_catalogue_artifacts(workspace.catalogue, load_catalogue_artifact_inventory(repo_root), stage="working")
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
            desired.update({path: data for path, data in source_files.items() if path.is_relative_to(prefix / "build-source") or path == prefix / "media-source-evidence.json"})
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
        Path("working-search"): search_index,
        Path("working-recent"): recent_payload,
        Path("catalogue-inventory"): (repo_root / CATALOGUE_CONFIG_REL_PATH).read_bytes(),
        **{Path("catalogue") / path: data for path, data in catalogue.items()},
    })
    return {
        "ok": True, "stage": "working", "plan_revision": plan_revision,
        "source_revision": source_revision, "document_count": len(eligible),
        "excluded_document_count": len(excluded), "collections": counts,
        "eligible_doc_ids": sorted(eligible), "excluded_doc_ids": sorted(excluded),
        "catalogue_file_count": len(catalogue),
        "summary_text": f"Prepare Preview with {len(eligible)} documents and {len(catalogue)} Catalogue JSON files.",
    }, desired, search_index, recent_payload, catalogue


def plan_prepare_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Bind confirmation to source, saved Search/Recents and current Preview."""
    preview, _files, _search_index, _recent_payload, _catalogue = _plan(repo_root, body)
    return preview


def build_captured_preview(
    repo_root: Path, source_files: dict[Path, bytes], search_index: bytes, recent_payload: bytes,
    catalogue: dict[str, bytes],
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    """Build captured inputs in temporary storage without replacing live Preview."""
    workspace = load_docs_workspace_config(repo_root)
    references = catalogue_asset_references(workspace, catalogue)
    build_parent = repo_root / "var"
    build_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="preview-build-", dir=build_parent) as directory:
        build_root = Path(directory)
        config = select_workspace_stage(load_docs_workspace_config(repo_root, docs_base_dir=build_root, assets_base_dir=workspace.assets.root.path), "preview")
        source_root = config.source.location.path
        generated_root = config.generated.documents.location.path.parent
        captured_search = build_root / "working-search.json"
        captured_search.write_bytes(search_index)
        captured_recent = build_root / "working-recent.json"
        captured_recent.write_bytes(recent_payload)
        for relative, data in source_files.items():
            path = source_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for collection in (config, *config.collections):
            documents = document_source_path(collection)
            documents.mkdir(parents=True, exist_ok=True)
            generated_documents_path(collection).mkdir(parents=True, exist_ok=True)
            for producer in collection.media.build_sources.values():
                producer.location.path.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [sys.executable, str(repo_root / "docs-viewer/build/build_preview.py"),
             "--docs-base-dir", str(build_root), "--search-index", str(captured_search),
             "--recent-payload", str(captured_recent), "--assets-base-dir", str(workspace.assets.root.path)],
            cwd=repo_root, capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise RuntimeError("Preview build failed: " + (result.stderr or result.stdout).strip())
        build_manifest, generated_files = _validate_generated_manifest(generated_root, "preview")
        files, eligibility = build_preview_snapshot_files(repo_root, config, generated_files)
        catalogue_prefix = workspace.catalogue.preview.path.relative_to(workspace.workspace_root.path / "preview")
        files.update({catalogue_prefix / identity: data for identity, data in catalogue.items()})
        references = sorted(set(references) | set(eligibility["asset_references"]))
    return files, {**build_manifest, "asset_references": references}


def apply_prepare_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Build temporary inputs synchronously, then replace the complete Preview."""
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to prepare Preview")
    plan, desired, search_index, recent_payload, catalogue = _plan(repo_root, body)
    if body.get("plan_revision") != plan["plan_revision"]:
        raise ValueError("Prepare Preview plan is stale; preview again")
    files, build_manifest = build_captured_preview(repo_root, desired, search_index, recent_payload, catalogue)
    current = plan_prepare_preview(repo_root, {"stage": "working"})
    if current["plan_revision"] != plan["plan_revision"]:
        raise ValueError("Working source, Catalogue, Search, Recents, configuration or Preview changed during preparation; prepare again")
    manifest = write_preview_snapshot(
        repo_root, files=files, generated_revision=build_manifest["generated_revision"],
        source_revision=plan["source_revision"], asset_references=build_manifest["asset_references"],
    )
    return {
        **plan, "applied": True, "preview_manifest": manifest,
        "summary_text": f"Preview prepared: {plan['document_count']} documents, Catalogue, Search and Recents. Review Preview before Publish.",
    }
