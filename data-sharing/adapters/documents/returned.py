#!/usr/bin/env python3
"""Returned package dispatch for Documents Data Sharing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .context import DocumentsDataSharingDependencies
from .families import library


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    return library.list_returned_packages(repo_root, data_domain, adapter, dependencies)


def review_returned_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    return library.review_returned_package(repo_root, body, dry_run, adapter, dependencies)


def apply_returned_changes(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    return library.apply_returned_changes(repo_root, body, dry_run, adapter, dependencies)
