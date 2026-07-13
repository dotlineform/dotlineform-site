#!/usr/bin/env python3
"""External workspace validation shared by Docs Viewer scope lifecycle actions."""

from __future__ import annotations

from pathlib import Path


ICLOUD_DRIVE_PATH_MARKER = ("Library", "Mobile Documents", "com~apple~CloudDocs")
ICLOUD_TMP_SCOPE_ID_BLOCKER = (
    "scope_id 'tmp' cannot be used for an external scope stored in iCloud Drive "
    "because iCloud excludes folders named tmp from sync"
)


def path_is_in_icloud_drive(path: Path) -> bool:
    parts = path.expanduser().resolve().parts
    return any(
        tuple(parts[index : index + len(ICLOUD_DRIVE_PATH_MARKER)]) == ICLOUD_DRIVE_PATH_MARKER
        for index in range(len(parts) - len(ICLOUD_DRIVE_PATH_MARKER) + 1)
    )


def external_scope_id_sync_blocker(scope_id: str, external_root: Path) -> str:
    if scope_id == "tmp" and path_is_in_icloud_drive(external_root):
        return ICLOUD_TMP_SCOPE_ID_BLOCKER
    return ""


__all__ = [
    "ICLOUD_TMP_SCOPE_ID_BLOCKER",
    "external_scope_id_sync_blocker",
    "path_is_in_icloud_drive",
]
