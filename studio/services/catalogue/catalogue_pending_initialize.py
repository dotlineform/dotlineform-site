"""Explicit one-time Catalogue pending-list migration from existing Working data."""

from __future__ import annotations

import json
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

REPO_ROOT = ensure_studio_python_paths(__file__)

from docs_catalogue_media import read_catalogue_work, read_catalogue_work_index  # noqa: E402
from docs_catalogue_source_inventory import catalogue_source_documents  # noqa: E402
from studio.services.catalogue.catalogue_generation_common import compute_payload_version  # noqa: E402
from studio.services.catalogue.catalogue_generation_records import WORK_RECORD_SCHEMA_VERSION  # noqa: E402
from studio.services.catalogue.catalogue_pending_updates import create_pending_updates, pending_updates_path  # noqa: E402


def initialize_pending_updates(repo_root: Path) -> dict[str, int]:
    """Validate all generated Works and source associations before create-only migration."""
    path = pending_updates_path(repo_root)
    if path.exists():
        raise FileExistsError(f"Catalogue pending updates list already exists: {path}")
    works = read_catalogue_work_index(repo_root)
    for work_id in works:
        record = read_catalogue_work(repo_root, work_id)
        header = record.get("header")
        if (not isinstance(header, dict) or header.get("schema") != WORK_RECORD_SCHEMA_VERSION
                or header.get("work_id") != work_id or not isinstance(record.get("sections"), list)
                or header.get("count") != len(record["sections"])
                or header.get("version") != compute_payload_version({
                    "schema": WORK_RECORD_SCHEMA_VERSION, "work": record["work"], "sections": record["sections"],
                })):
            raise ValueError(f"Generated Work {work_id} record is invalid")
    documents = catalogue_source_documents(repo_root)
    deleted = set(documents) - set(works)
    payload = create_pending_updates(repo_root, set(works), deleted)
    return {"current": len(payload["current_work_ids"]), "deleted": len(payload["deleted_work_ids"]),
            "documents": len(documents)}


def main() -> None:
    print(json.dumps(initialize_pending_updates(REPO_ROOT), sort_keys=True))


if __name__ == "__main__":
    main()
