#!/usr/bin/env python3
"""Prepare dispatch for Documents Data Sharing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .context import DocumentsDataSharingDependencies
from .families import library


def prepare_package(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Optional[Any] = None,
    dependencies: Optional[DocumentsDataSharingDependencies] = None,
) -> Dict[str, Any]:
    return library.prepare_package(repo_root, body, dry_run, adapter, dependencies)
