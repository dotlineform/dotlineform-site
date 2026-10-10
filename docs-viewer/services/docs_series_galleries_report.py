"""Read the private Series–Gallery report saved by Refresh Catalogue."""

from pathlib import Path
from typing import Any

from docs_generated_reads import read_generated_json
from studio.services.catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from studio.services.catalogue.catalogue_series_galleries_report import METADATA_PATH, validate_series_galleries_report


def read_series_galleries_report(repo_root: Path) -> dict[str, Any]:
    """Confine reads to Working output; missing data requires explicit relationship maintenance."""
    path = output_path(catalogue_output_workspace(repo_root), METADATA_PATH)
    if not path.exists():
        raise ValueError("Series and Galleries data is unavailable; run explicit relationship maintenance.")
    return validate_series_galleries_report(read_generated_json(path, "Series and Galleries report"))
