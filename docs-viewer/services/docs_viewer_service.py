#!/usr/bin/env python3
"""Serve the standalone local Docs Viewer shell and management API."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
import json
import mimetypes
import os
import shlex
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse, urlsplit

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

import docs_management_routes as routes  # noqa: E402
import docs_management_service as docs_service  # noqa: E402


ENABLED_VALUES = {"1", "on", "true", "yes"}
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
DEFAULT_SERVICE_CONFIG = REPO_ROOT / "docs-viewer" / "config" / "defaults" / "docs-viewer-service.json"
SHELL_TEMPLATE = REPO_ROOT / "docs-viewer" / "shell" / "docs-viewer-shell.html"
MANAGE_ROUTE = "/docs/"
STATIC_PREFIXES = (
    "/assets/data/",
    "/assets/docs/",
    "/docs-viewer/config/",
    "/docs-viewer/generated/",
    "/docs-viewer/runtime/",
    "/docs-viewer/static/",
)
STATIC_FILES = {
    "/apple-touch-icon.png",
    "/favicon.ico",
    "/favicon-16x16.png",
    "/favicon-32x32.png",
    "/safari-pinned-tab.svg",
    "/site.webmanifest",
}
MAX_BODY_BYTES = 1024 * 1024
GENERATED_READ_PATHS = {
    routes.GENERATED_INDEX_PATH,
    routes.GENERATED_INDEX_ALT_PATH,
    routes.GENERATED_PAYLOAD_PATH,
    routes.GENERATED_PAYLOAD_ALT_PATH,
    routes.GENERATED_SEARCH_PATH,
    routes.GENERATED_SEARCH_ALT_PATH,
    routes.GENERATED_DOCS_LOG_PATH,
    routes.GENERATED_REFERENCES_PATH,
    routes.GENERATED_REFERENCES_ALT_PATH,
    routes.GENERATED_REFERENCE_TARGET_PATH,
    routes.GENERATED_REFERENCE_TARGET_ALT_PATH,
}


@dataclass(frozen=True)
class DocsViewerServiceConfig:
    host: str
    port: int
    base_url: str
    management_enabled: bool
    generated_reads_enabled: bool
    watch_enabled: bool


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
    }


def load_service_config(
    repo_root: Path,
    environ: dict[str, str] | None = None,
    *,
    host_override: str | None = None,
    port_override: int | None = None,
    base_url_override: str | None = None,
) -> DocsViewerServiceConfig:
    env = dict(parse_site_env(repo_root / "var" / "local" / "site.env"))
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
    candidates = [
        repo_root / "docs-viewer" / "shell" / "docs-viewer-shell.html",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer.js",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer-access.js",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer-app-context.js",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer-app-shell.js",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer-hosted-views.js",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer-header-controls-renderer.js",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer-management-actions-renderer.js",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer-route-config.js",
        repo_root / "docs-viewer" / "runtime" / "js" / "docs-viewer-view-state.js",
        repo_root / "docs-viewer" / "static" / "css" / "docs-viewer-base.css",
        repo_root / "docs-viewer" / "static" / "css" / "docs-viewer.css",
        repo_root / "docs-viewer" / "static" / "css" / "docs-viewer-reports.css",
        repo_root / "docs-viewer" / "static" / "css" / "docs-viewer-management.css",
        repo_root / "docs-viewer" / "config" / "defaults" / "docs-viewer-config.json",
        repo_root / "docs-viewer" / "config" / "routes" / "docs-viewer-routes.json",
        repo_root / "docs-viewer" / "config" / "ui-text" / "ui-text.json",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def render_docs_viewer_shell(repo_root: Path, config: DocsViewerServiceConfig, version: str) -> str:
    text = (repo_root / SHELL_TEMPLATE.relative_to(REPO_ROOT)).read_text(encoding="utf-8")
    lines: list[str] = []
    active_stack = [True]
    allow_management = config.management_enabled
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("{%- assign "):
            continue
        if stripped == "{%- if include.allow_management -%}":
            active_stack.append(active_stack[-1] and allow_management)
            continue
        if stripped == "{%- if include.allow_scope_query -%}":
            active_stack.append(active_stack[-1])
            continue
        if stripped in {"{%- endif -%}", "{%- endunless -%}"}:
            if len(active_stack) > 1:
                active_stack.pop()
            continue
        if active_stack[-1]:
            lines.append(raw_line)

    shell = "\n".join(lines)
    escaped_version = html.escape(version, quote=True)
    management_base_url = html.escape(config.base_url if config.management_enabled else "", quote=True)
    generated_base_url = html.escape(config.base_url if config.generated_reads_enabled else "", quote=True)
    replacements = {
        "{{ '/docs-viewer/static/css/docs-viewer-base.css' | relative_url }}": "/docs-viewer/static/css/docs-viewer-base.css",
        "{{ '/docs-viewer/static/css/docs-viewer.css' | relative_url }}": "/docs-viewer/static/css/docs-viewer.css",
        "{{ '/docs-viewer/static/css/docs-viewer-reports.css' | relative_url }}": "/docs-viewer/static/css/docs-viewer-reports.css",
        "{{ '/docs-viewer/static/css/docs-viewer-management.css' | relative_url }}": "/docs-viewer/static/css/docs-viewer-management.css",
        "{{ '/docs-viewer/runtime/js/docs-viewer.js' | relative_url }}": "/docs-viewer/runtime/js/docs-viewer.js",
        "{{ site.time | date: '%s' }}": escaped_version,
        "{{ include.route_id | default: '' }}": "docs-manage",
        "{{ include.route_id | default: '' | jsonify }}": '"docs-manage"',
        "{{ docs_viewer_route_config_url | relative_url }}": "/docs-viewer/config/routes/docs-viewer-routes.json",
        "{{ include.index_url }}": "",
        "{{ include.index_url | default: '' | jsonify }}": '""',
        "{{ include.viewer_base_url }}": MANAGE_ROUTE,
        "{{ include.viewer_base_url | jsonify }}": f'"{MANAGE_ROUTE}"',
        "{{ include.viewer_scope | default: '' }}": "",
        "{{ include.viewer_scope | default: '' | jsonify }}": '""',
        "{{ include.include_scope_param | default: false }}": "true",
        "{{ include.include_scope_param | default: false | jsonify }}": "true",
        "{{ include.allow_management | default: false }}": "true" if config.management_enabled else "false",
        "{{ include.allow_management | default: false | jsonify }}": "true" if config.management_enabled else "false",
        "{{ include.allow_scope_query | default: false }}": "true",
        "{{ include.allow_scope_query | default: false | jsonify }}": "true",
        "{{ include.default_doc_id | default: '' }}": "",
        "{{ include.default_doc_id | default: '' | jsonify }}": '""',
        "{{ include.search_index_url | default: '' }}": "",
        "{{ include.search_index_url | default: '' | jsonify }}": '""',
        "{{ docs_viewer_config_url | relative_url }}": "/docs-viewer/config/defaults/docs-viewer-config.json",
        "{{ docs_viewer_config_url | relative_url | jsonify }}": '"/docs-viewer/config/defaults/docs-viewer-config.json"',
        "{{ include.ui_text_url | default: '/docs-viewer/config/ui-text/ui-text.json' | relative_url }}": "/docs-viewer/config/ui-text/ui-text.json",
        "{{ include.ui_text_url | default: '/docs-viewer/config/ui-text/ui-text.json' | relative_url | jsonify }}": '"/docs-viewer/config/ui-text/ui-text.json"',
        "{{ include.report_registry_url | default: '/assets/data/docs/reports.json' | relative_url }}": "/assets/data/docs/reports.json",
        "{{ include.report_registry_url | default: '/assets/data/docs/reports.json' | relative_url | jsonify }}": '"/assets/data/docs/reports.json"',
        "{{ docs_viewer_generated_base_url }}": generated_base_url,
        "{{ docs_viewer_generated_base_url | jsonify }}": f'"{generated_base_url}"',
        "{{ include.management_base_url | default: '' }}": management_base_url,
        "{{ include.management_base_url | default: '' | jsonify }}": f'"{management_base_url}"',
        "{%- if include.enable_search == false -%}false{%- else -%}true{%- endif -%}": "true",
        "{{ include.search_aria_label | default: 'Search docs' }}": "Search docs",
        "{{ include.search_placeholder | default: 'search docs' }}": "search docs",
    }
    for token, value in replacements.items():
        shell = shell.replace(token, value)
    return shell


def render_route_config_registry(repo_root: Path, config: DocsViewerServiceConfig) -> dict[str, object]:
    payload = json.loads((repo_root / "docs-viewer" / "config" / "routes" / "docs-viewer-routes.json").read_text(encoding="utf-8"))
    routes_payload = payload.get("routes")
    routes_list = routes_payload if isinstance(routes_payload, list) else []
    for route in routes_list:
        if not isinstance(route, dict) or route.get("route_id") != "docs-manage":
            continue
        route["generated_base_url"] = config.base_url if config.generated_reads_enabled else ""
        access = route.get("access")
        if not isinstance(access, dict):
            access = {}
            route["access"] = access
        access["allow_management"] = bool(config.management_enabled)
        access["management_base_url"] = config.base_url if config.management_enabled else ""
    return payload


def render_manage_page(repo_root: Path, config: DocsViewerServiceConfig, version: str) -> str:
    escaped_version = html.escape(version, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <title>Docs Viewer</title>
  <script>
    (function () {{
      try {{
        var theme = localStorage.getItem("theme");
        document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
      }} catch (error) {{
        document.documentElement.setAttribute("data-theme", "light");
      }}
    }})();
  </script>
</head>
<body class="docs-viewer-service">
  <main class="docs-viewer-service__main">
    {render_docs_viewer_shell(repo_root, config, version)}
  </main>
</body>
</html>
"""


def apply_capability_flags(payload: dict[str, object], config: DocsViewerServiceConfig) -> dict[str, object]:
    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        return payload
    capabilities["docs_management"] = bool(capabilities.get("docs_management")) and config.management_enabled
    capabilities["generated_data_reads"] = bool(capabilities.get("generated_data_reads")) and config.generated_reads_enabled
    if not config.management_enabled:
        for key in (
            "source_config_settings_writes",
            "html_import",
            "docs_export",
            "library_import",
        ):
            capabilities[key] = False
        lifecycle = capabilities.get("scope_lifecycle")
        if isinstance(lifecycle, dict):
            lifecycle["create_apply"] = False
            lifecycle["delete_apply"] = False
    if not config.generated_reads_enabled:
        scopes = capabilities.get("scopes")
        if isinstance(scopes, dict):
            for scope_caps in scopes.values():
                if isinstance(scope_caps, dict):
                    scope_caps["generated_data_reads"] = False
                    scope_caps["generated_search_reads"] = False
    return payload


class DocsViewerRequestHandler(BaseHTTPRequestHandler):
    server_version = "DocsViewerService/0.1"

    @property
    def repo_root(self) -> Path:
        return self.server.repo_root  # type: ignore[attr-defined]

    @property
    def config(self) -> DocsViewerServiceConfig:
        return self.server.docs_viewer_config  # type: ignore[attr-defined]

    @property
    def version(self) -> str:
        return self.server.asset_version  # type: ignore[attr-defined]

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        if self.server.access_log_enabled:  # type: ignore[attr-defined]
            super().log_request(code, size)

    def do_GET(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        query = parse_qs(request.query)

        if path in {"/docs", MANAGE_ROUTE}:
            self.send_html(render_manage_page(self.repo_root, self.config, self.version))
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
                }
            )
            return
        if path == routes.CAPABILITIES_PATH:
            self.send_json(apply_capability_flags(docs_service.capabilities_payload(self.repo_root), self.config))
            return
        if path in GENERATED_READ_PATHS and not self.config.generated_reads_enabled:
            self.send_json({"ok": False, "error": "Generated reads are disabled"}, HTTPStatus.FORBIDDEN)
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
        if path not in routes.POST_PATHS:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if not self.config.management_enabled:
            self.send_json({"ok": False, "error": "Docs Viewer management is disabled"}, HTTPStatus.FORBIDDEN)
            return
        if not self.origin_allowed_for_local_api():
            self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
            return
        self.send_docs_api_post_json(path)

    def do_OPTIONS(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path not in routes.OPTIONS_PATHS:
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
        return path in STATIC_FILES or any(path.startswith(prefix) for prefix in STATIC_PREFIXES)

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

    def send_html(self, html_text: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, request_path: str) -> None:
        relative = request_path.lstrip("/")
        if not relative or ".." in Path(relative).parts:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        path = (self.repo_root / relative).resolve()
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
