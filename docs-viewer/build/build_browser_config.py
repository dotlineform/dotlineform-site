#!/usr/bin/env python3
"""Project design-time workspace configuration for local and public readers."""

from __future__ import annotations

import argparse
from pathlib import Path

from docs_builder.runtime_bootstrap import apply_repo_local_env

if __name__ == "__main__":
    apply_repo_local_env()

from docs_builder.browser_config import write_browser_config  # noqa: E402
from docs_builder.common import (  # noqa: E402
    DOCS_VIEWER_BROWSER_CONFIG_PATH,
    DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
    load_docs_workspace_config,
)


def main() -> int:
    """Write both canonical browser projections without building user data or site output."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    repo_root = Path.cwd().resolve()
    workspace = load_docs_workspace_config(repo_root)
    write_browser_config(repo_root, workspace, path=DOCS_VIEWER_BROWSER_CONFIG_PATH, label="Docs Viewer browser config")
    write_browser_config(repo_root, workspace, path=DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
                         label="Docs Viewer public browser config", published=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
