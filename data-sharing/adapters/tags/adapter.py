#!/usr/bin/env python3
"""Analytics tags adapter wiring for Data Sharing workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from data_sharing_adapters import AdapterResolution
from services.dispatch import DataSharingAdapterHandlers

from . import context, prepare, returned


def handlers_for(
    dependencies_factory: Callable[[], context.TagsDataSharingDependencies],
) -> DataSharingAdapterHandlers:
    def selectable_records_handler(repo_root: Path, data_domain: Any, selectors: Any, adapter: AdapterResolution) -> Dict[str, Any]:
        return prepare.selectable_records(repo_root, data_domain, selectors, adapter, dependencies_factory())

    def list_handler(repo_root: Path, data_domain: Any, adapter: AdapterResolution) -> Dict[str, Any]:
        return returned.list_returned_packages(repo_root, data_domain, adapter, dependencies_factory())

    def review_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return returned.review_returned_package(repo_root, body, dry_run, adapter, dependencies_factory())

    def apply_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return returned.apply_returned_changes(repo_root, body, dry_run, adapter, dependencies_factory())

    def prepare_handler(repo_root: Path, body: Dict[str, Any], dry_run: bool, adapter: AdapterResolution) -> Dict[str, Any]:
        return prepare.prepare_package(repo_root, body, dry_run, adapter, dependencies_factory())

    return DataSharingAdapterHandlers(
        module="analytics.tags",
        selectable_records=selectable_records_handler,
        prepare=prepare_handler,
        list_returned=list_handler,
        review=review_handler,
        apply=apply_handler,
    )
