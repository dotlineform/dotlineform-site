"""Explicit command for the mutation-selected Catalogue Refresh handoff."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)
from catalogue.catalogue_refresh_service import refresh_catalogue, refresh_private_report_inputs  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True)
    parser.add_argument("--private-report-inputs", action="store_true", help="Refresh only the three private report inputs; preserve unrelated queue work")
    args = parser.parse_args()
    result = refresh_private_report_inputs(ROOT) if args.private_report_inputs else refresh_catalogue(ROOT)
    print(f"Catalogue Refresh completed: {len(result['output']['written'])} writes, {len(result['output']['deleted'])} deletions.")


if __name__ == "__main__":
    main()
