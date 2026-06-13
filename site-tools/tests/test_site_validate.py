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
    assert result.docs_viewer_runtime_count == len(config.validation.docs_viewer_runtime.manifest)


def test_site_validation_rejects_missing_required_file(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)

    with pytest.raises(RuntimeError, match="site root is missing required files"):
        validate_site(tmp_path, config)


def test_site_validation_rejects_extra_docs_viewer_runtime_file(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)
    site_root = resolve_site_root(REPO_ROOT, config)
    for required in config.validation.required_files:
        source = site_root / required
        target = tmp_path / required
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    runtime_root = config.validation.docs_viewer_runtime.root
    for required in config.validation.docs_viewer_runtime.manifest:
        source = site_root / runtime_root / required
        target = tmp_path / runtime_root / required
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    for required in config.validation.required_directories:
        (tmp_path / required).mkdir(parents=True, exist_ok=True)
    extra = tmp_path / runtime_root / "management" / "docs-viewer-management.js"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("export {};\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="outside manifest"):
        validate_site(tmp_path, config)
