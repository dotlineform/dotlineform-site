"""Peer-service URL helpers for Studio links into Docs Viewer."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode, urlparse

from studio.shared.python.local_env import runtime_env


LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
DEFAULT_DOCS_VIEWER_HOST = "127.0.0.1"
DEFAULT_DOCS_VIEWER_PORT = "8776"
DEFAULT_DOCS_VIEWER_BASE_URL = f"http://{DEFAULT_DOCS_VIEWER_HOST}:{DEFAULT_DOCS_VIEWER_PORT}"


def docs_viewer_base_url(repo_root: Path, environ: dict[str, str] | None = None) -> str:
    env = runtime_env(repo_root=repo_root, environ=environ)
    host = str(env.get("DOCS_VIEWER_HOST") or DEFAULT_DOCS_VIEWER_HOST).strip()
    port = str(env.get("DOCS_VIEWER_PORT") or DEFAULT_DOCS_VIEWER_PORT).strip()
    base_url = str(env.get("DOCS_VIEWER_BASE_URL") or f"http://{host}:{port}").strip().rstrip("/")
    validate_docs_viewer_base_url(base_url)
    return base_url


def validate_docs_viewer_base_url(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS:
        raise ValueError("DOCS_VIEWER_BASE_URL must be an http loopback URL")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("DOCS_VIEWER_BASE_URL must not include a path, query, or fragment")
    if parsed.port is None:
        raise ValueError("DOCS_VIEWER_BASE_URL must include a port")


def docs_viewer_url(repo_root: Path, path: str, query: dict[str, str] | None = None) -> str:
    base = docs_viewer_base_url(repo_root)
    normalized_path = "/" + str(path or "").lstrip("/")
    url = f"{base}{normalized_path}"
    params = {key: value for key, value in (query or {}).items() if value is not None and str(value) != ""}
    if params:
        url = f"{url}?{urlencode(params)}"
    return url


def docs_viewer_manage_url(
    repo_root: Path,
    *,
    scope: str = "",
    doc: str = "",
) -> str:
    query: dict[str, str] = {}
    if scope:
        query["scope"] = scope
    if doc:
        query["doc"] = doc
    query["mode"] = "manage"
    return docs_viewer_url(repo_root, "/docs/", query)


def docs_viewer_service_endpoints(repo_root: Path) -> dict[str, str]:
    base = docs_viewer_base_url(repo_root)
    return {
        "base": base,
        "health": f"{base}/health",
        "generated_index": f"{base}/docs/generated/index",
        "data_sharing_prepare": f"{base}/data-sharing/prepare",
        "data_sharing_returned_packages": f"{base}/data-sharing/returned-packages",
        "data_sharing_review": f"{base}/data-sharing/review",
        "data_sharing_apply": f"{base}/data-sharing/apply",
    }
