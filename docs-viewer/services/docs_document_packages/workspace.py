"""External workspace path contracts for document-package artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Any, Mapping


_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.external_workspace_paths import (  # noqa: E402
    path_is_relative_to,
    resolve_external_workspace_root,
    resolve_workspace_path,
    workspace_marker_path,
)


PROJECTS_BASE_DIR_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"
WORKSPACE_DIR_NAME = "data-sharing"
WORKSPACE_ROOT_MARKER = f"${PROJECTS_BASE_DIR_ENV}/{WORKSPACE_DIR_NAME}"

EXPORT_ROOT = f"{WORKSPACE_ROOT_MARKER}/exports"
IMPORT_STAGING_ROOT = f"{WORKSPACE_ROOT_MARKER}/import-staging"
IMPORT_PREVIEW_ROOT = f"{WORKSPACE_ROOT_MARKER}/import-preview"
META_ROOT = f"{WORKSPACE_ROOT_MARKER}/meta"


@dataclass(frozen=True)
class DocumentPackageWorkspacePaths:
    root: Path
    exports: Path
    import_staging: Path
    import_preview: Path
    meta: Path


def _environment(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if environ is None else environ


def resolve_workspace_root(*, environ: Mapping[str, str] | None = None) -> Path:
    try:
        return resolve_external_workspace_root(
            WORKSPACE_DIR_NAME,
            environ=_environment(environ),
            require_exists=True,
        ).root
    except ValueError as exc:
        message = str(exc)
        if f"{PROJECTS_BASE_DIR_ENV} is required" in message:
            raise ValueError(
                f"{PROJECTS_BASE_DIR_ENV} is required for document packages. "
                f"Set it to an absolute projects directory and create {WORKSPACE_ROOT_MARKER}."
            ) from exc
        if "external workspace does not exist" in message or "does not exist or is not a directory" in message:
            raise ValueError(
                f"Document package workspace does not exist. "
                f"Create {WORKSPACE_ROOT_MARKER} as a readable and writable directory."
            ) from exc
        if "external workspace must be a directory" in message:
            raise ValueError(f"Document package workspace must be a directory: {WORKSPACE_ROOT_MARKER}") from exc
        if "external workspace must be readable and writable" in message:
            raise ValueError(f"Document package workspace must be readable and writable: {WORKSPACE_ROOT_MARKER}") from exc
        raise


def safe_workspace_marker_path(value: Any, *, field: str) -> Path:
    text = str(value or "").strip()
    prefix = f"{WORKSPACE_ROOT_MARKER}/"
    if not text.startswith(prefix):
        raise ValueError(f"Document package path field {field} must be under {WORKSPACE_ROOT_MARKER}")
    relative = Path(text[len(prefix):])
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Document package path field {field} must be under {WORKSPACE_ROOT_MARKER}")
    return relative


def resolve_marker_path(
    value: Any,
    *,
    field: str,
    workspace_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    relative = safe_workspace_marker_path(value, field=field)
    root = (workspace_root or resolve_workspace_root(environ=environ)).resolve()
    workspace = resolve_external_workspace_root(
        WORKSPACE_DIR_NAME,
        environ={PROJECTS_BASE_DIR_ENV: str(root.parent)},
        require_exists=True,
    )
    try:
        return resolve_workspace_path(workspace, relative)
    except ValueError as exc:
        raise ValueError(f"Document package path field {field} resolves outside {WORKSPACE_ROOT_MARKER}") from exc


def marker_path(path: Path, *, workspace_root: Path | None = None) -> str:
    root = (workspace_root or resolve_workspace_root()).resolve()
    workspace = resolve_external_workspace_root(
        WORKSPACE_DIR_NAME,
        environ={PROJECTS_BASE_DIR_ENV: str(root.parent)},
        require_exists=True,
    )
    try:
        return workspace_marker_path(path, workspace)
    except ValueError as exc:
        raise ValueError(f"Document package artifact path is outside {WORKSPACE_ROOT_MARKER}: {path}") from exc


def workspace_paths(*, environ: Mapping[str, str] | None = None) -> DocumentPackageWorkspacePaths:
    root = resolve_workspace_root(environ=environ)
    return DocumentPackageWorkspacePaths(
        root=root,
        exports=root / "exports",
        import_staging=root / "import-staging",
        import_preview=root / "import-preview",
        meta=root / "meta",
    )


def configured_workspace_paths(
    repo_root: Path,
    *,
    config_path: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> DocumentPackageWorkspacePaths:
    del repo_root, config_path
    return workspace_paths(environ=environ)


def workspace_status(
    repo_root: Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    required_paths: tuple[str, ...] = (),
) -> dict[str, Any]:
    try:
        paths = (
            configured_workspace_paths(repo_root, environ=environ)
            if repo_root is not None
            else workspace_paths(environ=environ)
        )
        for path_name in required_paths:
            if path_name not in {"exports", "import_staging", "import_preview", "meta"}:
                raise ValueError(f"Unknown document package workspace path: {path_name}")
            required_path = getattr(paths, path_name)
            display_path = marker_path(required_path, workspace_root=paths.root)
            if not required_path.exists():
                raise ValueError(f"Document package workspace path does not exist: {display_path}")
            if not required_path.is_dir():
                raise ValueError(f"Document package workspace path must be a directory: {display_path}")
            if not os.access(required_path, os.R_OK | os.W_OK):
                raise ValueError(f"Document package workspace path must be readable and writable: {display_path}")
    except (OSError, ValueError) as exc:
        return {
            "available": False,
            "root": WORKSPACE_ROOT_MARKER,
            "message": str(exc),
        }
    return {
        "available": True,
        "root": WORKSPACE_ROOT_MARKER,
        "message": "",
        "paths": {
            "exports": marker_path(paths.exports, workspace_root=paths.root),
            "import_staging": marker_path(paths.import_staging, workspace_root=paths.root),
            "import_preview": marker_path(paths.import_preview, workspace_root=paths.root),
            "meta": marker_path(paths.meta, workspace_root=paths.root),
        },
    }


__all__ = [
    "DocumentPackageWorkspacePaths",
    "EXPORT_ROOT",
    "IMPORT_PREVIEW_ROOT",
    "IMPORT_STAGING_ROOT",
    "META_ROOT",
    "PROJECTS_BASE_DIR_ENV",
    "WORKSPACE_ROOT_MARKER",
    "configured_workspace_paths",
    "marker_path",
    "path_is_relative_to",
    "resolve_marker_path",
    "resolve_workspace_root",
    "safe_workspace_marker_path",
    "workspace_paths",
    "workspace_status",
]
