"""Project public media policy and enumerate producer-owned thumbnail paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from catalogue.catalogue_generation_common import compute_payload_version
from catalogue.catalogue_source import CatalogueSourceRecords
from pipeline_config import load_pipeline_config


def catalogue_media_policy(repo_root: Path, *, timestamp: str) -> dict[str, Any]:
    """Expose only rendition policy; routes supply their own thumbnail base URL."""
    pipeline = load_pipeline_config(repo_root=repo_root)
    media = json.loads((repo_root / "site-tools/config/site-tools.json").read_text())["media"]
    prefix = str(media["image_works"]).strip("/")
    if prefix == "archive" or prefix.startswith("archive/") or ".." in prefix.split("/"):
        raise ValueError(f"invalid active Catalogue media prefix: {prefix}")
    bases = {"works": f"{media['base'].rstrip('/')}/{prefix}/"}
    primary, thumb = pipeline["variants"]["primary"], pipeline["variants"]["thumb"]
    policy = {
        "format": pipeline["encoding"]["format"],
        "primary": {"base_urls": bases, "widths": primary["widths"], "suffix": primary["suffix"],
                    "version_query_parameter": "v"},
        "thumbnails": {"sizes": thumb["sizes"], "suffix": thumb["suffix"]},
    }
    schema = "catalogue_media_config_v1"
    return {"header": {"schema": schema, "version": compute_payload_version({"schema": schema, **policy}),
                       "generated_at_utc": timestamp}, **policy}


def catalogue_thumbnail_paths(repo_root: Path, records: CatalogueSourceRecords) -> set[str]:
    """Enumerate expected derivatives from source identity, independent of consumer records."""
    pipeline = load_pipeline_config(repo_root=repo_root)
    thumb = pipeline["variants"]["thumb"]
    return {
        f"{item_id}-{thumb['suffix']}-{size}.{pipeline['encoding']['format']}"
        for item_id, record in records.works.items() if record.get("project_filename")
        for size in thumb["sizes"]
    }
