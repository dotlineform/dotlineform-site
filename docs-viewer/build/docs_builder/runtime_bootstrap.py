"""Establish repo-local environment before Docs builder configuration imports."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECTS_BASE_DIR_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"


def projects_base_dir_from_argv(argv: list[str]) -> str | None:
    """Read the explicit Projects-base override before scope-config imports."""

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--projects-base-dir")
    args, _ = parser.parse_known_args(argv)
    return args.projects_base_dir


def normalize_projects_base_dir(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("--projects-base-dir must be an absolute path without parent segments")
    return path.resolve()


def apply_projects_base_dir_override(value: str | Path) -> Path:
    path = normalize_projects_base_dir(value)
    os.environ[PROJECTS_BASE_DIR_ENV] = str(path)
    return path


def apply_repo_local_env(
    repo_root: str | Path | None = None,
    *,
    projects_base_dir: str | Path | None = None,
) -> dict[str, str]:
    root = Path(repo_root).expanduser().resolve() if repo_root is not None else Path.cwd().resolve()
    shared_python_dir = Path(__file__).resolve().parents[3] / "studio" / "shared" / "python"
    shared_python_text = str(shared_python_dir)
    if shared_python_text not in sys.path:
        sys.path.insert(0, shared_python_text)

    from local_env import runtime_env

    values = runtime_env(repo_root=root)
    if projects_base_dir is not None:
        values[PROJECTS_BASE_DIR_ENV] = str(normalize_projects_base_dir(projects_base_dir))
    os.environ.update(values)
    return values


__all__ = [
    "PROJECTS_BASE_DIR_ENV",
    "apply_projects_base_dir_override",
    "apply_repo_local_env",
    "normalize_projects_base_dir",
    "projects_base_dir_from_argv",
]
