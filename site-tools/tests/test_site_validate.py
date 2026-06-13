from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = REPO_ROOT / "site-tools"
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from site_tools.config import load_config
from site_tools.validation import resolve_site_root, validate_site


CONFIG_PATH = REPO_ROOT / "site-tools" / "config" / "site-tools.json"


def test_site_validation_accepts_tracked_site_root() -> None:
    config = load_config(CONFIG_PATH)
    result = validate_site(resolve_site_root(REPO_ROOT, config), config)

    assert result.required_file_count == len(config.validation.required_files)
    assert result.docs_viewer_runtime_count == config.validation.docs_viewer_runtime.expected_module_count


def test_site_validation_rejects_missing_required_file(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)

    with pytest.raises(RuntimeError, match="site root is missing required files"):
        validate_site(tmp_path, config)
