"""Publish the retained selection for one Catalogue Work before shared output."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from docs_artifact_locations import artifact_location_adapter, authenticated_remote_client_for_locations, R2_PROVIDER
from docs_deploy_repo import json_bytes, project_document_payload, utc_now
from docs_preview_snapshot import PREVIEW_MANIFEST_FILENAME
from docs_publication_payloads import project_public_view
from docs_public_media_reconciliation import publication_media_bindings
from docs_workspace_config import load_docs_workspace_config, select_workspace_stage, generated_documents_path, preview_documents_path, public_documents_path, location_child
from studio.services.catalogue.catalogue_pending_publication import read_pending_publication, write_pending_publication
from studio.services.catalogue.catalogue_staged_media import work_image_paths


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


def _media(repo_root: Path, work_id: str, selection: dict[str, Any], assets: Any) -> list[tuple[str, Path]]:
    files = []
    if selection["image"]:
        for path in work_image_paths(repo_root, work_id, assets):
            family = "primary" if path.parent == assets.work_primary.path else "thumbs"
            files.append((f"catalogue/works/{family}", path))
    files.extend(("catalogue/works/files", location_child(assets.work_files, Path(name)).path) for name in selection["file_names"])
    return files


def publish_catalogue_works(
    repo_root: Path, *, client: object | None = None,
    env_files: Iterable[Path] | None = None, environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Complete each Work's Preview and Deploy, then remove only that entry.

    Deploy reads only Preview and the retained deletion/transfer selection. It
    never consults canonical flags, the updates queue, or Working readiness.
    Completed effects remain after failure; another explicit Publish retries.
    Draining a nonempty queue records Catalogue completion independently of the
    later shared pass. Empty queues and partial failure preserve the saved time.
    """
    pending = read_pending_publication(repo_root)
    workspace = load_docs_workspace_config(repo_root)
    working = select_workspace_stage(workspace, "working")
    preview = select_workspace_stage(workspace, "preview")
    working_collection = next(child for child in working.collections if child.collection == "catalogue")
    preview_collection = next(child for child in preview.collections if child.collection == "catalogue")
    preview_root = workspace.workspace_root.path / "preview"
    working_assets, preview_assets = workspace.assets, workspace.assets.for_stage("preview")
    destination = repo_root / workspace.catalogue.public_projection.location.path
    document_destination = repo_root / public_documents_path(preview_collection)
    bindings = publication_media_bindings(repo_root, preview)
    completed = []
    remote_client = client
    for family in ("current_works", "deleted_works"):
        for work_id in sorted(tuple(pending[family])):
            selection = pending[family][work_id]
            deleting = family == "deleted_works"
            identity = Path("works/index") / f"{work_id}.json"
            preview_metadata = location_child(workspace.catalogue.preview, identity).path
            preview_document = preview_documents_path(preview_collection) / "by-id" / f"{work_id}.json"
            phase = "Preview"
            try:
                if not selection["preview_done"]:
                    _delete(preview_root / PREVIEW_MANIFEST_FILENAME)
                    if deleting:
                        _delete(preview_metadata)
                        _delete(preview_document)
                    else:
                        metadata = _read(location_child(workspace.catalogue.working, identity).path)
                        if json.loads(metadata).get("work", {}).get("work_id") != work_id:
                            raise ValueError("Refreshed Work metadata has the wrong identity")
                        document = _read(generated_documents_path(working_collection) / "by-id" / f"{work_id}.json")
                        payload = json.loads(document)
                        if payload.get("doc_id") != work_id:
                            raise ValueError("Built Catalogue document has the wrong identity")
                        document = project_document_payload(json_bytes(project_public_view(workspace, payload)), label=f"Catalogue {work_id}")
                        _write(preview_metadata, metadata)
                        _write(preview_document, document)
                    for (_key, source), (_destination_key, target) in zip(
                        _media(repo_root, work_id, selection, working_assets),
                        _media(repo_root, work_id, selection, preview_assets), strict=True,
                    ):
                        if deleting:
                            _delete(target)
                        else:
                            _write(target, _read(source))
                    selection["preview_done"] = True
                    write_pending_publication(repo_root, pending)
                phase = "Deploy"
                targets = ((preview_metadata, destination / identity),
                           (preview_document, document_destination / f"by-id/{work_id}.json"))
                for source, target in targets:
                    if deleting:
                        _delete(target)
                    else:
                        _write(target, _read(source))
                media = _media(repo_root, work_id, selection, preview_assets)
                remote_client = authenticated_remote_client_for_locations(
                    repo_root, [bindings[key][1].location for key, _path in media],
                    client=remote_client, env_files=env_files, environ=environ,
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
                    adapter = artifact_location_adapter(repo_root, public.location, remote_client=remote_client)
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
                write_pending_publication(repo_root, pending)
                completed.append(work_id)
            except Exception as error:
                raise CataloguePublicationError(work_id, phase, error) from error
    return {"complete": True, "work_ids": completed, "work_count": len(completed)}
