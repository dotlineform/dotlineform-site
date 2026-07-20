#!/usr/bin/env python3
"""Serve the local vanilla Analytics app shell."""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse, urlsplit

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
ANALYTICS_SERVER_DIR = Path(__file__).resolve().parent
if str(ANALYTICS_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYTICS_SERVER_DIR))

from analytics_api import analytics_get_payload, analytics_post_response  # noqa: E402
from analytics_app_config import (  # noqa: E402
    analytics_shell_route_paths,
    analytics_views,
    asset_version,
    normalize_route_path,
    runtime_config,
)


STATIC_PREFIXES = (
    "/assets/data/",
    "/assets/series/",
    "/assets/work_details/",
    "/assets/works/",
    "/analytics/data/",
    "/analytics/app/assets/",
    "/analytics/app/frontend/js/",
    "/analytics/app/frontend/config/",
    "/analytics/app/frontend/routes/",
    "/shared/frontend/",
)
STATIC_FILES = set(LOCAL_BROWSER_ASSET_PATHS)
MAX_BODY_BYTES = 1024 * 1024
ENABLED_VALUES = {"1", "on", "true", "yes"}


def env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ENABLED_VALUES


class AnalyticsAppRequestHandler(QuietErrorLoggingMixin, BaseHTTPRequestHandler):
    server_version = "AnalyticsAppServer/0.1"
    service_log_name = "analytics"

    @property
    def repo_root(self) -> Path:
        return self.server.repo_root  # type: ignore[attr-defined]

    @property
    def version(self) -> str:
        return self.server.asset_version  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path == "/health":
            self.send_json({"status": "ok", "app": "analytics"})
            return
        if path == "/analytics/runtime-config.json":
            self.send_json(runtime_config(self.repo_root, self.version))
            return
        if path.startswith("/analytics/api/"):
            self.send_analytics_api_json(path.removeprefix("/analytics/api"))
            return
        if normalize_route_path(path) in analytics_shell_route_paths(self.repo_root):
            self.send_html(self.analytics_shell_html(path))
            return
        if self.is_allowed_static_path(path):
            self.send_static(path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path.startswith("/analytics/api/"):
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_analytics_api_post_json(path.removeprefix("/analytics/api"))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_OPTIONS(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if not path.startswith("/analytics/api/"):
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

    def allowed_origin(self) -> str:
        origin = self.headers.get("Origin", "")
        if not origin:
            return ""
        try:
            parsed = urlparse(origin)
        except Exception:
            return ""
        if parsed.scheme != "http":
            return ""
        if parsed.hostname not in {"localhost", "127.0.0.1"}:
            return ""
        if parsed.path not in {"", "/"}:
            return ""
        if parsed.params or parsed.query or parsed.fragment:
            return ""
        if parsed.port is None:
            return f"{parsed.scheme}://{parsed.hostname}"
        return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"

    def origin_allowed_for_local_api(self) -> bool:
        origin = self.headers.get("Origin", "")
        return not origin or bool(self.allowed_origin())

    def send_cors_headers(self) -> None:
        origin = self.allowed_origin()
        if not origin:
            return
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_analytics_api_json(self, api_path: str) -> None:
        try:
            self.send_json(analytics_get_payload(self.repo_root, api_path))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_analytics_api_post_json(self, api_path: str) -> None:
        try:
            body = self.read_json_body()
            status, payload = analytics_post_response(self.repo_root, api_path, body)
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

    def send_html(self, html_text: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def analytics_shell_html(self, request_path: str) -> str:
        route_paths = analytics_shell_route_paths(self.repo_root)
        route_id = route_paths.get(normalize_route_path(request_path), "analytics_home")
        route = analytics_views(self.repo_root).get(route_id, {})
        title = str(route.get("title") or "Analytics")
        shell_path = self.repo_root / "analytics-app" / "app" / "frontend" / "analytics-shell.html"
        try:
            shell = shell_path.read_text(encoding="utf-8")
        except OSError as error:
            raise RuntimeError(f"Could not read Analytics shell: {shell_path}") from error
        replacements = {
            "__ANALYTICS_ASSET_VERSION__": html.escape(self.version, quote=True),
            "__ANALYTICS_PAGE_TITLE__": html.escape(title, quote=False),
        }
        for token, value in replacements.items():
            shell = shell.replace(token, value)
        return render_local_browser_icon_links(shell)

    def send_static(self, request_path: str) -> None:
        if request_path.startswith("/analytics/app/"):
            relative_path = Path("analytics-app/app") / request_path.removeprefix("/analytics/app/")
        elif request_path.startswith("/analytics/data/"):
            relative_path = Path("analytics-app/data") / request_path.removeprefix("/analytics/data/")
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


class AnalyticsAppServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], repo_root: Path, access_log_enabled: bool = False):
        super().__init__(server_address, AnalyticsAppRequestHandler)
        self.repo_root = repo_root.resolve()
        self.asset_version = asset_version(self.repo_root)
        self.access_log_enabled = access_log_enabled


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument(
        "--access-log",
        action="store_true",
        default=env_flag("ANALYTICS_APP_ACCESS_LOG"),
        help="Print one access log line for each Analytics app HTTP request.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    server = AnalyticsAppServer((args.host, args.port), REPO_ROOT, access_log_enabled=args.access_log)
    host, port = server.server_address
    print(f"Analytics app server: http://{host}:{port}/analytics/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
