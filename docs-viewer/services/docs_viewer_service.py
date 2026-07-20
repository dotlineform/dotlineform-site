#!/usr/bin/env python3
"""Serve the standalone local Docs Viewer shell and management API."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import mimetypes
import os
import re
import shlex
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse, urlsplit

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.local_browser_assets import (
    LOCAL_BROWSER_ASSET_PATHS,
    render_local_browser_icon_links,
)
from studio.shared.python.local_http_logging import QuietErrorLoggingMixin
from studio.shared.python.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

import docs_management_routes as routes  # noqa: E402
import docs_management_service as docs_service  # noqa: E402
import docs_document_package_routes as package_routes  # noqa: E402
from docs_document_packages import service as package_service  # noqa: E402
import docs_media_storage as media_storage  # noqa: E402
import docs_review_routes as review_routes  # noqa: E402
import docs_review_service as review_service  # noqa: E402
from local_env import SITE_ENV_REL_PATH  # noqa: E402


ENABLED_VALUES = {"1", "on", "true", "yes"}
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
DEFAULT_SERVICE_CONFIG = REPO_ROOT / "docs-viewer" / "config" / "defaults" / "docs-viewer-service.json"
MANAGE_PAGE_TEMPLATE = REPO_ROOT / "docs-viewer" / "shell" / "docs-viewer-manage.html"
REVIEW_PAGE_TEMPLATE = REPO_ROOT / "docs-viewer" / "shell" / "docs-viewer-review.html"
MANAGE_ROUTE = "/docs/"
REVIEW_ROUTE = "/docs-review/"
STATIC_PREFIXES = (
    "/assets/data/",
    "/assets/docs/",
    "/docs-viewer/config/",
    "/docs-viewer/data/generated/",
    "/docs-viewer/static/",
)
SCOPE_PUBLISHED_STATIC_PATTERN = re.compile(
    r"\A/docs-viewer/scopes/[a-z][a-z0-9-]*/published/(?:documents|media|search)(?:/|\Z)"
)
RUNTIME_STATIC_ROUTES = (
    ("/docs-viewer/runtime/vendor/", Path("docs-viewer/runtime/vendor")),
    ("/docs-viewer/runtime/js/public/", Path("site/docs-viewer/runtime/js/public")),
    ("/docs-viewer/runtime/js/shared/", Path("site/docs-viewer/runtime/js/shared")),
    ("/docs-viewer/runtime/js/management/", Path("docs-viewer/runtime/js/management")),
    ("/docs-viewer/runtime/js/review/", Path("docs-viewer/runtime/js/review")),
    ("/docs-viewer/runtime/js/import/", Path("docs-viewer/runtime/js/import")),
    ("/docs-viewer/runtime/js/reports/", Path("docs-viewer/runtime/js/reports")),
    ("/docs-viewer/runtime/js/local/", Path("docs-viewer/runtime/js/local")),
)
SHARED_STATIC_ROUTES = {
    "/docs-viewer/static/css/docs-viewer.css": Path("site/docs-viewer/static/css/docs-viewer.css"),
    "/docs-viewer/static/css/docs-viewer-reports.css": Path(
        "site/docs-viewer/static/css/docs-viewer-reports.css"
    ),
    "/docs-viewer/static/css/docs-viewer-moments.css": Path(
        "site/docs-viewer/static/css/docs-viewer-moments.css"
    ),
    "/docs-viewer/config/routes/docs-viewer-public-routes.json": Path(
        "site/docs-viewer/config/routes/docs-viewer-public-routes.json"
    ),
}
STATIC_FILES = set(LOCAL_BROWSER_ASSET_PATHS)
RETIRED_STATIC_PATHS = {
    "/docs-viewer/runtime/js/docs-viewer.js",
    "/docs-viewer/static/css/docs-viewer-base.css",
    "/docs-viewer/static/css/docs-viewer-management.css",
    "/docs-viewer/static/css/docs-viewer-public.css",
}
MAX_BODY_BYTES = 1024 * 1024
GENERATED_READ_PATHS = {
    routes.GENERATED_INDEX_TREE_PATH,
    routes.GENERATED_RECENT_PATH,
    routes.GENERATED_PAYLOAD_PATH,
    routes.GENERATED_SEARCH_PATH,
    routes.GENERATED_REFERENCES_PATH,
    routes.GENERATED_REFERENCE_TARGET_PATH,
}
REVIEW_SESSION_READ_PATHS = {
    routes.REVIEW_SESSIONS_PATH,
    routes.REVIEW_SESSION_INDEX_TREE_PATH,
    routes.REVIEW_SESSION_PAYLOAD_PATH,
}


def runtime_static_relative_path(request_path: str) -> Path | None:
    for prefix, root in RUNTIME_STATIC_ROUTES:
        if not request_path.startswith(prefix):
            continue
        suffix = request_path.removeprefix(prefix)
        if not suffix:
            return None
        return root / suffix
    return None


def shared_static_relative_path(request_path: str) -> Path | None:
    return SHARED_STATIC_ROUTES.get(request_path)


@dataclass(frozen=True)
class DocsViewerServiceConfig:
    host: str
    port: int
    base_url: str
    management_enabled: bool
    generated_reads_enabled: bool
    watch_enabled: bool
    review_enabled: bool = False


def parse_site_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        try:
            parts = shlex.split(raw_value, comments=False, posix=True)
        except ValueError:
            parts = [raw_value.strip()]
        values[key] = parts[0] if parts else ""
    return values


def env_bool(values: dict[str, str], name: str, default: bool) -> bool:
    value = values.get(name)
    if value is None:
        return default
    return value.strip().lower() in ENABLED_VALUES


def service_defaults(repo_root: Path) -> dict[str, bool]:
    try:
        payload = json.loads((repo_root / DEFAULT_SERVICE_CONFIG.relative_to(REPO_ROOT)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        payload = {}
    capabilities = payload.get("capabilities") if isinstance(payload, dict) else {}
    if not isinstance(capabilities, dict):
        capabilities = {}
    return {
        "management_enabled": capabilities.get("management_enabled_default") is True,
        "generated_reads_enabled": capabilities.get("generated_reads_enabled_default") is not False,
        "watch_enabled": capabilities.get("watch_enabled_default") is not False,
        "review_enabled": capabilities.get("review_enabled_default") is True,
    }


def load_service_config(
    repo_root: Path,
    environ: dict[str, str] | None = None,
    *,
    host_override: str | None = None,
    port_override: int | None = None,
    base_url_override: str | None = None,
) -> DocsViewerServiceConfig:
    env = dict(parse_site_env(repo_root / SITE_ENV_REL_PATH))
    env.update(os.environ if environ is None else environ)
    defaults = service_defaults(repo_root)
    host = str(host_override or env.get("DOCS_VIEWER_HOST") or "127.0.0.1").strip()
    try:
        port = int(port_override or env.get("DOCS_VIEWER_PORT") or "8776")
    except (TypeError, ValueError) as error:
        raise ValueError("DOCS_VIEWER_PORT must be an integer") from error
    base_url = str(base_url_override or env.get("DOCS_VIEWER_BASE_URL") or f"http://{host}:{port}").strip().rstrip("/")
    config = DocsViewerServiceConfig(
        host=host,
        port=port,
        base_url=base_url,
        management_enabled=env_bool(env, "DOCS_VIEWER_MANAGEMENT_ENABLED", defaults["management_enabled"]),
        generated_reads_enabled=env_bool(env, "DOCS_VIEWER_GENERATED_READS_ENABLED", defaults["generated_reads_enabled"]),
        watch_enabled=env_bool(env, "DOCS_VIEWER_WATCH_ENABLED", defaults["watch_enabled"]),
        review_enabled=env_bool(env, "DOCS_VIEWER_REVIEW_ENABLED", defaults["review_enabled"]),
    )
    validate_service_config(config)
    return config


def validate_service_config(config: DocsViewerServiceConfig) -> None:
    if config.host not in LOOPBACK_HOSTS:
        raise ValueError("DOCS_VIEWER_HOST must be a loopback host for local manage mode")
    if config.port <= 0 or config.port > 65535:
        raise ValueError("DOCS_VIEWER_PORT must be between 1 and 65535")
    parsed = urlparse(config.base_url)
    if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS:
        raise ValueError("DOCS_VIEWER_BASE_URL must be an http loopback URL")
    if parsed.port != config.port:
        raise ValueError("DOCS_VIEWER_BASE_URL must use DOCS_VIEWER_PORT")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("DOCS_VIEWER_BASE_URL must not include a path, query, or fragment")


def asset_version(repo_root: Path) -> str:
    runtime_candidates = list((repo_root / "site/docs-viewer/runtime/js").rglob("*.js"))
    runtime_candidates.extend((repo_root / "docs-viewer/runtime/js").rglob("*.js"))
    candidates = [
        repo_root / "docs-viewer" / "shell" / "docs-viewer-manage.html",
        repo_root / "docs-viewer" / "shell" / "docs-viewer-review.html",
        repo_root / "site" / "docs-viewer" / "static" / "css" / "docs-viewer.css",
        repo_root / "site" / "docs-viewer" / "static" / "css" / "docs-viewer-moments.css",
        repo_root / "site" / "docs-viewer" / "static" / "css" / "docs-viewer-reports.css",
        repo_root / "docs-viewer" / "static" / "css" / "docs-viewer-manage.css",
        repo_root / "docs-viewer" / "static" / "css" / "docs-viewer-source-editor.css",
        repo_root / "docs-viewer" / "static" / "css" / "docs-viewer-import.css",
        repo_root / "docs-viewer" / "config" / "defaults" / "docs-viewer-config.json",
        repo_root / "docs-viewer" / "config" / "routes" / "docs-viewer-routes.json",
        repo_root / "site" / "docs-viewer" / "config" / "routes" / "docs-viewer-public-routes.json",
    ]
    candidates.extend(runtime_candidates)
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def render_route_config_registry(repo_root: Path, config: DocsViewerServiceConfig) -> dict[str, object]:
    payload = json.loads((repo_root / "docs-viewer" / "config" / "routes" / "docs-viewer-routes.json").read_text(encoding="utf-8"))
    routes_payload = payload.get("routes")
    routes_list = routes_payload if isinstance(routes_payload, list) else []
    for route in routes_list:
        if not isinstance(route, dict):
            continue
        route_id = route.get("route_id")
        if route_id not in {"docs-manage", "docs-review"}:
            continue
        services = route.get("services")
        if not isinstance(services, dict):
            services = {}
            route["services"] = services
        if route_id == "docs-review":
            services["generated_data"] = {"base_url": config.base_url if config.review_enabled else ""}
            services["source"] = {"base_url": ""}
            services["management"] = {"base_url": ""}
        else:
            services["generated_data"] = {
                "base_url": config.base_url if config.generated_reads_enabled else "",
            }
            services["source"] = {
                "base_url": config.base_url if config.management_enabled else "",
            }
            services["management"] = {
                "base_url": config.base_url if config.management_enabled else "",
            }
        access = route.get("access")
        if not isinstance(access, dict):
            access = {}
            route["access"] = access
        access["management_ui"] = bool(config.management_enabled) if route_id == "docs-manage" else False
    return payload


def manage_page_path(repo_root: Path) -> Path:
    return repo_root / MANAGE_PAGE_TEMPLATE.relative_to(REPO_ROOT)


def review_page_path(repo_root: Path) -> Path:
    return repo_root / REVIEW_PAGE_TEMPLATE.relative_to(REPO_ROOT)


def apply_capability_flags(payload: dict[str, object], config: DocsViewerServiceConfig) -> dict[str, object]:
    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        return payload
    capabilities["docs_management"] = bool(capabilities.get("docs_management")) and config.management_enabled
    capabilities["generated_data_reads"] = bool(capabilities.get("generated_data_reads")) and config.generated_reads_enabled
    if not config.management_enabled:
        for key in (
            "source_editor",
            "source_config_settings_writes",
            "html_import",
            "docs_export",
            "library_import",
        ):
            capabilities[key] = False
        document_packages = capabilities.get("document_packages")
        if isinstance(document_packages, dict):
            document_packages["prepare"] = False
            document_packages["context"] = False
            document_packages["inspect_returned"] = False
            document_packages["review_returned"] = False
            document_packages["apply_returned"] = False
        lifecycle = capabilities.get("scope_lifecycle")
        if isinstance(lifecycle, dict):
            for key in (
                "create_apply",
                "rename_apply",
                "delete_apply",
                "sub_scope_create_apply",
                "sub_scope_delete_apply",
            ):
                lifecycle[key] = False
        publishing = capabilities.get("publishing")
        if isinstance(publishing, dict):
            publishing["apply"] = False
            publishing["confirm"] = False
    if not config.generated_reads_enabled:
        scopes = capabilities.get("scopes")
        if isinstance(scopes, dict):
            for scope_caps in scopes.values():
                if isinstance(scope_caps, dict):
                    scope_caps["generated_data_reads"] = False
                    scope_caps["generated_search_reads"] = False
    return payload


class DocsViewerRequestHandler(QuietErrorLoggingMixin, BaseHTTPRequestHandler):
    server_version = "DocsViewerService/0.1"
    service_log_name = "docs-viewer"

    @property
    def repo_root(self) -> Path:
        return self.server.repo_root  # type: ignore[attr-defined]

    @property
    def config(self) -> DocsViewerServiceConfig:
        return self.server.docs_viewer_config  # type: ignore[attr-defined]

    @property
    def version(self) -> str:
        return self.server.asset_version  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        query = parse_qs(request.query)

        if path in {"/docs", MANAGE_ROUTE}:
            self.send_static_html(manage_page_path(self.repo_root))
            return
        if path in {"/docs-review", REVIEW_ROUTE}:
            self.send_static_html(review_page_path(self.repo_root))
            return
        if path == "/docs-viewer/config/routes/docs-viewer-routes.json":
            self.send_json(render_route_config_registry(self.repo_root, self.config))
            return
        if path == routes.HEALTH_PATH:
            self.send_json(
                {
                    "ok": True,
                    "service": "docs_viewer",
                    "management_enabled": self.config.management_enabled,
                    "generated_reads_enabled": self.config.generated_reads_enabled,
                    "review_enabled": self.config.review_enabled,
                }
            )
            return
        if path == routes.CAPABILITIES_PATH:
            self.send_capabilities_json()
            return
        if path in package_routes.GET_PATHS:
            if not self.config.management_enabled:
                self.send_json({"ok": False, "error": "Docs Viewer management is disabled"}, HTTPStatus.FORBIDDEN)
                return
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_document_package_json(path, query)
            return
        if path in GENERATED_READ_PATHS and not self.config.generated_reads_enabled:
            self.send_json({"ok": False, "error": "Generated reads are disabled"}, HTTPStatus.FORBIDDEN)
            return
        if path == routes.SOURCE_BODY_PATH:
            if not self.config.management_enabled:
                self.send_json({"ok": False, "error": "Docs Viewer management is disabled"}, HTTPStatus.FORBIDDEN)
                return
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
        if path in REVIEW_SESSION_READ_PATHS:
            if not self.config.management_enabled:
                self.send_json({"ok": False, "error": "Docs Viewer management is disabled"}, HTTPStatus.FORBIDDEN)
                return
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
        if path in review_routes.GET_PATHS:
            if not self.config.review_enabled:
                self.send_json({"ok": False, "error": "Docs Review is disabled"}, HTTPStatus.FORBIDDEN)
                return
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_review_api_json(path, query)
            return
        if path.startswith(review_routes.ASSET_CONTENT_PREFIX):
            if not self.config.review_enabled:
                self.send_json({"ok": False, "error": "Docs Review is disabled"}, HTTPStatus.FORBIDDEN)
                return
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_review_asset(path)
            return
        if path.startswith(media_storage.DOCS_MEDIA_ROUTE_PREFIX):
            self.send_docs_media(path)
            return
        if path in routes.GET_PATHS:
            self.send_docs_api_json(path, query)
            return
        if self.is_allowed_static_path(path):
            self.send_static(path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path in review_routes.POST_PATHS:
            if not self.config.review_enabled:
                self.send_json({"ok": False, "error": "Docs Review is disabled"}, HTTPStatus.FORBIDDEN)
                return
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_review_api_post_json(path)
            return
        if path not in routes.POST_PATHS and path not in package_routes.POST_PATHS:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if not self.config.management_enabled:
            self.send_json({"ok": False, "error": "Docs Viewer management is disabled"}, HTTPStatus.FORBIDDEN)
            return
        if not self.origin_allowed_for_local_api():
            self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
            return
        if path in package_routes.POST_PATHS:
            self.send_document_package_post_json(path)
        else:
            self.send_docs_api_post_json(path)

    def do_OPTIONS(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if (
            path not in routes.OPTIONS_PATHS
            and path not in review_routes.OPTIONS_PATHS
            and path not in package_routes.OPTIONS_PATHS
        ):
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if not self.origin_allowed_for_local_api():
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.end_headers()

    def is_allowed_static_path(self, path: str) -> bool:
        if path in RETIRED_STATIC_PATHS:
            return False
        return (
            path in STATIC_FILES
            or runtime_static_relative_path(path) is not None
            or bool(SCOPE_PUBLISHED_STATIC_PATTERN.match(path))
            or any(path.startswith(prefix) for prefix in STATIC_PREFIXES)
        )

    def origin_allowed_for_local_api(self) -> bool:
        origin = self.headers.get("Origin", "")
        return not origin or bool(docs_service.allowed_origin(origin))

    def send_cors_headers(self) -> None:
        origin = docs_service.allowed_origin(self.headers.get("Origin", ""))
        if not origin:
            return
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_docs_api_json(self, api_path: str, query: dict[str, list[str]]) -> None:
        try:
            payload = docs_service.docs_management_get_payload(self.repo_root, api_path, query)
            self.send_json(payload)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_document_package_json(self, api_path: str, query: dict[str, list[str]]) -> None:
        try:
            self.send_json(package_service.get_payload(self.repo_root, api_path, query))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_capabilities_json(self) -> None:
        try:
            payload = apply_capability_flags(docs_service.capabilities_payload(self.repo_root), self.config)
            self.send_json(payload)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_docs_api_post_json(self, api_path: str) -> None:
        try:
            body = self.read_json_body()
            status, payload = docs_service.docs_management_post_response(self.repo_root, api_path, body)
            self.send_json(payload, status)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_document_package_post_json(self, api_path: str) -> None:
        try:
            status, payload = package_service.post_response(
                self.repo_root,
                api_path,
                self.read_json_body(),
            )
            self.send_json(payload, status)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_review_api_json(self, api_path: str, query: dict[str, list[str]]) -> None:
        try:
            self.send_json(review_service.docs_review_get_payload(self.repo_root, api_path, query))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_review_api_post_json(self, api_path: str) -> None:
        try:
            status, payload = review_service.docs_review_post_response(
                self.repo_root,
                api_path,
                self.read_json_body(),
            )
            self.send_json(payload, status)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_review_asset(self, request_path: str) -> None:
        try:
            path = review_service.docs_review_asset_path_from_route(self.repo_root, request_path)
            body = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_cors_headers()
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if path.suffix.lower() in {".htm", ".html"}:
                self.send_header(
                    "Content-Security-Policy",
                    "sandbox allow-scripts; default-src 'self' data: blob:; connect-src 'none'",
                )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)

    def send_docs_media(self, request_path: str) -> None:
        try:
            path, media_class = media_storage.local_media_path_from_route(self.repo_root, request_path)
            body = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_cors_headers()
            self.send_header("Content-Type", media_storage.safe_content_type(path))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if media_class == "files":
                self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(path.name, safe='')}")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)

    def read_json_body(self) -> dict[str, object]:
        content_length = self.headers.get("Content-Length", "").strip()
        try:
            length = int(content_length)
        except ValueError as error:
            raise ValueError("Invalid Content-Length") from error
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("Request body too large")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Request body must be valid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object")
        return payload

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static_html(self, path: Path, status: HTTPStatus = HTTPStatus.OK) -> None:
        try:
            resolved_path = path.resolve()
            resolved_path.relative_to(self.repo_root)
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if not resolved_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        shell = resolved_path.read_text(encoding="utf-8")
        body = render_local_browser_icon_links(shell).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, request_path: str) -> None:
        shared_relative_path = shared_static_relative_path(request_path)
        runtime_relative_path = runtime_static_relative_path(request_path)
        if shared_relative_path is not None:
            relative_path = shared_relative_path
        elif runtime_relative_path is not None:
            relative_path = runtime_relative_path
        elif request_path.startswith("/assets/"):
            relative_path = Path("site") / request_path.lstrip("/")
        else:
            relative_path = Path(request_path.lstrip("/"))
        if not relative_path.parts or ".." in relative_path.parts:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        path = (self.repo_root / relative_path).resolve()
        try:
            path.relative_to(self.repo_root)
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class DocsViewerServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        repo_root: Path,
        config: DocsViewerServiceConfig,
        access_log_enabled: bool = False,
    ):
        super().__init__(server_address, DocsViewerRequestHandler)
        self.repo_root = repo_root.resolve()
        self.docs_viewer_config = config
        self.asset_version = asset_version(self.repo_root)
        self.access_log_enabled = access_log_enabled


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=None, help="Override DOCS_VIEWER_HOST for this run.")
    parser.add_argument("--port", type=int, default=None, help="Override DOCS_VIEWER_PORT for this run.")
    parser.add_argument("--base-url", default=None, help="Override DOCS_VIEWER_BASE_URL for this run.")
    parser.add_argument("--access-log", action="store_true", help="Print one access log line for each request.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_service_config(
            REPO_ROOT,
            host_override=args.host,
            port_override=args.port,
            base_url_override=args.base_url,
        )
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    try:
        media_storage.ensure_configured_scope_owned_media_directories(REPO_ROOT)
    except (OSError, ValueError) as error:
        print(f"ERROR: Could not materialize configured Docs media directories: {error}", file=sys.stderr)
        return 1

    try:
        server = DocsViewerServer((config.host, config.port), REPO_ROOT, config, access_log_enabled=args.access_log)
    except OSError as error:
        print(
            f"ERROR: Docs Viewer service cannot start on {config.host}:{config.port} because the port is unavailable.",
            file=sys.stderr,
        )
        print(f"Details: {error}", file=sys.stderr)
        return 1

    host, port = server.server_address
    print(f"Docs Viewer service: http://{host}:{port}/docs/", flush=True)
    print(f"Docs Viewer management: {'enabled' if config.management_enabled else 'disabled'}", flush=True)
    print(f"Docs Review: {'enabled' if config.review_enabled else 'disabled'}", flush=True)
    print(f"Docs Viewer generated reads: {'enabled' if config.generated_reads_enabled else 'disabled'}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
