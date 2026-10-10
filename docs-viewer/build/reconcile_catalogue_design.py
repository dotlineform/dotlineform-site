"""Explicit Catalogue source/document maintenance following design changes."""

from pathlib import Path
import argparse
import sys

from docs_builder.runtime_bootstrap import apply_repo_local_env


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", required=True, help="Reconcile Working Catalogue documents and queue completed publication changes.")
    parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    apply_repo_local_env(root)
    sys.path.insert(0, str(root / "docs-viewer/services"))
    from docs_catalogue_regeneration import reconcile_catalogue_design

    print(reconcile_catalogue_design(root)["summary_text"])


if __name__ == "__main__":
    main()
