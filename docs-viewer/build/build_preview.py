"""Build captured Preview inputs in an explicit temporary Docs workspace."""

from pathlib import Path
import argparse
import sys

from docs_builder.runtime_bootstrap import apply_repo_local_env


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-base-dir", type=Path, required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    apply_repo_local_env(repo_root, docs_base_dir=args.docs_base_dir)
    sys.path.insert(0, str(repo_root / "docs-viewer/services"))
    from docs_write_rebuild import rebuild_stage_outputs

    rebuild_stage_outputs(repo_root, stage="preview", include_search=True, docs_base_dir=args.docs_base_dir)


if __name__ == "__main__":
    main()
