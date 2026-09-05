"""Load the current Catalogue field and output ownership inventory."""

from pathlib import Path
from typing import Any

from catalogue.catalogue_source import load_json_file

REGISTRY_PATH = Path("studio/data/config/catalogue/catalogue-field-registry.json")


def load_catalogue_field_registry(repo_root: Path) -> dict[str, Any]:
    """Read the checked inventory; generation is owned by the producer services."""
    payload = load_json_file(repo_root / REGISTRY_PATH)
    if payload.get("schema") != "catalogue_field_registry_v2":
        raise ValueError("unsupported Catalogue field registry schema")
    return payload
