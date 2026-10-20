"""Read the private Catalogue Works metadata saved by Refresh Catalogue."""

import json
from pathlib import Path
from typing import Any

from studio.services.catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from studio.services.catalogue.catalogue_works_metadata import METADATA_PATH


def read_catalogue_works_report(repo_root: Path) -> dict[str, Any]:
    """Read one confined saved file, trusting Refresh-owned rows without generation."""
    path = output_path(catalogue_output_workspace(repo_root), METADATA_PATH)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Catalogue Works metadata is unavailable; run explicit metadata generation.") from error
