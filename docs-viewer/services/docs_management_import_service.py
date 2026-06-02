"""Docs import source service adapters for Local Studio."""

from __future__ import annotations

from typing import Any, Dict

import docs_import_source_service as import_source_service
import docs_write_rebuild as write_rebuild
from docs_management_context import log_event


def import_source_dependencies() -> import_source_service.ImportSourceDependencies:
    return import_source_service.ImportSourceDependencies(
        log_event=log_event,
        perform_source_write_and_rebuild=write_rebuild.perform_source_write_and_rebuild,
    )


def handle_import_source(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return import_source_service.handle_import_source(repo_root, body, dry_run, import_source_dependencies())
