"""Read the private Work Document Coverage manifest saved by Refresh Catalogue."""

from pathlib import Path
from typing import Any

from docs_generated_reads import read_generated_json
from studio.services.catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from studio.services.catalogue.catalogue_work_document_coverage import MANIFEST_PATH, validate_work_document_coverage_manifest


def read_work_document_coverage_manifest(repo_root: Path) -> dict[str, Any]:
    """Read only Working output; missing data requires an explicit Studio Refresh."""
    path = output_path(catalogue_output_workspace(repo_root), MANIFEST_PATH)
    if not path.exists():
        raise ValueError("Work Document Coverage data is unavailable; run Refresh Catalogue in Studio.")
    return validate_work_document_coverage_manifest(read_generated_json(path, "Work Document Coverage manifest"))
