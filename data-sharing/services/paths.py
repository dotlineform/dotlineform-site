"""External workspace path contracts for Data Sharing artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping


PROJECTS_BASE_DIR_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"
WORKSPACE_DIR_NAME = "data-sharing"
WORKSPACE_ROOT_MARKER = f"${PROJECTS_BASE_DIR_ENV}/{WORKSPACE_DIR_NAME}"
REGISTRY_REL_PATH = Path("data-sharing/config/adapters.json")

EXPORT_ROOT = f"{WORKSPACE_ROOT_MARKER}/exports"
IMPORT_STAGING_ROOT = f"{WORKSPACE_ROOT_MARKER}/import-staging"
IMPORT_PREVIEW_ROOT = f"{WORKSPACE_ROOT_MARKER}/import-preview"
META_ROOT = f"{WORKSPACE_ROOT_MARKER}/meta"


@dataclass(frozen=True)
class DataSharingWorkspacePaths:
    root: Path
    exports: Path
    import_staging: Path
    import_preview: Path
    meta: Path


def _environment(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if environ is None else environ


def resolve_workspace_root(*, environ: Mapping[str, str] | None = None) -> Path:
    base_text = str(_environment(environ).get(PROJECTS_BASE_DIR_ENV) or "").strip()
    if not base_text:
        raise ValueError(
            f"{PROJECTS_BASE_DIR_ENV} is required for Data Sharing. "
            f"Set it to an absolute projects directory and create {WORKSPACE_ROOT_MARKER}."
        )
    base_path = Path(base_text)
    if not base_path.is_absolute() or ".." in base_path.parts:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV} must be an absolute path without parent segments")
    root = (base_path / WORKSPACE_DIR_NAME).resolve()
    if not root.exists():
        raise ValueError(
            f"Data Sharing workspace does not exist: {root}. "
            f"Create {WORKSPACE_ROOT_MARKER} as a readable and writable directory."
        )
    if not root.is_dir():
        raise ValueError(f"Data Sharing workspace must be a directory: {root}")
    if not os.access(root, os.R_OK | os.W_OK):
        raise ValueError(f"Data Sharing workspace must be readable and writable: {root}")
    return root


def safe_workspace_marker_path(value: Any, *, field: str) -> Path:
    text = str(value or "").strip()
    prefix = f"{WORKSPACE_ROOT_MARKER}/"
    if not text.startswith(prefix):
        raise ValueError(f"Data Sharing config field {field} must be under {WORKSPACE_ROOT_MARKER}")
    relative = Path(text[len(prefix):])
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Data Sharing config field {field} must be under {WORKSPACE_ROOT_MARKER}")
    return relative


def path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_marker_path(
    value: Any,
    *,
    field: str,
    workspace_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    relative = safe_workspace_marker_path(value, field=field)
    root = (workspace_root or resolve_workspace_root(environ=environ)).resolve()
    resolved = (root / relative).resolve()
    if not path_is_relative_to(resolved, root):
        raise ValueError(f"Data Sharing config field {field} resolves outside {WORKSPACE_ROOT_MARKER}")
    return resolved


def marker_path(path: Path, *, workspace_root: Path | None = None) -> str:
    root = (workspace_root or resolve_workspace_root()).resolve()
    resolved = path.resolve()
    if resolved == root:
        return WORKSPACE_ROOT_MARKER
    if not path_is_relative_to(resolved, root):
        raise ValueError(f"Data Sharing artifact path is outside {WORKSPACE_ROOT_MARKER}: {path}")
    return f"{WORKSPACE_ROOT_MARKER}/{resolved.relative_to(root).as_posix()}"


def workspace_paths(*, environ: Mapping[str, str] | None = None) -> DataSharingWorkspacePaths:
    root = resolve_workspace_root(environ=environ)
    return DataSharingWorkspacePaths(
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
) -> DataSharingWorkspacePaths:
    registry_path = repo_root / (Path(config_path) if config_path else REGISTRY_REL_PATH)
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Data Sharing adapter registry is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("paths"), dict):
        raise ValueError("Data Sharing adapter registry paths must be an object")
    configured = payload["paths"]
    root = resolve_workspace_root(environ=environ)
    paths = DataSharingWorkspacePaths(
        root=root,
        exports=resolve_marker_path(
            configured.get("outbound_package_root"),
            field="paths.outbound_package_root",
            workspace_root=root,
        ),
        import_staging=resolve_marker_path(
            configured.get("returned_package_staging_root"),
            field="paths.returned_package_staging_root",
            workspace_root=root,
        ),
        import_preview=resolve_marker_path(
            configured.get("review_output_root"),
            field="paths.review_output_root",
            workspace_root=root,
        ),
        meta=resolve_marker_path(
            configured.get("metadata_root"),
            field="paths.metadata_root",
            workspace_root=root,
        ),
    )
    if len({paths.exports, paths.import_staging, paths.import_preview, paths.meta}) != 4:
        raise ValueError("Data Sharing runtime artifact roots must resolve to distinct workspace paths")
    return paths


def workspace_status(
    repo_root: Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    try:
        paths = (
            configured_workspace_paths(repo_root, environ=environ)
            if repo_root is not None
            else workspace_paths(environ=environ)
        )
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
    "DataSharingWorkspacePaths",
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
