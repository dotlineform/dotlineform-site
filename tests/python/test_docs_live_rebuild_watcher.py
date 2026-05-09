#!/usr/bin/env python3
"""Focused checks for Docs live rebuild watcher imports."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WATCHER_PATH = REPO_ROOT / "scripts" / "docs" / "docs_live_rebuild_watcher.py"


def load_docs_live_rebuild_watcher_module():
    scripts_docs_dir = WATCHER_PATH.parent
    if str(scripts_docs_dir) not in sys.path:
        sys.path.insert(0, str(scripts_docs_dir))
    spec = importlib.util.spec_from_file_location("docs_live_rebuild_watcher", WATCHER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load docs_live_rebuild_watcher.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_watcher_imports_source_model_helpers_directly() -> None:
    module = load_docs_live_rebuild_watcher_module()

    assert callable(module.load_scope_docs)
    assert callable(module.scope_doc_sort_key)
    assert module.load_scope_docs.__module__ == "docs_source_model"
    assert module.scope_doc_sort_key.__module__ == "docs_source_model"


def main() -> None:
    test_watcher_imports_source_model_helpers_directly()


if __name__ == "__main__":
    main()
