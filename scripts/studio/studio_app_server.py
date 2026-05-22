#!/usr/bin/env python3
"""Serve the local vanilla Studio app shell."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[2]
STUDIO_DIR = Path(__file__).resolve().parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

from studio_app_config import asset_version, runtime_config  # noqa: E402
from studio_app_views import docs_viewer_manage_view, studio_home_view, tag_groups_view  # noqa: E402
from studio_docs_api import docs_allowed_origin, docs_management_get_payload, docs_management_post_response  # noqa: E402


STATIC_PREFIXES = ("/assets/",)
STATIC_FILES = {
    "/favicon.ico",
    "/favicon-16x16.png",
    "/favicon-32x32.png",
    "/apple-touch-icon.png",
    "/safari-pinned-tab.svg",
    "/site.webmanifest",
}
MAX_BODY_BYTES = 64 * 1024


class StudioAppRequestHandler(BaseHTTPRequestHandler):
    server_version = "StudioAppServer/0.1"

    @property
    def repo_root(self) -> Path:
        return self.server.repo_root  # type: ignore[attr-defined]

    @property
    def version(self) -> str:
        return self.server.asset_version  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        query = parse_qs(request.query)

        if path == "/health":
            self.send_json({"status": "ok", "app": "studio"})
            return
        if path == "/studio/runtime-config.json":
            self.send_json(runtime_config(self.repo_root, self.version))
            return
        if path.startswith("/studio/api/docs/"):
            self.send_docs_api_json(path.removeprefix("/studio/api/docs"), query)
            return
        if path in {"/studio", "/studio/"}:
            self.send_html(studio_home_view(self.version))
            return
        if path in {"/docs", "/docs/"}:
            self.send_html(docs_viewer_manage_view(self.version, self.repo_root))
            return
        if path in {"/studio/analytics/tag-groups", "/studio/analytics/tag-groups/"}:
            self.send_html(tag_groups_view(self.version))
            return
        if self.is_allowed_static_path(path):
            self.send_static(path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path.startswith("/studio/api/docs/"):
            if not self.origin_allowed_for_docs_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_docs_api_post_json(path.removeprefix("/studio/api/docs"))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_OPTIONS(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if not path.startswith("/studio/api/docs/"):
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if not self.origin_allowed_for_docs_api():
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.end_headers()

    def is_allowed_static_path(self, path: str) -> bool:
        return path in STATIC_FILES or any(path.startswith(prefix) for prefix in STATIC_PREFIXES)

    def allowed_origin(self) -> str:
        return docs_allowed_origin(self.repo_root, self.headers.get("Origin", ""))

    def origin_allowed_for_docs_api(self) -> bool:
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

    def send_docs_api_json(self, api_path: str, query: dict[str, list[str]]) -> None:
        try:
            self.send_json(docs_management_get_payload(self.repo_root, api_path, query))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_docs_api_post_json(self, api_path: str) -> None:
        try:
            body = self.read_json_body()
            status, payload = docs_management_post_response(self.repo_root, api_path, body)
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


class StudioAppServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], repo_root: Path):
        super().__init__(server_address, StudioAppRequestHandler)
        self.repo_root = repo_root.resolve()
        self.asset_version = asset_version(self.repo_root)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    server = StudioAppServer((args.host, args.port), REPO_ROOT)
    host, port = server.server_address
    print(f"Studio app server: http://{host}:{port}/studio/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
