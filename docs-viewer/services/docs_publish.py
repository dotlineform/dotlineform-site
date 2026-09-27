"""Publish fresh Working content through one completed Preview snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from docs_deploy_repo import apply_deploy_repo_plan, build_deploy_repo_plan, utc_now
from docs_prepare_preview import prepare_preview


def publish_docs(
    repo_root: Path,
    body: dict[str, Any],
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Await fresh preparation and distribution without caller-selected stages.

    The request is an empty object. A preparation failure prevents distribution;
    a distribution failure retains completed Preview and reports incomplete
    publication, including any non-atomic repository/remote effects. No retries,
    rollback, Git actions or public-site deployment are performed here.
    """
    if not isinstance(body, dict) or body:
        raise ValueError("Publish requires an empty request object; its workspace and destinations are configured")

    result: dict[str, Any] = {
        "ok": False,
        "complete": False,
        "phase": "preparation",
        "preview_prepared": False,
    }
    try:
        snapshot = prepare_preview(repo_root)
        result.update(
            phase="distribution", preview_prepared=True,
            preview_revision=snapshot.manifest["preview_revision"],
        )
        plan = build_deploy_repo_plan(
            repo_root, snapshot, deployment_timestamp=utc_now(),
            client=client, env_files=env_files, environ=environ,
        )
        distribution = apply_deploy_repo_plan(
            repo_root, plan, client=client, env_files=env_files, environ=environ,
        )
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
        result["error"] = str(error)
        result["summary_text"] = (
            "Preview prepared; publication is incomplete. "
            if result["preview_prepared"]
            else "Preparation failed; distribution did not start. "
        ) + str(error)
        return result

    result.update(ok=True, complete=True, phase="complete", summary_text="Publish complete.")
    return result
