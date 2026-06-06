#!/usr/bin/env python3
"""Serve the local Admin app shell."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
ADMIN_SERVER_DIR = Path(__file__).resolve().parent
if str(ADMIN_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_SERVER_DIR))

from admin_app_config import asset_version, runtime_config  # noqa: E402
from admin_app_views import admin_home_view  # noqa: E402


STATIC_PREFIXES = (
    "/admin/app/assets/",
    "/admin/app/frontend/config/",
    "/admin/app/frontend/js/",
)
STATIC_FILES = {
    "/favicon.ico",
    "/favicon-16x16.png",
    "/favicon-32x32.png",
    "/apple-touch-icon.png",
    "/safari-pinned-tab.svg",
    "/site.webmanifest",
}
ENABLED_VALUES = {"1", "on", "true", "yes"}


def env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ENABLED_VALUES


class AdminAppRequestHandler(BaseHTTPRequestHandler):
    server_version = "AdminAppServer/0.1"

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

        if path == "/health":
            self.send_json({"status": "ok", "app": "admin"})
            return
        if path == "/admin/runtime-config.json":
            self.send_json(runtime_config(self.repo_root, self.version))
            return
        if path in {"/admin", "/admin/"}:
            self.send_html(admin_home_view(self.version, self.repo_root))
            return
        if self.is_allowed_static_path(path):
            self.send_static(path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def is_allowed_static_path(self, path: str) -> bool:
        return path in STATIC_FILES or any(path.startswith(prefix) for prefix in STATIC_PREFIXES)

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(status)
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
        if request_path.startswith("/admin/app/"):
            relative = f"admin-app/app/{request_path.removeprefix('/admin/app/')}"
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


class AdminAppServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], repo_root: Path, access_log_enabled: bool = False):
        super().__init__(server_address, AdminAppRequestHandler)
        self.repo_root = repo_root.resolve()
        self.asset_version = asset_version(self.repo_root)
        self.access_log_enabled = access_log_enabled


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8768)
    parser.add_argument(
        "--access-log",
        action="store_true",
        default=env_flag("ADMIN_APP_ACCESS_LOG"),
        help="Print one access log line for each Admin app HTTP request.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    server = AdminAppServer((args.host, args.port), REPO_ROOT, access_log_enabled=args.access_log)
    host, port = server.server_address
    print(f"Admin app server: http://{host}:{port}/admin/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
