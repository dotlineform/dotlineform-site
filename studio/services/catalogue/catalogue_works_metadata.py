"""Own private Catalogue Works metadata; Save updates selected rows, never the corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# The standalone command needs the same path bootstrap as other Catalogue tools.
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

REPO_ROOT = ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path  # noqa: E402
from catalogue.catalogue_revisions import record_hash  # noqa: E402
from catalogue.catalogue_source import CatalogueSourceRecords, DEFAULT_SOURCE_DIR, records_from_json_source  # noqa: E402


METADATA_PATH = "reports/catalogue-works/metadata.json"
METADATA_SCHEMA = "catalogue_works_report_metadata_v1"
WORK_FIELDS = ("work_id", "title", "year", "year_display", "storage_location", "medium_type", "medium_caption")


def _work_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{5}", value):
        raise ValueError("Catalogue Works metadata requires an exact five-digit Work ID")
    return value


def _project_work(records: CatalogueSourceRecords, work_id: str) -> dict[str, Any]:
    _work_id(work_id)
    source = records.works[work_id]
    row = {field: source[field] for field in WORK_FIELDS}
    if row["work_id"] != work_id or type(row["year"]) is not int:
        raise ValueError(f"Invalid Catalogue Works metadata identity/year: {work_id}")
    for field in ("title", "year_display"):
        if not isinstance(row[field], str) or not row[field].strip():
            raise ValueError(f"Invalid Catalogue Works metadata {field}: {work_id}")
    for field in ("storage_location", "medium_type", "medium_caption"):
        if row[field] is not None and not isinstance(row[field], str):
            raise ValueError(f"Invalid Catalogue Works metadata {field}: {work_id}")
    row["series"] = []
    if "series_id" in source:
        series_id = source["series_id"]
        if not isinstance(series_id, str) or not re.fullmatch(r"[0-9]{3}", series_id):
            raise ValueError(f"Invalid Catalogue Works Series ID: {work_id}")
        series = records.series[series_id]
        if series["series_id"] != series_id or not isinstance(series["title"], str) or not series["title"].strip():
            raise ValueError(f"Invalid Catalogue Works Series: {series_id}")
        row["series"] = [{"series_id": series_id, "title": series["title"]}]
    return row


def _payload(works: dict[str, Any]) -> dict[str, Any]:
    return {"header": {"schema": METADATA_SCHEMA, "count": len(works), "version": record_hash(works)}, "works": works}


def _read_metadata(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Catalogue Works metadata is unavailable; run explicit metadata generation.") from error
    if not isinstance(payload, dict) or set(payload) != {"header", "works"}:
        raise ValueError("Invalid Catalogue Works metadata envelope; regenerate explicitly.")
    header, works = payload["header"], payload["works"]
    if (not isinstance(header, dict) or set(header) != {"schema", "count", "version"}
            or header["schema"] != METADATA_SCHEMA or not isinstance(works, dict)
            or type(header["count"]) is not int or header["count"] != len(works)
            or not isinstance(header["version"], str) or not re.fullmatch(r"[0-9a-f]{64}", header["version"])):
        raise ValueError("Invalid Catalogue Works metadata header; regenerate explicitly.")
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
    deleted_work_ids: Sequence[str] = (), write: bool,
) -> dict[str, Any]:
    """Project only named saved Works and remove only explicitly deleted IDs.

    Unaffected rows are preserved. Missing/invalid metadata fails without a full
    rebuild; unchanged rows avoid both aggregate writes and revision changes.
    """
    selected = sorted({_work_id(value) for value in work_ids})
    deleted = sorted({_work_id(value) for value in deleted_work_ids})
    if set(selected).intersection(deleted) or any(value in records.works for value in deleted):
        raise ValueError("Catalogue Works metadata deletion must name deleted Works only")
    path = output_path(catalogue_output_workspace(repo_root), METADATA_PATH)
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
