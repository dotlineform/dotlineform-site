#!/usr/bin/env python3
"""Serve the local vanilla Analytics app shell."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
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
ANALYTICS_SERVER_DIR = Path(__file__).resolve().parent
if str(ANALYTICS_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYTICS_SERVER_DIR))

from analytics_api import analytics_get_payload, analytics_post_response  # noqa: E402
from analytics_app_config import asset_version, runtime_config  # noqa: E402
from analytics_app_views import (  # noqa: E402
    analytics_home_view,
    data_sharing_prepare_view,
    data_sharing_review_view,
    series_tag_editor_view,
    series_tags_view,
    tag_aliases_view,
    tag_groups_view,
    tag_registry_view,
)
from analytics_data_sharing_api import data_sharing_get_payload, data_sharing_post_response  # noqa: E402


STATIC_PREFIXES = (
    "/assets/data/",
    "/assets/series/",
    "/assets/work_details/",
    "/assets/works/",
    "/analytics/data/",
    "/analytics/app/assets/",
    "/analytics/app/frontend/js/",
    "/analytics/app/frontend/config/",
)
STATIC_FILES = {
    "/favicon.ico",
    "/favicon-16x16.png",
    "/favicon-32x32.png",
    "/apple-touch-icon.png",
    "/safari-pinned-tab.svg",
    "/site.webmanifest",
}
MAX_BODY_BYTES = 1024 * 1024
ENABLED_VALUES = {"1", "on", "true", "yes"}


def env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ENABLED_VALUES


class AnalyticsAppRequestHandler(BaseHTTPRequestHandler):
    server_version = "AnalyticsAppServer/0.1"

    @property
    def repo_root(self) -> Path:
        return self.server.repo_root  # type: ignore[attr-defined]

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

        if path == "/health":
            self.send_json({"status": "ok", "app": "analytics"})
            return
        if path == "/analytics/runtime-config.json":
            self.send_json(runtime_config(self.repo_root, self.version))
            return
        if path.startswith("/analytics/api/data-sharing/"):
            self.send_data_sharing_api_json(path.removeprefix("/analytics/api/data-sharing"), query)
            return
        if path.startswith("/analytics/api/"):
            self.send_analytics_api_json(path.removeprefix("/analytics/api"))
            return
        if path in {"/analytics", "/analytics/"}:
            self.send_html(analytics_home_view(self.version))
            return
        if path in {"/analytics/tag-groups", "/analytics/tag-groups/"}:
            self.send_html(tag_groups_view(self.version))
            return
        if path in {"/analytics/tag-registry", "/analytics/tag-registry/"}:
            self.send_html(tag_registry_view(self.version))
            return
        if path in {"/analytics/tag-aliases", "/analytics/tag-aliases/"}:
            self.send_html(tag_aliases_view(self.version))
            return
        if path in {"/analytics/series-tags", "/analytics/series-tags/"}:
            self.send_html(series_tags_view(self.version))
            return
        if path in {"/analytics/series-tag-editor", "/analytics/series-tag-editor/"}:
            self.send_html(series_tag_editor_view(self.version, self.repo_root))
            return
        if path in {"/analytics/data-sharing/prepare", "/analytics/data-sharing/prepare/"}:
            self.send_html(data_sharing_prepare_view(self.version))
            return
        if path in {"/analytics/data-sharing/review", "/analytics/data-sharing/review/"}:
            self.send_html(data_sharing_review_view(self.version))
            return
        if self.is_allowed_static_path(path):
            self.send_static(path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path.startswith("/analytics/api/data-sharing/"):
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_data_sharing_api_post_json(path.removeprefix("/analytics/api/data-sharing"))
            return
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

    def send_data_sharing_api_json(self, api_path: str, query: dict[str, list[str]]) -> None:
        try:
            self.send_json(data_sharing_get_payload(self.repo_root, api_path, query))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
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

    def send_data_sharing_api_post_json(self, api_path: str) -> None:
        try:
            body = self.read_json_body()
            status, payload = data_sharing_post_response(self.repo_root, api_path, body)
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

    def send_static(self, request_path: str) -> None:
        if request_path.startswith("/analytics/app/"):
            relative = f"analytics-app/app/{request_path.removeprefix('/analytics/app/')}"
        elif request_path.startswith("/analytics/data/"):
            relative = f"analytics-app/data/{request_path.removeprefix('/analytics/data/')}"
        else:
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
