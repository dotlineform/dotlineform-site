#!/usr/bin/env python3
"""Interactive HTML asset handling for staged Docs source imports."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any, Dict

from docs_import_common import HTML_STAGED_SUFFIXES, STAGING_REL_DIR, is_interactive_html_import_asset
from docs_import_source_helpers import relative_path
from docs_source_model import normalize_scope, slugify

INTERACTIVE_HTML_ASSET_REL_ROOT = Path("site/assets/docs/interactive")
INTERACTIVE_HTML_FILENAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*\.html$")

def interactive_html_staged_paths(repo_root: Path) -> list[Path]:
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    if not staging_root.exists():
        return []
    return [
        path
        for path in sorted(staging_root.iterdir(), key=lambda candidate: candidate.name.lower())
        if path.is_file()
        and path.suffix.lower() in HTML_STAGED_SUFFIXES
        and is_interactive_html_import_asset(path)
    ]


def interactive_html_asset_plan_for_path(repo_root: Path, source_path: Path, scope: str) -> Dict[str, Any]:
    filename = f"{slugify(source_path.stem)}.html"
    if not INTERACTIVE_HTML_FILENAME_PATTERN.fullmatch(filename):
        raise ValueError(f"Interactive HTML asset filename must be a simple slug ending in .html: {filename}")

    normalized_scope = normalize_scope(scope)
    target_rel = INTERACTIVE_HTML_ASSET_REL_ROOT / normalized_scope / filename
    target_root = (repo_root / INTERACTIVE_HTML_ASSET_REL_ROOT / normalized_scope).resolve()
    target_path = (repo_root / target_rel).resolve()
    if not target_path.is_relative_to(target_root):
        raise ValueError(f"Interactive HTML target escapes scope asset root: {target_rel.as_posix()}")

    return {
        "source_path": relative_path(repo_root, source_path),
        "target_path": target_rel.as_posix(),
        "public_path": f"/assets/docs/interactive/{normalized_scope}/{filename}",
        "token": f"[[interactive-html:{filename}]]",
        "filename": filename,
        "display_name": Path(filename).stem,
        "result_type": "script file",
        "target_exists": target_path.exists(),
    }


def interactive_html_asset_plans(repo_root: Path, scope: str) -> list[Dict[str, Any]]:
    plans = [
        interactive_html_asset_plan_for_path(repo_root, path, scope)
        for path in interactive_html_staged_paths(repo_root)
    ]
    target_paths: set[str] = set()
    for plan in plans:
        target_path = str(plan.get("target_path") or "")
        if target_path in target_paths:
            raise ValueError(f"Multiple interactive HTML staged files resolve to {target_path}.")
        target_paths.add(target_path)
    return plans


def ensure_interactive_html_targets_available(plans: list[Dict[str, Any]], *, allow_overwrite: bool = False) -> None:
    for plan in plans:
        if plan.get("target_exists") and not allow_overwrite:
            raise FileExistsError(
                f"Interactive HTML asset already exists: {plan.get('target_path')}. "
                "Edit that asset directly or confirm overwrite to replace it during import."
            )


def materialize_interactive_html_asset(
    repo_root: Path,
    plan: Dict[str, Any],
    *,
    allow_overwrite: bool = False,
) -> Dict[str, Any]:
    ensure_interactive_html_targets_available([plan], allow_overwrite=allow_overwrite)
    source_path = (repo_root / str(plan.get("source_path") or "")).resolve()
    target_path = (repo_root / str(plan.get("target_path") or "")).resolve()
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    target_root = (repo_root / INTERACTIVE_HTML_ASSET_REL_ROOT / target_path.parent.name).resolve()
    if not source_path.is_relative_to(staging_root):
        raise ValueError("Interactive HTML asset source escapes import staging root.")
    if not target_path.is_relative_to(target_root):
        raise ValueError("Interactive HTML asset target escapes scope asset root.")
    target_existed = target_path.exists()
    if target_existed and not allow_overwrite:
        raise FileExistsError(
            f"Interactive HTML asset already exists: {relative_path(repo_root, target_path)}"
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    return {
        "source_path": relative_path(repo_root, source_path),
        "target_path": relative_path(repo_root, target_path),
        "public_path": str(plan.get("public_path") or ""),
        "token": str(plan.get("token") or ""),
        "filename": str(plan.get("filename") or target_path.name),
        "display_name": str(plan.get("display_name") or target_path.stem),
        "result_type": "script file",
        "size_bytes": target_path.stat().st_size,
        "overwrote": target_existed,
    }


def materialize_interactive_html_assets(
    repo_root: Path,
    plans: list[Dict[str, Any]],
    *,
    allow_overwrite: bool = False,
) -> list[Dict[str, Any]]:
    if not plans:
        return []
    ensure_interactive_html_targets_available(plans, allow_overwrite=allow_overwrite)
    return [
        materialize_interactive_html_asset(repo_root, plan, allow_overwrite=allow_overwrite)
        for plan in plans
    ]
