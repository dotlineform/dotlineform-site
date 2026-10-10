"""Initialise approved incremental Catalogue state after the manual media baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_paths import catalogue_workspace_config, output_path  # noqa: E402
from catalogue.catalogue_pending_updates import FILENAME as UPDATES_FILENAME, initial_pending_updates, write_pending_updates  # noqa: E402
from catalogue.catalogue_pending_publication import FILENAME as PUBLISH_FILENAME, SCHEMA as PUBLISH_SCHEMA, write_pending_publication  # noqa: E402
from catalogue.catalogue_pending_state import pending_path  # noqa: E402
from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, records_from_json_source  # noqa: E402
from catalogue.catalogue_transactions import atomic_write_many  # noqa: E402


def initialise_incremental_catalogue(repo_root: Path) -> dict[str, int]:
    """One explicit cutover; no media migration, queue alias, or runtime fallback."""
    workspace = catalogue_workspace_config(repo_root)
    old_path = output_path(workspace.workspace_root, "working/source/collections/catalogue/updates-pending.json")
    old = json.loads(old_path.read_bytes())
    if old != {"schema": "catalogue_updates_pending_v1", "current_work_ids": [], "deleted_work_ids": []}:
        raise ValueError("Finish the old Refresh/Regenerate/Publish queue before cutover")
    if any(pending_path(repo_root, name).exists() for name in (UPDATES_FILENAME, PUBLISH_FILENAME)):
        raise ValueError("Incremental queues already exist; this cutover is a one-time operation")
    for stage in ("working", "preview"):
        if not workspace.assets.for_stage(stage).work_root.path.is_dir():
            raise FileNotFoundError(f"Manual {stage} Work media baseline directory is unavailable")
    source = repo_root / DEFAULT_SOURCE_DIR
    path = source / SOURCE_FILES["works"]
    payload = json.loads(path.read_bytes())
    works = payload["works"]
    downloads = 0
    for work in works.values():
        work["image_staged"] = False
        for entry in work.get("downloads") or []:
            entry["staged"] = False
            downloads += 1
    atomic_write_many({path: payload})
    records_from_json_source(source)
    write_pending_updates(repo_root, initial_pending_updates())
    write_pending_publication(repo_root, {"header": {"schema": PUBLISH_SCHEMA, "last_published_at_utc": None}, "current_works": {}, "deleted_works": {}})
    old_path.unlink()
    return {"works": len(works), "downloads": downloads}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True)
    parser.parse_args()
    result = initialise_incremental_catalogue(REPO_ROOT)
    print(f"Initialised {result['works']} Work image flags, {result['downloads']} download flags and two empty queues; retired the empty old queue.")


if __name__ == "__main__":
    main()
