"""Path contracts for Data Sharing runtime artifacts."""

from __future__ import annotations

from pathlib import Path


RUNTIME_ARTIFACT_ROOT = Path("var/analytics/data-sharing")
EXPORT_ROOT = RUNTIME_ARTIFACT_ROOT / "exports"
IMPORT_STAGING_ROOT = RUNTIME_ARTIFACT_ROOT / "import-staging"
IMPORT_PREVIEW_ROOT = RUNTIME_ARTIFACT_ROOT / "import-preview"


__all__ = ["EXPORT_ROOT", "IMPORT_PREVIEW_ROOT", "IMPORT_STAGING_ROOT", "RUNTIME_ARTIFACT_ROOT"]
