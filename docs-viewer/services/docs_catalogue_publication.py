"""Selected Catalogue item/shared byte transfers, without preparation or resume."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from docs_catalogue_artifacts import load_catalogue_artifact_inventory
from docs_deploy_repo import utc_now
from docs_catalogue_static import prepare_catalogue_document
from docs_publication_paths import confined, document_path
from docs_publication_transfer import completed_effect, delete_path, read_bytes, write_bytes
from docs_workspace_config import location_child, preview_documents_path, public_documents_path, select_workspace_stage
from pipeline_config import load_pipeline_config
from studio.services.catalogue.catalogue_pending_state import persist_pending_queue
from studio.services.catalogue.catalogue_shared_changes import SHARED_FIELDS
from studio.services.catalogue.catalogue_staged_media import work_rendition_paths
from studio.services.catalogue.catalogue_work_attachments import safe_download_filename


def _save(path: Path, pending: dict[str, Any], *, work_completed: bool = False) -> None:
    if work_completed and not pending["current_works"] and not pending["deleted_works"]:
        pending["header"]["last_published_at_utc"] = utc_now()
    persist_pending_queue(path, pending, progress="published")


def publish_catalogue_works(repo_root: Path, workspace: Any, pending: dict[str, Any], queue_path: Path, work_media: Any, inputs: Any, result: dict[str, Any]) -> None:
    if not pending["current_works"] and not pending["deleted_works"]:
        return
    preview = select_workspace_stage(workspace, "preview")
    owner = next(child for child in preview.collections if child.collection == "catalogue")
    assets = workspace.assets.for_stage("preview")
    policy = None
    for family in ("current_works", "deleted_works"):
        deleting = family == "deleted_works"
        for work_id, selection in tuple(pending[family].items()):
            result.update(phase="Catalogue Work Preview", target=work_id)
            metadata_identity = Path("works/index") / f"{work_id}.json"
            metadata = location_child(workspace.catalogue.preview, metadata_identity).path
            document_identity = Path("by-id") / f"{work_id}.json"
            document = confined(preview_documents_path(owner), document_identity)
            media = []
            if selection["image"]:
                if policy is None:
                    policy = load_pipeline_config(repo_root=repo_root)
                for target in work_rendition_paths(work_id, assets, config=policy):
                    key = "primary" if target.parent == assets.work_primary.path else "thumbs"
                    media.append((f"catalogue/works/{key}", target))
            media.extend(("catalogue/works/files", location_child(assets.work_files, Path(safe_download_filename(name))).path) for name in selection["file_names"])
            if not deleting:
                result.update(phase="Catalogue Work preparation", target=work_id)
                payload = json.loads(read_bytes(document_path(workspace, "catalogue", work_id)))
                prepared = prepare_catalogue_document({"collection": "catalogue", "doc_id": work_id}, payload, inputs)
                document_bytes = (json.dumps(prepared.payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
                result["phase"] = "Catalogue Work Preview"
            if deleting:
                delete_path(metadata)
                completed_effect(result, "Preview files removed", metadata)
                delete_path(document)
            else:
                metadata_bytes = write_bytes(metadata, inputs.bytes(metadata_identity.as_posix()))
                completed_effect(result, "Preview files applied", metadata)
                write_bytes(document, document_bytes)
            completed_effect(result, "Preview files removed" if deleting else "Preview files applied", document)
            work_media.apply(((key, target.name) for key, target in media), deleting=deleting)
            result["phase"] = "Catalogue Work distribution"
            result["target"] = work_id
            for data, target in ((None if deleting else metadata_bytes, confined(repo_root / workspace.catalogue.public_projection.location.path, metadata_identity)), (None if deleting else document_bytes, confined(repo_root / public_documents_path(owner), document_identity))):
                if deleting:
                    delete_path(target)
                else:
                    write_bytes(target, data)
                completed_effect(result, "destination files removed" if deleting else "destination files applied", target)
            del pending[family][work_id]
            _save(queue_path, pending, work_completed=True)
            result["completed"].append({"family": family, "work_id": work_id})


def publish_catalogue_shared(repo_root: Path, workspace: Any, pending: dict[str, Any], queue_path: Path, result: dict[str, Any]) -> None:
    if not any(pending[field] for field in SHARED_FIELDS):
        return
    inventory = load_catalogue_artifact_inventory(repo_root)
    for field in SHARED_FIELDS:
        for identity in tuple(pending[field]):
            result.update(phase="Catalogue shared Preview", target=f"{field}/{identity}")
            deleting = field == "deleted_galleries"
            if field.endswith("galleries"):
                relative = Path("galleries/index") / f"{identity}.json"
            elif field == "shared_outputs":
                relative = Path(identity)
                if relative not in inventory.system_files:
                    raise ValueError(f"Catalogue output is outside configured public authority: {identity}")
            else:
                # Series selections have completed their shared-index effects
                # upstream; they do not identify independent public files.
                pending[field].remove(identity)
                _save(queue_path, pending)
                result["completed"].append({"family": field, "identity": identity})
                continue
            target = location_child(workspace.catalogue.preview, relative).path
            if deleting:
                delete_path(target)
            else:
                data = write_bytes(target, read_bytes(location_child(workspace.catalogue.working, relative).path))
            completed_effect(result, "Preview files removed" if deleting else "Preview files applied", target)
            result["phase"] = "Catalogue shared distribution"
            destination = confined(repo_root / workspace.catalogue.public_projection.location.path, relative)
            if deleting:
                delete_path(destination)
            else:
                write_bytes(destination, data)
            completed_effect(result, "destination files removed" if deleting else "destination files applied", destination)
            pending[field].remove(identity)
            _save(queue_path, pending)
            result["completed"].append({"family": field, "identity": identity})
