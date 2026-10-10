"""Explicit command for the mutation-selected Catalogue Refresh handoff."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)
from catalogue.catalogue_refresh_service import refresh_catalogue, refresh_compact_indexes, refresh_gallery_records, refresh_private_report_inputs, refresh_series_galleries, refresh_work_document_coverage  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True)
    maintenance = parser.add_mutually_exclusive_group()
    maintenance.add_argument("--private-report-inputs", action="store_true", help="Refresh only the three private report inputs; preserve unrelated queue work")
    maintenance.add_argument("--work-document-coverage", action="store_true", help="Explicitly generate/repair only the private Series/member-Work coverage manifest")
    maintenance.add_argument("--compact-indexes", action="store_true", help="Explicitly generate/repair both compact indexes and queue their publication")
    maintenance.add_argument("--series-galleries", action="store_true", help="Explicitly generate/repair the relationship index and private report")
    maintenance.add_argument("--gallery-records", action="store_true", help="Explicitly generate/repair complete Gallery by-ID records")
    args = parser.parse_args()
    if args.gallery_records:
        result = refresh_gallery_records(ROOT)
    elif args.series_galleries:
        result = refresh_series_galleries(ROOT)
    elif args.compact_indexes:
        result = refresh_compact_indexes(ROOT)
    elif args.private_report_inputs:
        result = refresh_private_report_inputs(ROOT)
    elif args.work_document_coverage:
        result = refresh_work_document_coverage(ROOT)
    else:
        result = refresh_catalogue(ROOT)
    print(f"Catalogue Refresh completed: {len(result['output']['written'])} writes, {len(result['output']['deleted'])} deletions.")


if __name__ == "__main__":
    main()
