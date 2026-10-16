"""Explicit maintenance entrypoint for complete Working regeneration."""

from __future__ import annotations

import argparse
import sys

from docs_builder.runtime_bootstrap import add_workspace_arguments, apply_repo_local_env, apply_workspace_overrides, workspace_overrides_from_argv

if __name__ == "__main__":
    apply_repo_local_env(**workspace_overrides_from_argv(sys.argv[1:]))

from docs_builder.common import REPO_ROOT  # noqa: E402
from docs_working_rebuild import rebuild_working_docs_and_search  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Maintenance: rebuild Working documents, referenced media, Search and Recent. Catalogue regeneration has its own owner.")
    parser.add_argument("--write", action="store_true", required=True, help="Confirm generation and publication-queue writes; this command has no dry-run mode.")
    add_workspace_arguments(parser)
    args = parser.parse_args(argv)
    apply_workspace_overrides(args)
    result = rebuild_working_docs_and_search(REPO_ROOT)
    print("Working rebuild complete." if result["ok"] else result["error"])
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
