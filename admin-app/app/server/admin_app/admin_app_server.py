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
from urllib.parse import parse_qs, unquote, urlparse, urlsplit

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
ADMIN_SERVER_DIR = Path(__file__).resolve().parent
if str(ADMIN_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_SERVER_DIR))

from admin_app_config import asset_version, runtime_config  # noqa: E402
from admin_activity_api import activity_get_payload  # noqa: E402
from admin_app_views import admin_activity_view, admin_audits_view, admin_checks_view, admin_home_view, admin_testing_view  # noqa: E402
from admin_audit_api import audit_get_payload, audit_post_response  # noqa: E402
from admin_checks_api import ChecksConfigError, checks_delete_response, checks_get_payload, checks_post_response  # noqa: E402
from admin_testing_api import testing_get_payload  # noqa: E402


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
MAX_BODY_BYTES = 1024 * 1024


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
        query = parse_qs(request.query)

        if path == "/health":
            self.send_json({"status": "ok", "app": "admin"})
            return
        if path == "/admin/runtime-config.json":
            self.send_json(runtime_config(self.repo_root, self.version))
            return
        if path.startswith("/admin/api/activity/"):
            self.send_activity_api_json(path.removeprefix("/admin/api/activity"))
            return
        if path.startswith("/admin/api/audits/"):
            self.send_audit_api_json(path.removeprefix("/admin/api/audits"))
            return
        if path.startswith("/admin/api/checks/"):
            self.send_checks_api_json(path.removeprefix("/admin/api/checks"), query)
            return
        if path.startswith("/admin/api/testing/"):
            self.send_testing_api_json(path.removeprefix("/admin/api/testing"), query)
            return
        if path in {"/admin", "/admin/"}:
            self.send_html(admin_home_view(self.version, self.repo_root))
            return
        if path in {"/admin/audits", "/admin/audits/"}:
            self.send_html(admin_audits_view(self.version))
            return
        if path in {"/admin/checks", "/admin/checks/"}:
            self.send_html(admin_checks_view(self.version))
            return
        if path in {"/admin/activity", "/admin/activity/"}:
            self.send_html(admin_activity_view(self.version))
            return
        if path in {"/admin/testing", "/admin/testing/"}:
            self.send_html(admin_testing_view(self.version))
            return
        if self.is_allowed_static_path(path):
            self.send_static(path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path.startswith("/admin/api/audits/"):
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_audit_api_post_json(path.removeprefix("/admin/api/audits"))
            return
        if path.startswith("/admin/api/checks/"):
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_checks_api_post_json(path.removeprefix("/admin/api/checks"))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_DELETE(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path.startswith("/admin/api/checks/"):
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_checks_api_delete_json(path.removeprefix("/admin/api/checks"))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_OPTIONS(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if not path.startswith(("/admin/api/audits/", "/admin/api/checks/")):
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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
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

    def send_activity_api_json(self, api_path: str) -> None:
        try:
            self.send_json(activity_get_payload(self.repo_root, api_path))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_audit_api_json(self, api_path: str) -> None:
        try:
            self.send_json(audit_get_payload(self.repo_root, api_path))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_checks_api_json(self, api_path: str, query: dict[str, list[str]]) -> None:
        try:
            self.send_json(checks_get_payload(self.repo_root, api_path, query))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except (ChecksConfigError, ValueError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_testing_api_json(self, api_path: str, query: dict[str, list[str]]) -> None:
        try:
            self.send_json(testing_get_payload(self.repo_root, api_path, query))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_audit_api_post_json(self, api_path: str) -> None:
        try:
            body = self.read_json_body()
            status, payload = audit_post_response(self.repo_root, api_path, body)
            self.send_json(payload, status)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_checks_api_post_json(self, api_path: str) -> None:
        try:
            body = self.read_json_body()
            status, payload = checks_post_response(self.repo_root, api_path, body)
            self.send_json(payload, status)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except (ChecksConfigError, ValueError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_checks_api_delete_json(self, api_path: str) -> None:
        try:
            status, payload = checks_delete_response(self.repo_root, api_path)
            self.send_json(payload, status)
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except (ChecksConfigError, ValueError) as error:
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

    def send_redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

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
