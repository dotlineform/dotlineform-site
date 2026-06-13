from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import SiteToolsConfig


@dataclass(frozen=True)
class ValidationResult:
    site_root: Path
    required_file_count: int
    required_directory_count: int
    docs_viewer_runtime_count: int


def resolve_site_root(repo_root: Path, config: SiteToolsConfig, site_root: str | None = None) -> Path:
    raw_site_root = site_root or config.validation.site_root
    path = Path(raw_site_root)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def validate_site(site_root: Path, config: SiteToolsConfig) -> ValidationResult:
    if not site_root.is_dir():
        raise FileNotFoundError(f"site root does not exist: {site_root}")

    missing_files = [
        required
        for required in config.validation.required_files
        if not (site_root / required).is_file()
    ]
    if missing_files:
        raise RuntimeError("site root is missing required files: " + ", ".join(missing_files))

    missing_directories = [
        required
        for required in config.validation.required_directories
        if not (site_root / required).is_dir()
    ]
    if missing_directories:
        raise RuntimeError("site root is missing required directories: " + ", ".join(missing_directories))

    runtime_root = site_root / config.validation.docs_viewer_runtime.root
    runtime_modules = sorted(path.relative_to(runtime_root).as_posix() for path in runtime_root.rglob("*.js"))
    manifest_modules = sorted(config.validation.docs_viewer_runtime.manifest)
    missing_runtime_modules = sorted(set(manifest_modules) - set(runtime_modules))
    extra_runtime_modules = sorted(set(runtime_modules) - set(manifest_modules))
    if missing_runtime_modules:
        raise RuntimeError(
            "public Docs Viewer runtime manifest is missing files: "
            + ", ".join(missing_runtime_modules)
        )
    if extra_runtime_modules:
        raise RuntimeError(
            "public Docs Viewer runtime contains files outside manifest: "
            + ", ".join(extra_runtime_modules)
        )

    return ValidationResult(
        site_root=site_root,
        required_file_count=len(config.validation.required_files),
        required_directory_count=len(config.validation.required_directories),
        docs_viewer_runtime_count=len(runtime_modules),
    )
