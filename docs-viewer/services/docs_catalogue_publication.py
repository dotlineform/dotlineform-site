"""Publish the retained selection for one Catalogue Work before shared output."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from docs_artifact_locations import artifact_location_adapter, authenticated_remote_client_for_locations, R2_PROVIDER
from docs_deploy_repo import project_document_payload, utc_now
from docs_document_identity import is_document_id
from docs_preview_snapshot import PREVIEW_MANIFEST_FILENAME
from docs_publication_payloads import project_public_view
from docs_public_media_reconciliation import publication_media_bindings
from docs_workspace_config import DocsWorkspaceConfig, select_workspace_stage, generated_documents_path, preview_documents_path, public_documents_path, location_child
from pipeline_config import load_pipeline_config
from studio.services.catalogue.catalogue_pending_state import persist_pending_queue
from studio.services.catalogue.catalogue_staged_media import work_rendition_paths
from studio.services.catalogue.catalogue_work_attachments import safe_download_filename


class CataloguePublicationError(RuntimeError):
    """Retain the exact failed Work and handoff for the Publish result."""

    def __init__(self, work_id: str, phase: str, error: Exception) -> None:
        super().__init__(f"Work {work_id}: {phase} failed: {error}")
        self.work_id = work_id
        self.phase = phase


def _read(path: Path) -> bytes:
    if path.resolve() != path or not path.is_file():
        raise FileNotFoundError(f"Required publication input is unavailable: {path.name}")
    data = path.read_bytes()
    if not data:
        raise ValueError(f"Required publication input is empty: {path.name}")
    return data


def _write(path: Path, data: bytes) -> None:
    if path.resolve() != path:
        raise ValueError(f"Publication target must not be a symlink: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if path.read_bytes() != data:
        raise RuntimeError(f"Publication bytes did not verify: {path.name}")


def _delete(path: Path) -> None:
    if path.resolve() != path:
        raise ValueError(f"Publication target must not be a symlink: {path.name}")
    path.unlink(missing_ok=True)


def _media(work_id: str, selection: dict[str, Any], assets: Any, policy: Mapping[str, Any] | None) -> list[tuple[str, Path]]:
    files = []
    if selection["image"]:
        for path in work_rendition_paths(work_id, assets, config=policy):
            family = "primary" if path.parent == assets.work_primary.path else "thumbs"
            files.append((f"catalogue/works/{family}", path))
    files.extend(("catalogue/works/files", location_child(assets.work_files, Path(safe_download_filename(name))).path) for name in selection["file_names"])
    return files


def publish_catalogue_works(
    repo_root: Path, *, workspace: DocsWorkspaceConfig, pending: dict[str, Any], queue_path: Path,
    client: object | None = None,
    env_files: Iterable[Path] | None = None, environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Complete each Work's Preview and Deploy, then remove only that entry.

    Deploy reads only Preview and the retained deletion/transfer selection. It
    never consults canonical flags, the updates queue, or Working readiness.
    Completed effects remain after failure; another explicit Publish retries.
    The caller supplies its parsed queue and resolved workspace. Progress writes
    do not audit queue contents. Media policy, identities and adapters are reused.
    Draining a nonempty queue records Catalogue completion independently of the
    later shared pass. Empty queues and partial failure preserve the saved time.
    """
    if not pending["current_works"] and not pending["deleted_works"]:
        return {"complete": True, "work_ids": [], "work_count": 0}
    working = select_workspace_stage(workspace, "working")
    preview = select_workspace_stage(workspace, "preview")
    working_collection = next(child for child in working.collections if child.collection == "catalogue")
    preview_collection = next(child for child in preview.collections if child.collection == "catalogue")
    preview_root = workspace.workspace_root.path / "preview"
    working_assets, preview_assets = workspace.assets, workspace.assets.for_stage("preview")
    destination = repo_root / workspace.catalogue.public_projection.location.path
    document_destination = repo_root / public_documents_path(preview_collection)
    bindings = None
    policy = None
    adapters = {}
    completed = []
    remote_client = client
    for family in ("current_works", "deleted_works"):
        for work_id in sorted(tuple(pending[family])):
            selection = pending[family][work_id]
            deleting = family == "deleted_works"
            phase = "Preview"
            try:
                if not is_document_id(work_id, collection="catalogue"):
                    raise ValueError("Catalogue publication paths require an exact five-digit Work ID")
                identity = Path("works/index") / f"{work_id}.json"
                preview_metadata = location_child(workspace.catalogue.preview, identity).path
                preview_document = preview_documents_path(preview_collection) / "by-id" / f"{work_id}.json"
                if selection["image"] and policy is None:
                    policy = load_pipeline_config(repo_root=repo_root)
                media = _media(work_id, selection, preview_assets, policy)
                if not selection["preview_done"]:
                    _delete(preview_root / PREVIEW_MANIFEST_FILENAME)
                    if deleting:
                        _delete(preview_metadata)
                        _delete(preview_document)
                    else:
                        metadata = _read(location_child(workspace.catalogue.working, identity).path)
                        document = _read(generated_documents_path(working_collection) / "by-id" / f"{work_id}.json")
                        payload = json.loads(document)
                        document = project_document_payload(project_public_view(workspace, payload))
                        _write(preview_metadata, metadata)
                        _write(preview_document, document)
                    for _key, target in media:
                        if deleting:
                            _delete(target)
                        else:
                            source = location_child(working_assets.work_root, target.relative_to(preview_assets.work_root.path)).path
                            _write(target, _read(source))
                    selection["preview_done"] = True
                    persist_pending_queue(queue_path, pending, progress="preview_done")
                phase = "Deploy"
                targets = ((preview_metadata, destination / identity),
                           (preview_document, document_destination / f"by-id/{work_id}.json"))
                for source, target in targets:
                    if deleting:
                        _delete(target)
                    else:
                        _write(target, _read(source))
                if media:
                    if bindings is None:
                        bindings = publication_media_bindings(repo_root, preview, workspace=workspace)
                    if remote_client is None:
                        remote_client = authenticated_remote_client_for_locations(
                            repo_root, [bindings[key][1].location for key, _path in media],
                            env_files=env_files, environ=environ,
                        )
                for key, source in media:
                    public = bindings[key][1]
                    if public.location.provider == "repository":
                        target = repo_root / public.location.path / source.name
                        if deleting:
                            _delete(target)
                        else:
                            _write(target, _read(source))
                        continue
                    if key not in adapters:
                        adapters[key] = artifact_location_adapter(repo_root, public.location, remote_client=remote_client)
                    adapter = adapters[key]
                    name = source.name
                    if deleting:
                        try:
                            adapter.delete(name)
                        except FileNotFoundError:
                            pass
                        if adapter.stat(name) is not None:
                            raise RuntimeError(f"Deletion did not verify: {key}/{name}")
                    else:
                        data = _read(source)
                        stat = adapter.replace(name, data)
                        if public.location.provider == R2_PROVIDER:
                            verified = stat.size == len(data) and stat.etag.strip('"').lower() == hashlib.md5(data, usedforsecurity=False).hexdigest()
                        else:
                            verified = adapter.verify_bytes(name, data)
                        if not verified:
                            raise RuntimeError(f"Transfer did not verify: {key}/{name}")
                del pending[family][work_id]
                if not pending["current_works"] and not pending["deleted_works"]:
                    pending["header"]["last_published_at_utc"] = utc_now()
                persist_pending_queue(queue_path, pending, progress="preview_done")
                completed.append(work_id)
            except Exception as error:
                raise CataloguePublicationError(work_id, phase, error) from error
    return {"complete": True, "work_ids": completed, "work_count": len(completed)}
