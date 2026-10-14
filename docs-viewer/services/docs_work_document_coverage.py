"""Read the private Work Document Coverage input saved by Refresh Catalogue."""

import json
from pathlib import Path
from typing import Any

from studio.services.catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from studio.services.catalogue.catalogue_work_document_coverage import MANIFEST_PATH


def read_work_document_coverage_manifest(repo_root: Path) -> dict[str, Any]:
    """Read/parse one confined saved file, trusting Refresh-owned rows and order.

    Unavailable or unreadable JSON requires explicit maintenance. This reader
    never validates memberships/labels, joins canonical records or generates data.
    """
    path = output_path(catalogue_output_workspace(repo_root), MANIFEST_PATH)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError("Work Document Coverage data is unavailable or invalid; run explicit Work Document Coverage maintenance.") from error
    if not isinstance(payload, dict):
        raise ValueError("Work Document Coverage data must contain a JSON object.")
    return payload
