"""The single/bulk Work request envelope for relinking unchanged originals."""

from __future__ import annotations

from typing import Any, Mapping


def extract_source_folder(body: Mapping[str, Any]) -> dict[str, Any] | None:
    """Accept only location fields; the picker owns filename/location validity.

    Null source/subfolder values use existing canonical optional-key omission.
    This boundary performs no source lookup, directory scan or content check.
    """
    if "source_folder" not in body:
        return None
    folder = body["source_folder"]
    if not isinstance(folder, dict) or set(folder) != {
        "media_source_id", "project_folder", "project_subfolder",
    }:
        raise ValueError("source_folder requires media_source_id, project_folder and project_subfolder")
    return folder
