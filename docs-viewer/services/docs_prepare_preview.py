"""Prepare one read-only Preview snapshot from captured eligible Working content."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import json
import subprocess
import sys
import tempfile

from docs_workspace_config import (
    CONFIG_REL_PATH, DocsStageConfig, DocsWorkspaceConfig, load_docs_workspace_config, select_workspace_stage,
    document_source_path, generated_documents_path, generated_search_path, safe_relative_path,
)
from docs_preview_snapshot import (
    CompletedPreview,
    _files_from_root, _lifecycle_root, _validate_generated_manifest, files_revision,
    build_preview_snapshot_files, write_preview_snapshot,
)
from docs_source_model import SourceDoc, format_source, load_document_collection_docs_for_config, write_bytes_atomic
from docs_document_identity import doc_updated_date
from docs_index_order import exclude_nodes, index_order_path, index_order_text, read_index_order
from docs_collection_customisations import prepare_collection_publication
from docs_publication_ignore import read_publication_ignore_ids
from docs_build_manifest import remove_build_manifest
from docs_recent_exclusions import parse_recent_exclusions, recent_exclusions_path
from docs_recent_payload import build_recent_payload
from docs_selected_documents import read_selected, selected_path, selected_row, selected_text
from docs_catalogue_artifacts import (
    CONFIG_REL_PATH as CATALOGUE_CONFIG_REL_PATH, load_catalogue_artifact_inventory,
    read_catalogue_artifacts, select_catalogue_artifacts,
)


@dataclass(frozen=True)
class PreparationInputs:
    """Inputs captured once for the synchronous preparation operation."""

    workspace: DocsWorkspaceConfig
    working: DocsStageConfig
    recent_limit: int
    source_files: dict[Path, bytes]
    search_index: bytes
    catalogue: dict[str, bytes]
    related_links: dict[Path, bytes]
    preview_files: dict[Path, bytes]
    revision_basis: dict[Path, bytes]


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
        return doc.source_text.encode("utf-8")
    return format_source(front_matter, doc.body).encode("utf-8")


def _capture_inputs(repo_root: Path, workspace: DocsWorkspaceConfig, catalogue_selection: dict[str, list[str]]) -> PreparationInputs:
    configuration = {
        Path("configuration"): (repo_root / CONFIG_REL_PATH).read_bytes(),
        Path("catalogue-inventory"): (repo_root / CATALOGUE_CONFIG_REL_PATH).read_bytes(),
    }
    working = select_workspace_stage(workspace, "working")
    search_path = generated_search_path(working)
    if search_path.is_symlink() or not search_path.is_file():
        raise FileNotFoundError("Working Search index is unavailable; rebuild Search in Working before preparing Preview")
    search_index = search_path.read_bytes()
    links_root = generated_documents_path(working) / "links-by-id"
    if links_root.is_symlink():
        raise ValueError("Working related-links inputs must not be a symlink")
    related_links = _files_from_root(links_root) if links_root.exists() else {}
    source_root = _lifecycle_root(repo_root, working, "source")
    source_files = _files_from_root(source_root)
    preview_root = working.workspace_root.path / "preview"
    if preview_root.is_symlink() or (preview_root.exists() and not preview_root.is_dir()):
        raise ValueError("Preview root must be a directory without symlinks")
    current = _files_from_root(preview_root) if preview_root.is_dir() else {}
    inventory = load_catalogue_artifact_inventory(repo_root)
    catalogue_prefix = workspace.catalogue.preview.path.relative_to(preview_root)
    catalogue = {
        path.relative_to(catalogue_prefix).as_posix(): data for path, data in current.items()
        if path.is_relative_to(catalogue_prefix)
    }
    identities = {safe_relative_path(name, field="Catalogue shared output") for name in catalogue_selection["shared_outputs"]}
    identities.update(safe_relative_path(f"galleries/index/{gid}.json", field="Catalogue Gallery path") for gid in catalogue_selection["current_galleries"])
    catalogue.update(read_catalogue_artifacts(workspace.catalogue, inventory, stage="working", identities=identities))
    for gallery_id in catalogue_selection["deleted_galleries"]:
        identity = safe_relative_path(f"galleries/index/{gallery_id}.json", field="Catalogue Gallery path")
        catalogue.pop(identity.as_posix(), None)
    catalogue = select_catalogue_artifacts(catalogue, inventory)
    basis = {
        **configuration,
        Path("working"): files_revision(source_files).encode(),
        Path("preview"): files_revision(current).encode(),
        Path("working-search"): search_index,
        **{Path("working-links") / path: data for path, data in related_links.items()},
        **{Path("catalogue") / path: data for path, data in catalogue.items()},
    }
    return PreparationInputs(workspace, working, workspace.recent_limit, source_files, search_index, catalogue, related_links, current, basis)


def _plan(repo_root: Path, workspace: DocsWorkspaceConfig, catalogue_selection: dict[str, list[str]]) -> tuple[dict[str, Any], dict[Path, bytes], PreparationInputs, bytes]:
    inputs = _capture_inputs(repo_root, workspace, catalogue_selection)
    working, source_files = inputs.working, inputs.source_files
    source_revision = inputs.revision_basis[Path("working")].decode()
    source_root = _lifecycle_root(repo_root, working, "source")
    exclusions_file = recent_exclusions_path(working).relative_to(source_root)
    if exclusions_file not in source_files:
        raise FileNotFoundError("Working recent-exclusions.json is unavailable")
    recent_exclusions = parse_recent_exclusions(source_files[exclusions_file], working)
    ordinary = load_document_collection_docs_for_config(repo_root, working, working)
    ordinary_excluded = excluded_documents(ordinary, ignored_ids=read_publication_ignore_ids(repo_root, config=working))
    excluded = set(ordinary_excluded)
    order_path = index_order_path(working)
    desired: dict[Path, bytes] = {
        order_path.relative_to(source_root): index_order_text(
            exclude_nodes(read_index_order(order_path), ordinary_excluded)
        ).encode("utf-8"),
    }
    counts: dict[str, int] = {}
    eligible: list[str] = []
    selected = read_selected(working)
    selected_targets = {(row.get("collection", ""), row["doc_id"]) for row in selected["docs"]}
    selected_rows = []
    recent_candidates = []
    for collection in (working, *working.collections):
        child = str(getattr(collection, "collection", ""))
        docs = ordinary if not child else load_document_collection_docs_for_config(repo_root, working, collection)
        if child == "catalogue":
            rejected = set()
        elif child:
            rejected = excluded_documents(docs)
        else:
            rejected = set(ordinary_excluded)
        if child and collection.report_host_doc_id in ordinary_excluded:
            rejected.update(doc.doc_id for doc in docs)
        excluded.update(rejected)
        accepted = [doc for doc in docs if doc.doc_id not in rejected]
        if not child or collection.include_in_site_search:
            titles = {doc.doc_id: doc.title for doc in accepted}
            for doc in accepted:
                row = {
                    "doc_id": doc.doc_id, "title": doc.title,
                    "last_updated": doc_updated_date(doc.front_matter.get("last_updated", "")),
                }
                if child:
                    row.update(collection=child, report_doc_id=collection.report_host_doc_id, collection_title=collection.title)
                elif doc.parent_id in titles:
                    row.update(parent_id=doc.parent_id, parent_title=titles[doc.parent_id])
                recent_candidates.append(row)
        counts[child or "documents"] = len(accepted)
        eligible.extend(doc.doc_id for doc in accepted)
        for doc in accepted:
            desired[doc.path.relative_to(source_root)] = promoted_source(doc, collection)
            if (child, doc.doc_id) in selected_targets:
                selected_rows.append(selected_row(doc, collection))
        prefix = Path("collections") / child / "media" if child else Path("media")
        if accepted and collection.media is not None:
            desired.update({path: data for path, data in source_files.items() if path.is_relative_to(prefix / "build-source") or path == prefix / "media-source-evidence.json"})
    desired[selected_path(working).relative_to(source_root)] = selected_text({**selected, "docs": selected_rows}).encode("utf-8")
    recent = build_recent_payload(
        recent_candidates, limit=inputs.recent_limit,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), exclusions=recent_exclusions,
    )
    recent_payload = (json.dumps(recent, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    plan_revision = files_revision({
        **inputs.revision_basis,
        Path("prepared-source"): files_revision(desired).encode(),
        Path("prepared-recent"): recent_payload,
    })
    return {
        "ok": True, "stage": "working", "plan_revision": plan_revision,
        "source_revision": source_revision, "document_count": len(eligible),
        "excluded_document_count": len(excluded), "collections": counts,
        "eligible_doc_ids": sorted(eligible), "excluded_doc_ids": sorted(excluded),
        "catalogue_file_count": len(inputs.catalogue),
        "summary_text": f"Prepare Preview with {len(eligible)} documents and {len(inputs.catalogue)} Catalogue JSON files.",
    }, desired, inputs, recent_payload


def build_captured_preview(
    repo_root: Path, source_files: dict[Path, bytes], search_index: bytes, recent_payload: bytes,
    catalogue: dict[str, bytes],
    related_links: dict[Path, bytes], eligible_doc_ids: list[str],
    retained_preview: dict[Path, bytes],
    *, workspace: DocsWorkspaceConfig,
) -> tuple[dict[Path, bytes], dict[str, Any], dict[str, bytes]]:
    """Build captured inputs in temporary storage without replacing live Preview."""
    build_parent = repo_root / "var"
    build_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="preview-build-", dir=build_parent) as directory:
        build_root = Path(directory)
        working_assets = workspace.assets.for_stage("working").root.path
        work_assets = workspace.assets.for_stage("preview").work_root.path
        captured_workspace = load_docs_workspace_config(repo_root, docs_base_dir=build_root,
                                                      assets_base_dir=working_assets, work_assets_base_dir=work_assets)
        config = select_workspace_stage(captured_workspace, "preview")
        source_root = config.source.location.path
        generated_root = config.generated.documents.location.path.parent
        captured_search = build_root / "working-search.json"
        captured_search.write_bytes(search_index)
        captured_recent = build_root / "prepared-recent.json"
        captured_recent.write_bytes(recent_payload)
        captured_links = build_root / "related-links"
        captured_links.mkdir()
        eligible = set(eligible_doc_ids)
        catalogue_documents = generated_root / "collections/catalogue/documents"
        catalogue_rows = []
        catalogue_source_prefix = Path("collections/catalogue/documents")
        for relative in sorted(source_files):
            if relative.parent != catalogue_source_prefix or relative.suffix != ".md":
                continue
            document = catalogue_source_prefix / "by-id" / (relative.stem + ".json")
            if document not in retained_preview:
                raise FileNotFoundError(f"Catalogue {relative.stem} has no completed Preview document; Regenerate its refreshed queue or run explicit Catalogue design maintenance")
            data = retained_preview[document]
            payload = json.loads(data)
            target = generated_root / document
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            catalogue_rows.append({"doc_id": payload["doc_id"], "title": payload["title"],
                                   "last_updated": doc_updated_date(payload["last_updated"])})
        catalogue_documents.mkdir(parents=True, exist_ok=True)
        catalogue_rows.sort(key=lambda row: (row["title"].lower(), row["doc_id"]))
        (catalogue_documents / "manifest.json").write_bytes((json.dumps({"docs": catalogue_rows}, indent=2, ensure_ascii=False) + "\n").encode())
        for relative, data in related_links.items():
            if relative.parent != Path(".") or relative.suffix != ".json":
                raise ValueError("Related-links inputs require flat JSON records")
            if relative.stem not in eligible:
                continue
            # Body eligibility selects the owner only; linked destinations keep
            # their captured identities/titles even when their bodies are omitted.
            (captured_links / relative).write_bytes(data)
        for relative, data in source_files.items():
            path = source_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for identity, data in catalogue.items():
            path = captured_workspace.catalogue.preview.path / identity
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for collection in (config, *config.collections):
            documents = document_source_path(collection)
            documents.mkdir(parents=True, exist_ok=True)
            generated_documents_path(collection).mkdir(parents=True, exist_ok=True)
        for collection in (config, *config.media_collections):
            for producer in collection.media.build_sources.values():
                producer.location.path.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [sys.executable, str(repo_root / "docs-viewer/build/build_preview.py"),
             "--docs-base-dir", str(build_root), "--search-index", str(captured_search),
             "--recent-payload", str(captured_recent), "--assets-base-dir", str(working_assets),
             "--work-assets-base-dir", str(work_assets),
             "--related-links-dir", str(captured_links)],
            cwd=repo_root, capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise RuntimeError("Preview build failed: " + (result.stderr or result.stdout).strip())
        build_manifest, generated_files = _validate_generated_manifest(generated_root, "preview")
        files, eligibility, media_files = build_preview_snapshot_files(repo_root, config, generated_files)
        catalogue_prefix = workspace.catalogue.preview.path.relative_to(workspace.workspace_root.path / "preview")
        files.update({catalogue_prefix / identity: data for identity, data in catalogue.items()})
        references = eligibility["asset_references"]
    return files, {**build_manifest, "asset_references": references}, media_files


def _complete_preview(
    repo_root: Path, plan: dict[str, Any], desired: dict[Path, bytes],
    inputs: PreparationInputs, recent_payload: bytes,
    *, on_recent_written: Callable[[], None],
) -> CompletedPreview:
    files, build_manifest, media_files = build_captured_preview(
        repo_root, desired, inputs.search_index, recent_payload, inputs.catalogue,
        inputs.related_links, plan["eligible_doc_ids"],
        inputs.preview_files, workspace=inputs.workspace,
    )
    recent_path = generated_documents_path(inputs.working) / "recent.json"
    if recent_path.is_symlink():
        raise ValueError("Working Recents output must not be a symlink")
    remove_build_manifest(repo_root, inputs.working)
    write_bytes_atomic(recent_path, recent_payload)
    on_recent_written()
    return write_preview_snapshot(
        repo_root, files=files, generated_revision=build_manifest["generated_revision"],
        source_revision=plan["source_revision"], asset_references=build_manifest["asset_references"],
        media_files=media_files,
        current_files=inputs.preview_files,
        config=inputs.workspace,
    )


def prepare_preview(
    repo_root: Path, *, workspace: DocsWorkspaceConfig, catalogue_selection: dict[str, list[str]],
    on_recent_written: Callable[[], None],
) -> CompletedPreview:
    """Capture fresh eligible Working inputs and complete Preview synchronously.

    The synchronous workflow prevents edits while captured inputs are consumed.
    Failure prevents distribution; snapshot replacement retains its receipt semantics.
    Notify the caller immediately after Working Recent persistence, so a later
    failure still carries the browser's required refresh selection.
    """
    return _complete_preview(repo_root, *_plan(repo_root, workspace, catalogue_selection), on_recent_written=on_recent_written)
