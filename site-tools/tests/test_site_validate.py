from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = REPO_ROOT / "site-tools"
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from site_tools.config import load_config
from site_tools.validation import resolve_site_root, validate_site


CONFIG_PATH = REPO_ROOT / "site-tools" / "config" / "site-tools.json"


def test_site_validation_accepts_tracked_site_root() -> None:
    config = load_config(CONFIG_PATH)
    result = validate_site(resolve_site_root(REPO_ROOT, config), config)

    assert result.required_file_count == len(config.validation.required_files)
    assert result.docs_viewer_runtime_count == len(config.validation.docs_viewer_runtime.manifest)
    assert result.docs_viewer_route_count == 3
    assert result.docs_viewer_route_file_count >= result.docs_viewer_route_count


def test_site_validation_rejects_missing_required_file(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)

    with pytest.raises(RuntimeError, match="site root is missing required files"):
        validate_site(tmp_path, config)


def test_site_validation_rejects_extra_docs_viewer_runtime_file(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)
    site_root = resolve_site_root(REPO_ROOT, config)
    runtime_root = _copy_validation_site(site_root, tmp_path, config)
    extra = tmp_path / runtime_root / "management" / "docs-viewer-management.js"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("export {};\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="outside manifest"):
        validate_site(tmp_path, config)


def test_site_validation_rejects_missing_docs_viewer_route_file(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)
    site_root = resolve_site_root(REPO_ROOT, config)
    _copy_validation_site(site_root, tmp_path, config)
    (tmp_path / "moments/index.html").unlink()

    with pytest.raises(RuntimeError, match="moments route_path"):
        validate_site(tmp_path, config)


def test_site_validation_rejects_missing_docs_viewer_route_payload(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)
    site_root = resolve_site_root(REPO_ROOT, config)
    _copy_validation_site(site_root, tmp_path, config)
    (tmp_path / "assets/data/search/moments/index.json").unlink()

    with pytest.raises(RuntimeError, match="moments docs_paths.search_index_url"):
        validate_site(tmp_path, config)


def test_site_validation_rejects_missing_configured_default_doc_payload(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)
    site_root = resolve_site_root(REPO_ROOT, config)
    _copy_validation_site(site_root, tmp_path, config)
    viewer_config = json.loads(
        (tmp_path / "docs-viewer/config/defaults/docs-viewer-public-config.json").read_text(
            encoding="utf-8"
        )
    )
    library = next(scope for scope in viewer_config["scopes"] if scope["scope_id"] == "library")
    (
        tmp_path
        / "assets/data/docs/scopes/library/by-id"
        / f"{library['default_doc_id']}.json"
    ).unlink()

    with pytest.raises(RuntimeError, match="library default document"):
        validate_site(tmp_path, config)


def _copy_validation_site(site_root: Path, target_root: Path, config) -> str:
    for required in config.validation.required_files:
        _copy_file(site_root, target_root, required)

    runtime_root = config.validation.docs_viewer_runtime.root
    for required in config.validation.docs_viewer_runtime.manifest:
        _copy_file(site_root, target_root, f"{runtime_root}/{required}")

    for required in config.validation.required_directories:
        (target_root / required).mkdir(parents=True, exist_ok=True)

    _copy_docs_viewer_route_files(site_root, target_root, config)
    return runtime_root


def _copy_docs_viewer_route_files(site_root: Path, target_root: Path, config) -> None:
    route_config = _site_relative_url_path(config.docs_viewer["route_config_url"])
    route_config_path = site_root / route_config
    data = json.loads(route_config_path.read_text(encoding="utf-8"))
    viewer_config_path = _site_relative_url_path(data["routes"][0]["config_urls"]["docs_viewer"])
    viewer_config = json.loads((site_root / viewer_config_path).read_text(encoding="utf-8"))
    scopes = {scope["scope_id"]: scope for scope in viewer_config["scopes"]}
    for route in data["routes"]:
        _copy_file(site_root, target_root, _route_path_to_file(route["route_path"]))
        for section_name in ("docs_paths", "config_urls"):
            for url in route.get(section_name, {}).values():
                _copy_file(site_root, target_root, _site_relative_url_path(url))
        default_doc_id = scopes[route["default_scope_id"]]["default_doc_id"]
        if default_doc_id:
            docs_root = Path(_site_relative_url_path(route["docs_paths"]["index_tree_url"])).parent
            _copy_file(site_root, target_root, (docs_root / "by-id" / f"{default_doc_id}.json").as_posix())


def _copy_file(site_root: Path, target_root: Path, relative: str) -> None:
    source = site_root / relative
    target = target_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def _route_path_to_file(route_path: str) -> str:
    path = urlparse(route_path).path
    trimmed = path.strip("/")
    if not trimmed:
        return "index.html"
    if path.endswith("/"):
        return f"{trimmed}/index.html"
    return trimmed


def _site_relative_url_path(url: str) -> str:
    return urlparse(url).path.lstrip("/")
