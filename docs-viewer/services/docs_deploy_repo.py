"""Public byte projection and configured repository capability."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
from pathlib import Path
from typing import Any

from docs_workspace_config import DocsWorkspaceConfig, select_workspace_stage


LOCAL_FOLDER_ANCHOR_PATTERN = re.compile(
    r"<a\b(?P<attrs>(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>(?P<label>.*?)</a\s*>",
    re.IGNORECASE | re.DOTALL,
)


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _writable_repository_destination(
    repo_root: Path,
    relative_path: Path,
    *,
    directory: bool,
) -> bool:
    target = repository_path(repo_root, relative_path)
    if target.is_symlink():
        return False
    if target.exists():
        if directory and not target.is_dir():
            return False
        if not directory and not target.is_file():
            return False
        required = os.W_OK | (os.X_OK if directory else 0)
        return os.access(target, required)

    ancestor = target if directory else target.parent
    resolved_root = repo_root.resolve()
    while not ancestor.exists() and ancestor != resolved_root:
        ancestor = ancestor.parent
    return (
        ancestor.is_dir()
        and not ancestor.is_symlink()
        and os.access(ancestor, os.W_OK | os.X_OK)
    )


def deploy_repo_capability(
    repo_root: Path,
    config: DocsWorkspaceConfig,
) -> dict[str, Any]:
    """Project a browser-safe capability from configured destination authority."""

    unavailable = {
        "available": False,
        "reason": "The configured repository projection is unavailable.",
    }
    try:
        deployable = select_workspace_stage(config, "preview")
    except (FileNotFoundError, ValueError):
        return {
            **unavailable,
            "reason": "The workspace has no configured repository projection.",
        }

    projection = deployable.public_projection
    if projection is None:
        return {
            **unavailable,
            "reason": "The workspace has no configured repository projection.",
        }
    destinations: list[tuple[Path, bool]] = [
        (projection.documents.location.path, True),
        (projection.search.location.path, False),
        (config.catalogue.public_projection.location.path, True),
    ]
    destinations.extend(
        (collection.public_projection.documents.location.path, True)
        for collection in deployable.collections
        if collection.public_projection is not None
    )
    destinations.extend(
        (media.location.path, True)
        for media in projection.media.values()
        if media.location.provider == "repository"
    )
    try:
        writable = all(
            _writable_repository_destination(
                repo_root.resolve(),
                path,
                directory=directory,
            )
            for path, directory in destinations
        )
    except ValueError:
        writable = False
    if not writable:
        return {
            **unavailable,
            "reason": "The configured repository projection is unavailable.",
        }
    return {
        "available": True,
        "reason": "",
    }


def repository_path(repo_root: Path, path: Path) -> Path:
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"repository deployment path escapes the repository: {path}") from exc
    return resolved


def project_public_local_folder_links(content_html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs").lower()
        if "data-docs-viewer-local-target" not in attrs and not re.search(
            r"\bhref\s*=\s*(?:[\"']dlf-local:|dlf-local:)",
            attrs,
            re.IGNORECASE,
        ):
            return match.group(0)
        label = html.unescape(re.sub(r"<[^>]*>", "", match.group("label"))).strip()
        if not label or label.startswith("/") or label.lower().startswith(("file:", "dlf-local:")):
            label = "[local file or folder]"
        return html.escape(label)

    return LOCAL_FOLDER_ANCHOR_PATTERN.sub(replace, content_html)


def project_document_payload(payload: dict[str, Any]) -> bytes:
    """Finish local-folder presentation on an upstream-rendered public payload."""
    payload["content_html"] = project_public_local_folder_links(payload["content_html"])
    return json_bytes(payload)
