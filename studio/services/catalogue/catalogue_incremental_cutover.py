"""Migrate the completed Catalogue publication baseline to Gallery/Series queues."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_pending_updates import FILENAME as UPDATES_FILENAME, SCHEMA as UPDATES_SCHEMA, write_pending_updates  # noqa: E402
from catalogue.catalogue_pending_publication import FILENAME as PUBLISH_FILENAME, SCHEMA as PUBLISH_SCHEMA, write_pending_publication  # noqa: E402
from catalogue.catalogue_pending_state import pending_path, validate_pending_state  # noqa: E402
from catalogue.catalogue_shared_changes import empty_shared_changes  # noqa: E402


def migrate_shared_catalogue_queues(repo_root: Path) -> None:
    """Explicit v3 → v4 cutover from the user's completed publication baseline."""
    migrated = []
    for filename, schema, progress, timestamp in (
        (UPDATES_FILENAME, UPDATES_SCHEMA, "refreshed", "last_refreshed_at_utc"),
        (PUBLISH_FILENAME, PUBLISH_SCHEMA, "preview_done", "last_published_at_utc"),
    ):
        old = json.loads(pending_path(repo_root, filename).read_bytes())
        old_schema = "catalogue_updates_pending_v3" if progress == "refreshed" else "catalogue_publish_pending_v3"
        header_fields = {"schema", timestamp} | ({"shared_refresh_pending"} if progress == "refreshed" else set())
        if (not isinstance(old, dict) or set(old) != {"header", "current_works", "deleted_works"}
                or not isinstance(old["header"], dict) or set(old["header"]) != header_fields
                or old["header"]["schema"] != old_schema or old["current_works"] != {} or old["deleted_works"] != {}
                or (progress == "refreshed" and old["header"]["shared_refresh_pending"] is not False)):
            raise ValueError("Complete the v3 Refresh/Regenerate/Publish baseline before Gallery/Series cutover")
        value = {"header": {"schema": schema, timestamp: old["header"][timestamp]},
                 "current_works": {}, "deleted_works": {}, **empty_shared_changes()}
        validate_pending_state(repo_root, value, schema=schema, progress=progress)
        migrated.append(value)
    write_pending_updates(repo_root, migrated[0])
    write_pending_publication(repo_root, migrated[1])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True)
    parser.parse_args()
    migrate_shared_catalogue_queues(REPO_ROOT)
    print("Migrated both empty Catalogue queues to v4; preserved Refresh and Work publication timestamps.")


if __name__ == "__main__":
    main()
