"""Generate complete Catalogue JSON and report any missing thumbnails."""

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

from catalogue.catalogue_output_paths import catalogue_output_workspace, output_path
from catalogue.catalogue_media_policy import catalogue_thumbnail_paths
from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, records_from_json_source
from catalogue.generate_work_pages import generate_catalogue_json


def populate_catalogue_output(repo_root: Path, *, write: bool) -> dict:
    """Preserve canonical data and existing media while producing current JSON."""
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    records = records_from_json_source(source_dir)
    workspace = catalogue_output_workspace(repo_root)
    missing = []
    existing_count = 0
    for relative in sorted(catalogue_thumbnail_paths(repo_root, records)):
        destination = output_path(workspace, relative)
        if destination.is_file():
            existing_count += 1
        else:
            missing.append(relative)
    output = generate_catalogue_json(repo_root, source_dir, write=write)
    return {
        "status": "incomplete" if missing else ("completed" if write else "planned"),
        "output": output,
        "thumbnails": {"existing_count": existing_count, "missing": missing},
    }


def main() -> None:
    """Preview by default; --write writes JSON without processing or copying media."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write current Catalogue JSON")
    args = parser.parse_args()
    result = populate_catalogue_output(REPO_ROOT, write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "incomplete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
