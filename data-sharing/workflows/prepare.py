"""Prepare workflow ownership boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.dispatch import AdapterResolver, DataSharingAdapterHandlers
from services.dispatch import prepare_package as dispatch_prepare_package

OPERATION = "prepare"


def prepare_package(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
    resolve_adapter: AdapterResolver,
) -> dict[str, Any]:
    return dispatch_prepare_package(repo_root, body, dry_run, handlers, resolve_adapter)


__all__ = ["OPERATION", "prepare_package"]
