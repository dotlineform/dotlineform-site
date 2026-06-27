#!/usr/bin/env python3
"""Load repo-local runtime environment from .env.local."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Iterable, Mapping


SITE_ENV_REL_PATH = Path(".env.local")


def resolve_repo_root(start: str | Path | None = None) -> Path:
    current = Path(start if start is not None else __file__).expanduser().resolve()
    candidates = [current] if current.is_dir() else [current.parent, *current.parents]
    for candidate in candidates:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate
    raise ValueError("could not resolve repo root for local env")


def strip_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    if not path.is_file():
        raise ValueError(f"env file is not a file: {path}")

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise ValueError(f"invalid env file line {line_number} in {path}")

        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"invalid env var name {key!r} in {path}")
        values[key] = strip_env_value(value.strip())

    return values


def default_site_env_path(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).expanduser().resolve() if repo_root is not None else resolve_repo_root(__file__)
    return root / SITE_ENV_REL_PATH


def load_site_env(repo_root: str | Path | None = None) -> Dict[str, str]:
    return load_env_file(default_site_env_path(repo_root))


def runtime_env(
    *,
    repo_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    env_files: Iterable[Path] | None = None,
) -> Dict[str, str]:
    """Return process env overlaid with repo-local env-file values.

    If .env.local exists, its values win over inherited shell values so
    local runs have one predictable source of repo-specific configuration.
    """

    combined: Dict[str, str] = dict(environ if environ is not None else os.environ)
    files = list(env_files) if env_files is not None else [default_site_env_path(repo_root)]
    for env_file in files:
        combined.update(load_env_file(env_file))
    return combined
