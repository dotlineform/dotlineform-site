"""Explicit full Catalogue regeneration for initial population and maintenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_media import complete_catalogue_media
from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from catalogue.catalogue_service_context import build_catalogue_write_context, refresh_lookup_payloads
from catalogue.catalogue_source import records_from_json_source
from catalogue.generate_work_pages import generate_catalogue_json


def main() -> None:
    """Preview by default; --write explicitly completes media and generated JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Apply the complete regeneration, including remote media")
    args = parser.parse_args()
    context = build_catalogue_write_context(REPO_ROOT)
    records = records_from_json_source(context.source_dir)
    workspace = catalogue_output_workspace(REPO_ROOT)
    work_ids = sorted(set(records.works) | {path.stem for path in output_path(workspace, "works/index").glob("*.json")})
    media = complete_catalogue_media(
        REPO_ROOT, context.source_dir, records=records, previous=None, work_ids=work_ids, write=args.write,
    )
    output = generate_catalogue_json(REPO_ROOT, context.source_dir, write=args.write)
    if args.write:
        refresh_lookup_payloads(context)
    print(json.dumps({"media": media, "output": output}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
