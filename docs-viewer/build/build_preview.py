"""Build captured Preview documents and copy saved Search and freshly prepared Recents."""

from pathlib import Path
import argparse
import sys

from docs_builder.runtime_bootstrap import apply_repo_local_env


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-base-dir", type=Path, required=True)
    parser.add_argument("--assets-base-dir", type=Path, required=True)
    parser.add_argument("--work-assets-base-dir", type=Path, required=True)
    parser.add_argument("--search-index", type=Path, required=True, help="Captured Working Search index to copy unchanged.")
    parser.add_argument("--recent-payload", type=Path, required=True, help="Freshly prepared Recents to copy unchanged.")
    parser.add_argument("--related-links-dir", type=Path, required=True, help="Captured eligible persisted relationship records.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    apply_repo_local_env(repo_root, docs_base_dir=args.docs_base_dir, assets_base_dir=args.assets_base_dir, work_assets_base_dir=args.work_assets_base_dir)
    sys.path.insert(0, str(repo_root / "docs-viewer/services"))
    from docs_write_rebuild import rebuild_stage_outputs

    rebuild_stage_outputs(
        repo_root, stage="preview", copied_search_index=args.search_index.read_bytes(),
        copied_recent_payload=args.recent_payload.read_bytes(),
        docs_base_dir=args.docs_base_dir, assets_base_dir=args.assets_base_dir,
        related_links_dir=args.related_links_dir,
        retained_catalogue=True,
    )


if __name__ == "__main__":
    main()
