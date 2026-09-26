"""Save-owned Work/Series titles for the private Works document collection."""

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
# Standalone initial population/repair uses the standard Catalogue bootstrap.
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

REPO_ROOT = ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path  # noqa: E402
from catalogue.catalogue_revisions import record_hash  # noqa: E402
from catalogue.catalogue_source import CatalogueSourceRecords, DEFAULT_SOURCE_DIR, records_from_json_source  # noqa: E402


METADATA_PATH = "reports/works/manifest.json"
METADATA_SCHEMA = "works_collection_metadata_v1"


def _identity(family: str, value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{5}" if family == "works" else r"[0-9]{3}", value):
        raise ValueError(f"Works collection metadata requires an exact {family} ID")
    return value


def _title(family: str, key: str, records: CatalogueSourceRecords) -> str:
    source = getattr(records, family)[_identity(family, key)]
    title = source["title"]
    if source["work_id" if family == "works" else "series_id"] != key or not isinstance(title, str) or not title.strip():
        raise ValueError(f"Invalid Works collection {family} title: {key}")
    return title


def _payload(titles: dict[str, Any]) -> dict[str, Any]:
    return {"header": {"schema": METADATA_SCHEMA, "version": record_hash(titles)}, **titles}


def _read(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Works collection metadata is unavailable; run explicit metadata generation.") from error
    if not isinstance(payload, dict) or set(payload) != {"header", "works", "series"}:
        raise ValueError("Invalid Works collection metadata envelope; regenerate explicitly.")
    header = payload["header"]
    if not isinstance(header, dict) or set(header) != {"schema", "version"} or header["schema"] != METADATA_SCHEMA:
        raise ValueError("Invalid Works collection metadata header; regenerate explicitly.")
    titles = {family: payload[family] for family in ("works", "series")}
    for family, rows in titles.items():
        if not isinstance(rows, dict):
            raise ValueError("Invalid Works collection title map; regenerate explicitly.")
        for key, title in rows.items():
            _identity(family, key)
            if not isinstance(title, str) or not title.strip():
                raise ValueError("Invalid Works collection title; regenerate explicitly.")
    if header["version"] != record_hash(titles):
        raise ValueError("Invalid Works collection metadata revision; regenerate explicitly.")
    return titles


def _write(path: Path, payload: dict[str, Any], *, write: bool) -> bool:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    changed = not path.exists() or path.read_text(encoding="utf-8") != text
    if changed and write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return changed


def generate_works_collection_metadata(repo_root: Path, records: CatalogueSourceRecords, *, write: bool) -> dict[str, Any]:
    """Populate/repair all titles explicitly; never build Docs, Search or media."""
    titles = {family: {key: _title(family, key, records) for key in getattr(records, family)} for family in ("works", "series")}
    path = output_path(catalogue_output_workspace(repo_root), METADATA_PATH)
    changed = _write(path, _payload(titles), write=write)
    return {"status": "completed" if write else "planned", "mode": "complete", "path": METADATA_PATH,
            "work_count": len(titles["works"]), "series_count": len(titles["series"]), "changed": changed, "written": write and changed}


def update_works_collection_metadata(
    repo_root: Path, records: CatalogueSourceRecords, *, work_ids: Sequence[str], series_ids: Sequence[str],
    deleted_work_ids: Sequence[str] = (), deleted_series_ids: Sequence[str] = (), write: bool,
) -> dict[str, Any]:
    """Update only saved identities using Save's loaded records; preserve other titles.

    Deleted IDs must be absent from canonical data. Missing/invalid output fails
    without a rebuild; unchanged projections leave bytes and revision untouched.
    """
    path = output_path(catalogue_output_workspace(repo_root), METADATA_PATH)
    titles = _read(path)
    changed = False
    projected_count = 0
    for family, selected_ids, deleted_ids in (("works", work_ids, deleted_work_ids), ("series", series_ids, deleted_series_ids)):
        selected = {_identity(family, key) for key in selected_ids}
        deleted = {_identity(family, key) for key in deleted_ids}
        if selected & deleted or deleted & getattr(records, family).keys():
            raise ValueError("Works collection metadata deletion must name deleted identities only")
        projected_count += len(selected)
        rows = titles[family]
        for key in sorted(selected):
            title = _title(family, key, records)
            if rows.get(key) != title:
                rows[key] = title
                changed = True
        for key in deleted:
            if key in rows:
                del rows[key]
                changed = True
    if changed:
        _write(path, _payload(titles), write=write)
    return {"status": "completed" if write else "planned", "mode": "targeted", "path": METADATA_PATH,
            "projected_count": projected_count, "changed": changed, "written": write and changed}


def main() -> None:
    """Preview initial population/repair or selected updates; --write applies."""
    parser = argparse.ArgumentParser(description=__doc__)
    for kind in ("work", "series"):
        parser.add_argument(f"--{kind}-id", action="append", default=[], help=f"Update this exact {kind} ID")
        parser.add_argument(f"--deleted-{kind}-id", action="append", default=[], help=f"Remove this deleted {kind} ID")
    parser.add_argument("--write", action="store_true", help="Write private Works collection metadata")
    args = parser.parse_args()
    records = records_from_json_source(REPO_ROOT / DEFAULT_SOURCE_DIR)
    if args.work_id or args.series_id or args.deleted_work_id or args.deleted_series_id:
        result = update_works_collection_metadata(
            REPO_ROOT, records, work_ids=args.work_id, series_ids=args.series_id,
            deleted_work_ids=args.deleted_work_id, deleted_series_ids=args.deleted_series_id, write=args.write,
        )
    else:
        result = generate_works_collection_metadata(REPO_ROOT, records, write=args.write)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
