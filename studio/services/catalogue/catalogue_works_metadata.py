"""Own private Catalogue Works metadata; Refresh updates supplied Work rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# The standalone command needs the same path bootstrap as other Catalogue tools.
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

REPO_ROOT = ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path  # noqa: E402
from catalogue.catalogue_source import CatalogueSourceRecords, DEFAULT_SOURCE_DIR, records_from_json_source  # noqa: E402
from docs_artifact_locations import ArtifactLocation  # noqa: E402


METADATA_PATH = "reports/catalogue-works/metadata.json"
METADATA_SCHEMA = "catalogue_works_report_metadata_v3"
WORK_FIELDS = ("work_id", "title", "year", "year_display")


def _project_work(records: CatalogueSourceRecords, work_id: str) -> dict[str, Any]:
    source = records.works[work_id]
    row = {field: source[field] for field in WORK_FIELDS}
    for field in ("storage_location", "medium", "project_folder", "project_subfolder", "project_filename"):
        row[field] = source.get(field)
    row["series"] = []
    if "series_id" in source:
        series_id = source["series_id"]
        series = records.series[series_id]
        row["series"] = [{"series_id": series_id, "title": series["title"]}]
    return row


def _payload(works: dict[str, Any]) -> dict[str, Any]:
    return {"header": {"schema": METADATA_SCHEMA}, "works": works}


def _read_metadata(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Catalogue Works metadata is unavailable; run explicit metadata generation.") from error
    return payload


def _write(path: Path, payload: dict[str, Any], *, write: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def generate_catalogue_works_metadata(repo_root: Path, records: CatalogueSourceRecords, *, write: bool) -> dict[str, Any]:
    """Explicitly generate the complete aggregate, including initial population/repair.

    Writes only private report metadata; never invokes media, Docs or Search work.
    """
    path = output_path(catalogue_output_workspace(repo_root), METADATA_PATH)
    works = {work_id: _project_work(records, work_id) for work_id in records.works}
    payload = _payload(works)
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    changed = not path.exists() or path.read_text(encoding="utf-8") != text
    if changed:
        _write(path, payload, write=write)
    return {"status": "completed" if write else "planned", "mode": "complete", "path": METADATA_PATH,
            "count": len(works), "projected_count": len(works), "changed": changed, "written": write and changed}


def update_catalogue_works_metadata(
    repo_root: Path, records: CatalogueSourceRecords, *, work_ids: Sequence[str],
    deleted_work_ids: Sequence[str] = (), write: bool, workspace: ArtifactLocation | None = None,
) -> dict[str, Any]:
    """Project only named saved Works and remove only explicitly deleted IDs.

    Trust supplied identities and authored/saved values without content checks.
    Unaffected rows survive and unchanged rows avoid writes. Unreadable metadata
    fails without full rebuilding; no complete-content hash is computed.
    """
    selected, deleted = work_ids, deleted_work_ids
    workspace = catalogue_output_workspace(repo_root) if workspace is None else workspace
    path = output_path(workspace, METADATA_PATH)
    payload = _read_metadata(path)
    works = payload["works"]
    updated, removed = [], []
    for work_id in selected:
        row = _project_work(records, work_id)
        if works.get(work_id) != row:
            works[work_id] = row
            updated.append(work_id)
    for work_id in deleted:
        if work_id in works:
            del works[work_id]
            removed.append(work_id)
    changed = bool(updated or removed)
    if changed:
        _write(path, _payload(works), write=write)
    return {"status": "completed" if write else "planned", "mode": "targeted", "path": METADATA_PATH,
            "count": len(works), "projected_count": len(selected), "updated_work_ids": updated,
            "deleted_work_ids": removed, "changed": changed, "written": write and changed}


def main() -> None:
    """Preview complete generation by default, or explicit row updates; --write applies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-id", action="append", default=[], help="Update this exact Work ID; repeat to select several")
    parser.add_argument("--deleted-work-id", action="append", default=[], help="Remove this deleted Work ID; repeat as needed")
    parser.add_argument("--write", action="store_true", help="Write the private report metadata")
    args = parser.parse_args()
    records = records_from_json_source(REPO_ROOT / DEFAULT_SOURCE_DIR)
    if args.work_id or args.deleted_work_id:
        result = update_catalogue_works_metadata(
            REPO_ROOT, records, work_ids=args.work_id, deleted_work_ids=args.deleted_work_id, write=args.write,
        )
    else:
        result = generate_catalogue_works_metadata(REPO_ROOT, records, write=args.write)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
