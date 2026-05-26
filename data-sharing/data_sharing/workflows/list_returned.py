"""Returned-package listing workflow ownership boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from data_sharing.services.dispatch import AdapterResolver, DataSharingAdapterHandlers
from data_sharing.services.dispatch import list_returned_packages as dispatch_list_returned_packages

OPERATION = "list_returned"


def list_returned_packages(
    repo_root: Path,
    data_domain: Any,
    handlers: dict[str, DataSharingAdapterHandlers],
    resolve_adapter: AdapterResolver,
) -> dict[str, Any]:
    return dispatch_list_returned_packages(repo_root, data_domain, handlers, resolve_adapter)


__all__ = ["OPERATION", "list_returned_packages"]
