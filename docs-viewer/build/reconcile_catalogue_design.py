"""Explicit Catalogue source/document maintenance following design changes."""

from pathlib import Path
import argparse
import json
import sys

from docs_builder.runtime_bootstrap import apply_repo_local_env


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write Working documents and queue completed publication changes.")
    parser.add_argument("--seed-work-snapshots", type=Path, metavar="SELECTION_JSON",
                        help="Prepare the supplied work_ids without changing Catalogue sources. Omit --write to preview.")
    args = parser.parse_args()
    if not args.write and not args.seed_work_snapshots:
        parser.error("design reconciliation requires --write")
    root = Path(__file__).resolve().parents[2]
    apply_repo_local_env(root)
    sys.path.insert(0, str(root / "docs-viewer/services"))
    from docs_catalogue_regeneration import reconcile_catalogue_design, seed_catalogue_work_snapshots

    if args.seed_work_snapshots:
        work_ids = json.loads(args.seed_work_snapshots.read_bytes())["work_ids"]
        result = seed_catalogue_work_snapshots(root, work_ids, write=args.write)
        print(f"Prepared {result['docs_emitted']} Catalogue Work snapshots.")
    else:
        print(reconcile_catalogue_design(root)["summary_text"])


if __name__ == "__main__":
    main()
