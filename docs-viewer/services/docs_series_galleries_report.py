"""Read the private Series and Galleries input saved by Refresh Catalogue."""

import json
from pathlib import Path
from typing import Any

from studio.services.catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from studio.services.catalogue.catalogue_series_galleries_report import METADATA_PATH


def read_series_galleries_report(repo_root: Path) -> dict[str, Any]:
    """Read/parse one confined saved file, trusting Refresh-owned rows and order.

    Unavailable or unreadable JSON requires explicit maintenance. This reader
    never validates memberships/labels, joins canonical records or generates data.
    """
    path = output_path(catalogue_output_workspace(repo_root), METADATA_PATH)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError("Series and Galleries data is unavailable or invalid; run explicit relationship maintenance.") from error
    if not isinstance(payload, dict):
        raise ValueError("Series and Galleries data must contain a JSON object.")
    return payload
