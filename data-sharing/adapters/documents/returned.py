#!/usr/bin/env python3
"""Temporary legacy returned-route dispatch into Docs Viewer document packages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .context import DocumentsDataSharingDependencies
from .families import documents


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    return documents.list_returned_packages(repo_root, data_domain, adapter, dependencies)


def review_returned_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    return documents.review_returned_package(repo_root, body, dry_run, adapter, dependencies)


def returned_records(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    return documents.returned_records(repo_root, body, dry_run, adapter, dependencies)


def apply_returned_changes(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    return documents.apply_returned_changes(repo_root, body, dry_run, adapter, dependencies)


__all__ = [
    "apply_returned_changes",
    "list_returned_packages",
    "returned_records",
    "review_returned_package",
]
