"""Build captured Preview documents and copy captured Working Search and Recents."""

from pathlib import Path
import argparse
import sys

from docs_builder.runtime_bootstrap import apply_repo_local_env


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-base-dir", type=Path, required=True)
    parser.add_argument("--assets-base-dir", type=Path, required=True)
    parser.add_argument("--search-index", type=Path, required=True, help="Captured Working Search index to copy unchanged.")
    parser.add_argument("--recent-payload", type=Path, required=True, help="Captured Working Recents to copy unchanged.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    apply_repo_local_env(repo_root, docs_base_dir=args.docs_base_dir, assets_base_dir=args.assets_base_dir)
    sys.path.insert(0, str(repo_root / "docs-viewer/services"))
    from docs_write_rebuild import rebuild_stage_outputs

    rebuild_stage_outputs(
        repo_root, stage="preview", copied_search_index=args.search_index.read_bytes(),
        copied_recent_payload=args.recent_payload.read_bytes(),
        docs_base_dir=args.docs_base_dir, assets_base_dir=args.assets_base_dir,
    )


if __name__ == "__main__":
    main()
