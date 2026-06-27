#!/usr/bin/env python3
"""Documents adapter for Data Sharing workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from services.dispatch import DataSharingAdapterHandlers

from . import context, prepare, returned
from .families import documents


def handlers_for(
    dependencies_factory: Callable[[], context.DocumentsDataSharingDependencies],
) -> DataSharingAdapterHandlers:
    def selectable_records_handler(repo_root: Path, data_domain: Any, selectors: Any, adapter: Any) -> Dict[str, Any]:
        return documents.selectable_records(repo_root, data_domain, selectors, adapter, dependencies_factory())

    def prepare_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: Any) -> Dict[str, Any]:
        return prepare.prepare_package(repo_root, body, dry_run, adapter, dependencies_factory())

    def list_handler(repo_root: Path, data_domain: Any, adapter: Any) -> Dict[str, Any]:
        return returned.list_returned_packages(repo_root, data_domain, adapter, dependencies_factory())

    def review_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: Any) -> Dict[str, Any]:
        return returned.review_returned_package(repo_root, body, dry_run, adapter, dependencies_factory())

    def returned_records_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: Any) -> Dict[str, Any]:
        return returned.returned_records(repo_root, body, dry_run, adapter, dependencies_factory())

    def apply_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: Any) -> Dict[str, Any]:
        return returned.apply_returned_changes(repo_root, body, dry_run, adapter, dependencies_factory())

    return DataSharingAdapterHandlers(
        module="documents",
        selectable_records=selectable_records_handler,
        prepare=prepare_handler,
        list_returned=list_handler,
        returned_records=returned_records_handler,
        review=review_handler,
        apply=apply_handler,
    )


def update_prepare_context(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: Any,
    dependencies: context.DocumentsDataSharingDependencies | None = None,
) -> Dict[str, Any]:
    return documents.update_prepare_context(repo_root, body, dry_run, adapter, dependencies)
