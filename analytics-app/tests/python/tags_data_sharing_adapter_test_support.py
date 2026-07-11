"""Compatibility imports for Analytics tags Data Sharing adapter tests."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "analytics-app" / "tests" / "fixtures"
for path in (FIXTURES_DIR,):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from tag_factory import (  # noqa: E402,F401
    data_sharing_workspace_path,
    make_registry_payload,
    make_tags_repo as make_repo,
    read_json,
    resolve_data_sharing_marker,
    resolve_tags_adapter,
    tags_dependencies as dependencies,
    write_activity_contract,
    write_json,
)
