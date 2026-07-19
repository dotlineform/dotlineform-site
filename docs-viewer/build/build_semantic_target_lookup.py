#!/usr/bin/env python3
"""Build Docs Viewer semantic-reference target lookup data."""

from __future__ import annotations

from docs_builder.runtime_bootstrap import apply_repo_local_env

if __name__ == "__main__":
    apply_repo_local_env()

from docs_builder.semantic_target_lookup import main


if __name__ == "__main__":
    raise SystemExit(main())
