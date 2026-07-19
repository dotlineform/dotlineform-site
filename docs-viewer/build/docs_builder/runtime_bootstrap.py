"""Establish repo-local environment before Docs builder configuration imports."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def apply_repo_local_env(repo_root: str | Path | None = None) -> dict[str, str]:
    root = Path(repo_root).expanduser().resolve() if repo_root is not None else Path.cwd().resolve()
    shared_python_dir = Path(__file__).resolve().parents[3] / "studio" / "shared" / "python"
    shared_python_text = str(shared_python_dir)
    if shared_python_text not in sys.path:
        sys.path.insert(0, shared_python_text)

    from local_env import runtime_env

    values = runtime_env(repo_root=root)
    os.environ.update(values)
    return values


__all__ = ["apply_repo_local_env"]
