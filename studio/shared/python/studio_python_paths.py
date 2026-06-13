"""Python import path bootstrap for Studio-owned source modules."""

from __future__ import annotations

import sys
from pathlib import Path


def resolve_repo_root(start: str | Path | None = None) -> Path:
    current = Path(start if start is not None else __file__).expanduser().resolve()
    candidates = [current] if current.is_dir() else [current.parent, *current.parents]
    for candidate in candidates:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate
    raise ValueError("could not resolve repo root")


def ensure_studio_python_paths(start: str | Path | None = None) -> Path:
    repo_root = resolve_repo_root(start)
    paths = [
        repo_root / "studio" / "shared" / "python",
        repo_root / "studio" / "app" / "server",
        repo_root / "studio" / "services",
        repo_root / "docs-viewer" / "services",
        repo_root / "data-sharing",
    ]
    for path in reversed(paths):
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)
    return repo_root
