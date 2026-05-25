#!/usr/bin/env python3
"""Serve the local vanilla Studio app shell."""

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
STUDIO_DIR = Path(__file__).resolve().parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

from studio_app_config import asset_version, runtime_config  # noqa: E402
from studio_catalogue_views import (  # noqa: E402
    catalogue_dashboard_view,
    catalogue_field_registry_view,
    catalogue_moment_view,
    catalogue_series_view,
    catalogue_status_view,
    catalogue_work_detail_view,
    catalogue_work_view,
    studio_works_view,
)
from studio_ui_catalogue_views import UI_CATALOGUE_DEMO_ROUTES, ui_catalogue_demo_view  # noqa: E402
from studio_app_views import (  # noqa: E402
    activity_view,
    bulk_add_work_view,
    data_sharing_dashboard_view,
    data_sharing_prepare_view,
    data_sharing_review_view,
    project_state_view,
    series_tags_view,
    series_tag_editor_view,
    studio_analytics_view,
    studio_audits_view,
    studio_home_view,
    tag_aliases_view,
    tag_groups_view,
    tag_registry_view,
    thumbnail_quality_view,
)
from studio_analytics_api import analytics_get_payload, analytics_post_response  # noqa: E402
from studio_audit_api import audit_get_payload, audit_post_response  # noqa: E402
from studio_catalogue_api import catalogue_get_payload, catalogue_post_response  # noqa: E402


STATIC_PREFIXES = (
    "/assets/css/",
    "/assets/data/",
    "/assets/docs/",
    "/assets/home/",
    "/assets/js/",
    "/assets/moments/",
    "/assets/series/",
    "/assets/site/",
    "/assets/work_details/",
    "/assets/works/",
    "/studio/data/generated/thumbnail-quality/img/",
    "/studio/app/frontend/js/",
    "/studio/app/frontend/config/",
    "/studio/app/assets/",
    "/studio/ui-catalogue/assets/",
    "/studio/data/",
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


class StudioAppRequestHandler(BaseHTTPRequestHandler):
    server_version = "StudioAppServer/0.1"

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
            self.send_json({"status": "ok", "app": "studio"})
            return
        if path == "/studio/runtime-config.json":
            self.send_json(runtime_config(self.repo_root, self.version))
            return
        if path.startswith("/studio/api/analytics/"):
            self.send_analytics_api_json(path.removeprefix("/studio/api/analytics"))
            return
        if path.startswith("/studio/api/audits/"):
            self.send_audit_api_json(path.removeprefix("/studio/api/audits"))
            return
        if path.startswith("/studio/api/catalogue/"):
            self.send_catalogue_api_json(path.removeprefix("/studio/api/catalogue"), query)
            return
        if path in {"/studio", "/studio/"}:
            self.send_html(studio_home_view(self.version))
            return
        if path in {"/studio/analytics/tag-groups", "/studio/analytics/tag-groups/"}:
            self.send_html(tag_groups_view(self.version))
            return
        if path in {"/studio/analytics/tag-registry", "/studio/analytics/tag-registry/"}:
            self.send_html(tag_registry_view(self.version))
            return
        if path in {"/studio/analytics/tag-aliases", "/studio/analytics/tag-aliases/"}:
            self.send_html(tag_aliases_view(self.version))
            return
        if path in {"/studio/analytics/series-tags", "/studio/analytics/series-tags/"}:
            self.send_html(series_tags_view(self.version))
            return
        if path in {"/studio/analytics/series-tag-editor", "/studio/analytics/series-tag-editor/"}:
            self.send_html(series_tag_editor_view(self.version, self.repo_root))
            return
        if path in {"/studio/catalogue", "/studio/catalogue/"}:
            self.send_html(catalogue_dashboard_view(self.version))
            return
        if path in {"/studio/analytics", "/studio/analytics/"}:
            self.send_html(studio_analytics_view(self.version))
            return
        if path in {"/studio/audits", "/studio/audits/"}:
            self.send_html(studio_audits_view(self.version))
            return
        if path in {"/studio/project-state", "/studio/project-state/"}:
            self.send_html(project_state_view(self.version))
            return
        if path in {"/studio/thumbnail-quality", "/studio/thumbnail-quality/"}:
            self.send_html(thumbnail_quality_view(self.version))
            return
        if path in {"/studio/bulk-add-work", "/studio/bulk-add-work/"}:
            self.send_html(bulk_add_work_view(self.version, self.repo_root))
            return
        if path in {"/studio/activity", "/studio/activity/"}:
            self.send_html(activity_view(self.version))
            return
        if path in {"/studio/data-sharing", "/studio/data-sharing/"}:
            self.send_html(data_sharing_dashboard_view(self.version))
            return
        if path in {"/studio/data-sharing/prepare", "/studio/data-sharing/prepare/"}:
            self.send_html(data_sharing_prepare_view(self.version))
            return
        if path in {"/studio/data-sharing/review", "/studio/data-sharing/review/"}:
            self.send_html(data_sharing_review_view(self.version))
            return
        if path in {"/studio/catalogue-field-registry", "/studio/catalogue-field-registry/"}:
            self.send_html(catalogue_field_registry_view(self.version))
            return
        if path in {"/studio/catalogue-status", "/studio/catalogue-status/"}:
            self.send_html(catalogue_status_view(self.version))
            return
        if path in {"/studio/studio-works", "/studio/studio-works/"}:
            self.send_html(studio_works_view(self.version))
            return
        if path in {"/studio/catalogue-series", "/studio/catalogue-series/"}:
            self.send_html(catalogue_series_view(self.version))
            return
        if path in {"/studio/catalogue-work", "/studio/catalogue-work/"}:
            self.send_html(catalogue_work_view(self.version, self.repo_root))
            return
        if path in {"/studio/catalogue-work-detail", "/studio/catalogue-work-detail/"}:
            self.send_html(catalogue_work_detail_view(self.version, self.repo_root))
            return
        if path in {"/studio/catalogue-moment", "/studio/catalogue-moment/"}:
            self.send_html(catalogue_moment_view(self.version))
            return
        for route_path, view_id in UI_CATALOGUE_DEMO_ROUTES.items():
            if path in {route_path.rstrip("/"), route_path}:
                self.send_html(ui_catalogue_demo_view(self.version, self.repo_root, view_id))
                return
        if self.is_allowed_static_path(path):
            self.send_static(path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if path.startswith("/studio/api/analytics/"):
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_analytics_api_post_json(path.removeprefix("/studio/api/analytics"))
            return
        if path.startswith("/studio/api/audits/"):
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_audit_api_post_json(path.removeprefix("/studio/api/audits"))
            return
        if path.startswith("/studio/api/catalogue/"):
            if not self.origin_allowed_for_local_api():
                self.send_json({"ok": False, "error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                return
            self.send_catalogue_api_post_json(path.removeprefix("/studio/api/catalogue"))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_OPTIONS(self) -> None:
        request = urlsplit(self.path)
        path = unquote(request.path)
        if not path.startswith(("/studio/api/analytics/", "/studio/api/audits/", "/studio/api/catalogue/")):
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

    def send_audit_api_json(self, api_path: str) -> None:
        try:
            self.send_json(audit_get_payload(self.repo_root, api_path))
        except FileNotFoundError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.NOT_FOUND)
        except RuntimeError as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_catalogue_api_json(self, api_path: str, query: dict[str, list[str]]) -> None:
        try:
            self.send_json(catalogue_get_payload(self.repo_root, api_path, query))
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

    def send_catalogue_api_post_json(self, api_path: str) -> None:
        try:
            body = self.read_json_body()
            status, payload = catalogue_post_response(self.repo_root, api_path, body)
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
    def __init__(self, server_address: tuple[str, int], repo_root: Path, access_log_enabled: bool = False):
        super().__init__(server_address, StudioAppRequestHandler)
        self.repo_root = repo_root.resolve()
        self.asset_version = asset_version(self.repo_root)
        self.access_log_enabled = access_log_enabled


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--access-log",
        action="store_true",
        default=env_flag("STUDIO_APP_ACCESS_LOG"),
        help="Print one access log line for each Studio app HTTP request.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    server = StudioAppServer((args.host, args.port), REPO_ROOT, access_log_enabled=args.access_log)
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
