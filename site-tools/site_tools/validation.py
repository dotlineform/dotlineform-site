from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from site_code_update import Projection, SiteCodeUpdateError, load_manifest

from .config import SiteToolsConfig


DOCS_VIEWER_ROUTE_FEATURE_IDS = {
    "configured-scope-discovery",
    "scope-selection",
    "search",
    "recent",
    "bookmarks",
    "reports",
    "source-editing",
    "management",
}
SITE_CODE_MANIFEST = Path("site-tools/config/site-code-update.json")
DOCS_VIEWER_RUNTIME_ROOT = Path("docs-viewer/runtime/js")


@dataclass(frozen=True)
class ValidationResult:
    site_root: Path
    required_file_count: int
    required_directory_count: int
    site_code_projection_count: int
    docs_viewer_runtime_count: int
    docs_viewer_route_count: int
    docs_viewer_route_file_count: int


def resolve_site_root(repo_root: Path, config: SiteToolsConfig, site_root: str | None = None) -> Path:
    raw_site_root = site_root or config.validation.site_root
    path = Path(raw_site_root)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def validate_site(
    site_root: Path,
    config: SiteToolsConfig,
    *,
    repo_root: Path,
) -> ValidationResult:
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

    projection_count, runtime_count = _validate_site_code_projection(
        repo_root.resolve(),
        site_root,
    )

    route_count, route_file_count = _validate_docs_viewer_routes(site_root, config)

    return ValidationResult(
        site_root=site_root,
        required_file_count=len(config.validation.required_files),
        required_directory_count=len(config.validation.required_directories),
        site_code_projection_count=projection_count,
        docs_viewer_runtime_count=runtime_count,
        docs_viewer_route_count=route_count,
        docs_viewer_route_file_count=route_file_count,
    )


def _validate_site_code_projection(repo_root: Path, site_root: Path) -> tuple[int, int]:
    try:
        projections = load_manifest(repo_root, repo_root / SITE_CODE_MANIFEST)
    except SiteCodeUpdateError as exc:
        raise RuntimeError(f"site code projection manifest is invalid: {exc}") from exc
    expected_runtime: set[str] = set()
    missing: list[str] = []
    extra: list[str] = []
    changed: list[str] = []
    unsafe: list[str] = []

    for projection in projections:
        destination_root = _site_relative_projection_root(projection)
        source_root = repo_root / projection.source_root
        target_root = site_root / destination_root
        expected_names = set(projection.files)
        actual_names: set[str] = set()
        if target_root.is_symlink():
            unsafe.append(destination_root.as_posix())
        elif target_root.is_dir():
            for target in sorted(target_root.iterdir(), key=lambda path: path.name):
                relative = (destination_root / target.name).as_posix()
                if target.is_symlink() or not target.is_file():
                    unsafe.append(relative)
                    continue
                actual_names.add(target.name)
        elif target_root.exists():
            unsafe.append(destination_root.as_posix())

        missing.extend(
            (destination_root / filename).as_posix()
            for filename in sorted(expected_names - actual_names)
        )
        extra.extend(
            (destination_root / filename).as_posix()
            for filename in sorted(actual_names - expected_names)
        )
        for filename in sorted(expected_names & actual_names):
            target_relative = destination_root / filename
            if (source_root / filename).read_bytes() != (site_root / target_relative).read_bytes():
                changed.append(target_relative.as_posix())
        if destination_root.is_relative_to(DOCS_VIEWER_RUNTIME_ROOT):
            expected_runtime.update(
                (destination_root / filename)
                .relative_to(DOCS_VIEWER_RUNTIME_ROOT)
                .as_posix()
                for filename in projection.files
            )

    runtime_root = site_root / DOCS_VIEWER_RUNTIME_ROOT
    actual_runtime: set[str] = set()
    if runtime_root.is_symlink():
        unsafe.append(DOCS_VIEWER_RUNTIME_ROOT.as_posix())
    elif runtime_root.is_dir():
        for target in runtime_root.rglob("*"):
            relative = target.relative_to(runtime_root).as_posix()
            if target.is_symlink():
                unsafe.append((DOCS_VIEWER_RUNTIME_ROOT / relative).as_posix())
            elif target.is_file():
                actual_runtime.add(relative)
    extra.extend(
        (DOCS_VIEWER_RUNTIME_ROOT / relative).as_posix()
        for relative in sorted(actual_runtime - expected_runtime)
    )

    if unsafe:
        raise RuntimeError(
            "site code projection contains unsafe entries: " + ", ".join(sorted(set(unsafe)))
        )
    if missing:
        raise RuntimeError(
            "site code projection is missing files: " + ", ".join(sorted(set(missing)))
        )
    if extra:
        raise RuntimeError(
            "public Docs Viewer runtime contains files outside manifest: "
            + ", ".join(sorted(set(extra)))
        )
    if changed:
        raise RuntimeError(
            "site code projection differs from canonical source: "
            + ", ".join(sorted(set(changed)))
        )
    return sum(len(projection.files) for projection in projections), len(expected_runtime)


def _site_relative_projection_root(projection: Projection) -> Path:
    destination = PurePosixPath(projection.destination_root)
    if not destination.parts or destination.parts[0] != "site":
        raise RuntimeError(
            f"site code projection destination must be under site/: {projection.destination_root}"
        )
    return Path(*destination.parts[1:])


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
        raw_features = route.get("features")
        if not isinstance(raw_features, list) or not all(isinstance(item, str) for item in raw_features):
            raise RuntimeError(f"Docs Viewer route {route_id} must define a features string array")
        features = set(raw_features)
        unknown_features = sorted(features - DOCS_VIEWER_ROUTE_FEATURE_IDS)
        if unknown_features:
            raise RuntimeError(f"Docs Viewer route {route_id} has unknown features: {', '.join(unknown_features)}")
        if "scope-selection" in features and "configured-scope-discovery" not in features:
            raise RuntimeError(
                f"Docs Viewer route {route_id} scope-selection requires configured-scope-discovery"
            )
        required_fields = {
            ("docs_paths", "index_tree_url"),
            ("config_urls", "docs_viewer"),
        }
        if "search" in features:
            required_fields.add(("docs_paths", "search_index_url"))
        recent_basis = route.get("recent_basis")
        if "recent" in features:
            required_fields.add(("docs_paths", "recent_url"))
            if recent_basis not in {"added", "edited"}:
                raise RuntimeError(
                    f"Docs Viewer route {route_id} with Recent enabled must define recent_basis as added or edited"
                )
        elif recent_basis:
            raise RuntimeError(f"Docs Viewer route {route_id} cannot define recent_basis without Recent")
        if "reports" in features:
            required_fields.add(("config_urls", "report_registry"))
        for section_name, field_name in required_fields:
            section = route.get(section_name)
            if not isinstance(section, dict) or not isinstance(section.get(field_name), str) or not section[field_name]:
                raise RuntimeError(f"Docs Viewer route {route_id} must define {section_name}.{field_name}")
        for section_name in ("docs_paths", "config_urls"):
            section = route.get(section_name)
            if section is None:
                continue
            if not isinstance(section, dict):
                raise RuntimeError(f"Docs Viewer route {route_id} {section_name} must be an object")
            for field_name, url in section.items():
                if not isinstance(url, str):
                    raise RuntimeError(f"Docs Viewer route {route_id} {section_name}.{field_name} must be a URL string")
                if not url:
                    if (section_name, field_name) in required_fields:
                        raise RuntimeError(f"Docs Viewer route {route_id} {section_name}.{field_name} must be a URL string")
                    continue
                relative = _site_relative_url_path(
                    url,
                    context=f"Docs Viewer route {route_id} {section_name}.{field_name}",
                )
                checked_files.add(relative)
                if not (site_root / relative).is_file():
                    missing_files.append(f"{route_id} {section_name}.{field_name}: {relative}")

        default_doc_payload = _docs_viewer_default_doc_payload(site_root, route_id, route)
        if default_doc_payload:
            checked_files.add(default_doc_payload)
            if not (site_root / default_doc_payload).is_file():
                missing_files.append(f"{route_id} default document: {default_doc_payload}")

    if missing_files:
        raise RuntimeError("Docs Viewer route config points at missing files: " + ", ".join(missing_files))

    return len(routes), len(checked_files)


def _docs_viewer_default_doc_payload(site_root: Path, route_id: str, route: dict) -> str:
    default_scope_id = route.get("default_scope_id")
    if not isinstance(default_scope_id, str) or not default_scope_id:
        raise RuntimeError(f"Docs Viewer route {route_id} must define default_scope_id")
    config_url = (route.get("config_urls") or {}).get("docs_viewer")
    config_path = site_root / _site_relative_url_path(
        config_url,
        context=f"Docs Viewer route {route_id} config_urls.docs_viewer",
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    scopes = config.get("scopes") if isinstance(config, dict) else None
    if not isinstance(scopes, list):
        raise RuntimeError(f"Docs Viewer config for route {route_id} must contain a scopes list")
    scope = next(
        (
            item
            for item in scopes
            if isinstance(item, dict) and item.get("scope_id") == default_scope_id
        ),
        None,
    )
    if scope is None:
        raise RuntimeError(
            f"Docs Viewer config for route {route_id} is missing scope {default_scope_id}"
        )
    default_doc_id = scope.get("default_doc_id")
    if not isinstance(default_doc_id, str):
        raise RuntimeError(
            f"Docs Viewer config scope {default_scope_id} default_doc_id must be a string"
        )
    if not default_doc_id:
        return ""
    index_tree_url = (route.get("docs_paths") or {}).get("index_tree_url")
    index_tree_path = Path(
        _site_relative_url_path(
            index_tree_url,
            context=f"Docs Viewer route {route_id} docs_paths.index_tree_url",
        )
    )
    return (index_tree_path.parent / "by-id" / f"{default_doc_id}.json").as_posix()


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
