#!/usr/bin/env python3
"""Shared exact Catalogue document-URL refresh after public Docs changes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


# UAC 1: retain the machinery, but resume only when the new Catalogue projection
# destination is implemented. This is not controlled by payload availability.
CATALOGUE_SITE_PROJECTION_PAUSED = True


def paused_result() -> dict[str, Any]:
    return {
        "status": "paused",
        "reason": "Catalogue site projection is paused until the new projection is wired in.",
        "stale": False,
        "affected_targets": [],
        "changed_paths": [],
        "changed_count": 0,
        "updated_paths": [],
        "error": "",
    }


def repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes repo root: {path}") from exc


def stale_result(
    error: Exception,
    *,
    affected_targets: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "status": "stale",
        "stale": True,
        "affected_targets": affected_targets or [],
        "updated_paths": [],
        "error": str(error),
    }


def apply_projection(
    repo_root: Path,
    projection: Mapping[str, Mapping[str, list[Mapping[str, str]]]],
) -> dict[str, Any]:
    """Apply one already-derived exact Catalogue URL projection."""

    if CATALOGUE_SITE_PROJECTION_PAUSED:
        return paused_result()

    affected_targets: list[dict[str, str]] = []
    try:
        from catalogue.catalogue_document_url_refresh import (
            apply_catalogue_document_url_refresh_plan,
            build_catalogue_document_url_refresh_plan,
        )

        plan = build_catalogue_document_url_refresh_plan(repo_root, projection)
        affected_targets = [
            {"kind": kind, "key": key}
            for kind, key in plan.affected_targets
        ]
        result = apply_catalogue_document_url_refresh_plan(plan)
    except Exception as exc:
        return stale_result(exc, affected_targets=affected_targets)

    updated_paths = [repo_relative(repo_root, path) for path in result.written_paths]
    return {
        "status": "updated" if updated_paths else "unchanged",
        "stale": False,
        "affected_targets": affected_targets,
        "updated_paths": updated_paths,
    }


def refresh_from_current_public_state(repo_root: Path) -> dict[str, Any]:
    """Refresh after exact Delete cleanup using the surviving public state."""

    if CATALOGUE_SITE_PROJECTION_PAUSED:
        return paused_result()

    try:
        from docs_catalogue_document_urls import load_public_catalogue_documents

        projection = load_public_catalogue_documents(repo_root)
    except Exception as exc:
        return stale_result(exc)
    return apply_projection(repo_root, projection)


__all__ = [
    "CATALOGUE_SITE_PROJECTION_PAUSED",
    "apply_projection",
    "paused_result",
    "refresh_from_current_public_state",
    "repo_relative",
    "stale_result",
]
