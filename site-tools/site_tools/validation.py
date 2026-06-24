from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .config import SiteToolsConfig


@dataclass(frozen=True)
class ValidationResult:
    site_root: Path
    required_file_count: int
    required_directory_count: int
    docs_viewer_runtime_count: int
    docs_viewer_route_count: int
    docs_viewer_route_file_count: int


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

    route_count, route_file_count = _validate_docs_viewer_routes(site_root, config)

    return ValidationResult(
        site_root=site_root,
        required_file_count=len(config.validation.required_files),
        required_directory_count=len(config.validation.required_directories),
        docs_viewer_runtime_count=len(runtime_modules),
        docs_viewer_route_count=route_count,
        docs_viewer_route_file_count=route_file_count,
    )


def _validate_docs_viewer_routes(site_root: Path, config: SiteToolsConfig) -> tuple[int, int]:
    route_config_url = config.docs_viewer.get("route_config_url")
    if not isinstance(route_config_url, str) or not route_config_url:
        raise RuntimeError("site-tools config docs_viewer.route_config_url must be a non-empty string")

    route_config_path = site_root / _site_relative_url_path(
        route_config_url,
        context="docs_viewer.route_config_url",
    )
    if not route_config_path.is_file():
        raise RuntimeError(f"Docs Viewer route config is missing: {route_config_path.relative_to(site_root)}")

    data = json.loads(route_config_path.read_text(encoding="utf-8"))
    routes = data.get("routes") if isinstance(data, dict) else None
    if not isinstance(routes, list):
        raise RuntimeError("Docs Viewer route config must contain a routes list")

    missing_files: list[str] = []
    checked_files: set[str] = set()
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise RuntimeError(f"Docs Viewer route config route #{index + 1} must be an object")
        route_id = route.get("route_id")
        if not isinstance(route_id, str) or not route_id:
            route_id = f"#{index + 1}"

        route_path = route.get("route_path")
        if not isinstance(route_path, str) or not route_path:
            raise RuntimeError(f"Docs Viewer route {route_id} must define route_path")

        _check_route_file(site_root, route_id, route_path, checked_files, missing_files)
        for section_name in ("docs_paths", "config_urls"):
            section = route.get(section_name)
            if section is None:
                continue
            if not isinstance(section, dict):
                raise RuntimeError(f"Docs Viewer route {route_id} {section_name} must be an object")
            for field_name, url in section.items():
                if not isinstance(url, str) or not url:
                    raise RuntimeError(f"Docs Viewer route {route_id} {section_name}.{field_name} must be a URL string")
                relative = _site_relative_url_path(
                    url,
                    context=f"Docs Viewer route {route_id} {section_name}.{field_name}",
                )
                checked_files.add(relative)
                if not (site_root / relative).is_file():
                    missing_files.append(f"{route_id} {section_name}.{field_name}: {relative}")

    if missing_files:
        raise RuntimeError("Docs Viewer route config points at missing files: " + ", ".join(missing_files))

    return len(routes), len(checked_files)


def _check_route_file(
    site_root: Path,
    route_id: str,
    route_path: str,
    checked_files: set[str],
    missing_files: list[str],
) -> None:
    relative = _route_path_to_file(route_path, context=f"Docs Viewer route {route_id} route_path")
    checked_files.add(relative)
    if not (site_root / relative).is_file():
        missing_files.append(f"{route_id} route_path: {relative}")


def _route_path_to_file(route_path: str, *, context: str) -> str:
    path = _local_url_path(route_path, context=context, allow_empty=True)
    trimmed = path.strip("/")
    if not trimmed:
        return "index.html"
    if path.endswith("/"):
        return f"{trimmed}/index.html"
    return trimmed


def _site_relative_url_path(url: str, *, context: str) -> str:
    path = _local_url_path(url, context=context, allow_empty=False)
    return path.lstrip("/")


def _local_url_path(url: str, *, context: str, allow_empty: bool) -> str:
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        raise RuntimeError(f"{context} must be a site-root relative URL: {url}")
    path = parsed.path
    if not path.startswith("/"):
        raise RuntimeError(f"{context} must start with /: {url}")
    if not allow_empty and path == "/":
        raise RuntimeError(f"{context} must include a file path: {url}")
    parts = [part for part in path.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        raise RuntimeError(f"{context} must not contain relative path segments: {url}")
    return path
