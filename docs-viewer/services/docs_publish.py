"""Publish queued Catalogue Works, then complete one shared Preview snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from docs_deploy_repo import apply_deploy_repo_plan, build_deploy_repo_plan, utc_now
from docs_prepare_preview import prepare_preview
from docs_catalogue_publication import CataloguePublicationError, publish_catalogue_works


def publish_docs(
    repo_root: Path,
    body: dict[str, Any],
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Await per-Work publication and shared output without caller-selected stages.

    The request is empty. Each Work finishes Preview/Deploy before shared
    preparation starts. Shared preparation failure prevents shared distribution;
    earlier Work effects remain. Distribution failure retains completed Preview
    and reports incomplete publication, including non-atomic effects. No retries,
    rollback, Git actions or public-site deployment are performed here.
    """
    if not isinstance(body, dict) or body:
        raise ValueError("Publish requires an empty request object; its workspace and destinations are configured")

    result: dict[str, Any] = {
        "ok": False,
        "complete": False,
        "phase": "catalogue",
        "preview_prepared": False,
    }
    try:
        result["catalogue"] = publish_catalogue_works(repo_root, client=client, env_files=env_files, environ=environ)
        result["phase"] = "shared preparation"
        snapshot = prepare_preview(repo_root)
        result.update(
            phase="distribution", preview_prepared=True,
            preview_revision=snapshot.manifest["preview_revision"],
        )
        plan = build_deploy_repo_plan(
            repo_root, snapshot, deployment_timestamp=utc_now(),
            client=client, env_files=env_files, environ=environ,
        )
        distribution = apply_deploy_repo_plan(repo_root, plan)
        result["distribution"] = distribution
        if not distribution["complete"]:
            errors = [
                *distribution["media"]["errors"],
                *(item["error"] for item in distribution["publication_lineage"]["workflows"] if item["error"]),
            ]
            result["error"] = "; ".join(errors)
            result["summary_text"] = "Preview prepared; publication is incomplete. " + result["error"]
            return result
    except Exception as error:
        if isinstance(error, CataloguePublicationError):
            result.update(work_id=error.work_id, phase=error.phase)
        result["error"] = str(error)
        result["summary_text"] = (
            "Preview prepared; publication is incomplete. "
            if result["preview_prepared"]
            else "Publish stopped; completed effects were retained. "
        ) + str(error)
        return result

    result.update(ok=True, complete=True, phase="complete", summary_text="Publish complete.")
    return result
