"""Establish repo-local environment before Docs builder configuration imports."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECTS_BASE_DIR_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"
DOCS_BASE_DIR_ENV = "DOTLINEFORM_DOCS_BASE_DIR"


def add_workspace_arguments(parser: argparse.ArgumentParser) -> None:
    """Expose independent workspace overrides that take precedence over .env.local."""
    for option, environment in (("projects", PROJECTS_BASE_DIR_ENV), ("docs", DOCS_BASE_DIR_ENV)):
        parser.add_argument(f"--{option}-base-dir", help=f"Override {environment} after loading .env.local.")


def workspace_overrides_from_argv(argv: list[str]) -> dict[str, str | None]:
    """Read workspace overrides before scope-config imports."""

    parser = argparse.ArgumentParser(add_help=False)
    add_workspace_arguments(parser)
    args, _ = parser.parse_known_args(argv)
    return vars(args)


def normalize_base_dir(value: str | Path, *, option: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError(f"--{option}-base-dir must be an absolute path without parent segments")
    return path.resolve()


def workspace_env_overrides(
    *, projects_base_dir: str | Path | None = None, docs_base_dir: str | Path | None = None,
) -> dict[str, str]:
    return {
        environment: str(normalize_base_dir(value, option=option))
        for option, environment, value in (
            ("projects", PROJECTS_BASE_DIR_ENV, projects_base_dir),
            ("docs", DOCS_BASE_DIR_ENV, docs_base_dir),
        )
        if value is not None
    }


def apply_workspace_overrides(args: argparse.Namespace) -> None:
    """Apply parsed overrides for in-process CLI calls without reloading local env."""
    os.environ.update(workspace_env_overrides(
        projects_base_dir=args.projects_base_dir, docs_base_dir=args.docs_base_dir,
    ))


def apply_repo_local_env(
    repo_root: str | Path | None = None,
    *,
    projects_base_dir: str | Path | None = None,
    docs_base_dir: str | Path | None = None,
) -> dict[str, str]:
    root = Path(repo_root).expanduser().resolve() if repo_root is not None else Path.cwd().resolve()
    shared_python_dir = Path(__file__).resolve().parents[3] / "studio" / "shared" / "python"
    shared_python_text = str(shared_python_dir)
    if shared_python_text not in sys.path:
        sys.path.insert(0, shared_python_text)

    from local_env import runtime_env

    values = runtime_env(repo_root=root)
    values.update(workspace_env_overrides(projects_base_dir=projects_base_dir, docs_base_dir=docs_base_dir))
    os.environ.update(values)
    return values


__all__ = [
    "PROJECTS_BASE_DIR_ENV",
    "DOCS_BASE_DIR_ENV",
    "add_workspace_arguments",
    "apply_workspace_overrides",
    "apply_repo_local_env",
    "workspace_overrides_from_argv",
]
