"""Migrate an empty Catalogue updates queue to explicit Gallery member candidates."""

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
from catalogue.catalogue_pending_publication import read_pending_publication  # noqa: E402
from catalogue.catalogue_pending_state import pending_path  # noqa: E402
from catalogue.catalogue_shared_changes import SHARED_FIELDS, empty_shared_changes  # noqa: E402


def migrate_gallery_member_queue(repo_root: Path) -> None:
    """Explicit v4 → v5 updates-only cutover; neither runtime reads nor repairs v4."""
    publication = read_pending_publication(repo_root)
    old = json.loads(pending_path(repo_root, UPDATES_FILENAME).read_bytes())
    fields = {"current_works", "deleted_works", *SHARED_FIELDS}
    if (any(publication[field] for field in fields)
            or not isinstance(old, dict) or set(old) != {"header", *fields}
            or not isinstance(old["header"], dict) or set(old["header"]) != {"schema", "last_refreshed_at_utc"}
            or old["header"]["schema"] != "catalogue_updates_pending_v4"
            or old["current_works"] != {} or old["deleted_works"] != {}
            or any(old[field] != [] for field in SHARED_FIELDS)):
        raise ValueError("Complete the v4 Refresh/Regenerate/Publish baseline before Gallery-member cutover")
    value = {
        "header": {"schema": UPDATES_SCHEMA, "last_refreshed_at_utc": old["header"]["last_refreshed_at_utc"]},
        "current_works": {}, "deleted_works": {}, **empty_shared_changes(),
    }
    write_pending_updates(repo_root, value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True)
    parser.parse_args()
    migrate_gallery_member_queue(REPO_ROOT)
    print("Migrated the empty Catalogue updates queue to v5; publication remains v4 and lifecycle timestamps are preserved.")


if __name__ == "__main__":
    main()
