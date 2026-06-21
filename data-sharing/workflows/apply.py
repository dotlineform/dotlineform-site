"""Apply workflow ownership boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.dispatch import AdapterResolver, DataSharingAdapterHandlers
from services.dispatch import apply_returned_changes as dispatch_apply_returned_changes

OPERATION = "apply"


def apply_returned_changes(
    repo_root: Path,
    body: dict[str, Any],
    dry_run: bool,
    handlers: dict[str, DataSharingAdapterHandlers],
    resolve_adapter: AdapterResolver,
) -> dict[str, Any]:
    return dispatch_apply_returned_changes(repo_root, body, dry_run, handlers, resolve_adapter)


__all__ = ["OPERATION", "apply_returned_changes"]
