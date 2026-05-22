#!/usr/bin/env python3
"""
Optional localhost HTTP wrapper for shared Docs management services.

Normal Local Studio sessions serve Docs management through
`scripts/studio/studio_app_server.py` at `/studio/api/docs/...`.
Run this wrapper only for explicit standalone/debug use:

  ./scripts/docs/docs_management_server.py
  ./scripts/docs/docs_management_server.py --port 8789
  ./scripts/docs/docs_management_server.py --repo-root /path/to/dotlineform-site
  ./scripts/docs/docs_management_server.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from studio import data_sharing_routes  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_management_service as service  # noqa: E402


MAX_BODY_BYTES = 64 * 1024


def parse_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    content_length = handler.headers.get("Content-Length", "").strip()
    try:
        length = int(content_length)
    except ValueError as exc:
        raise ValueError("Invalid Content-Length") from exc
    if length < 0 or length > MAX_BODY_BYTES:
        raise ValueError("Request body too large")
    raw = handler.rfile.read(length)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Request body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    return payload


def write_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: Dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    origin = service.allowed_origin(handler.headers.get("Origin", ""))
    if origin:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
        handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


def error_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, message: str) -> None:
    write_response(handler, status, {"ok": False, "error": message})


class DocsManagementHandler(BaseHTTPRequestHandler):
    server_version = "DocsManagementServer/0.1"

    GET_HANDLERS: Dict[str, str] = {
        **{path: "_handle_get" for path in routes.GET_PATHS},
        **{path: "_handle_get" for path in data_sharing_routes.GET_PATHS},
    }
    POST_HANDLERS: Dict[str, str] = {
        **{path: "_handle_post" for path in routes.POST_PATHS},
        **{path: "_handle_post" for path in data_sharing_routes.POST_PATHS},
    }
    OPTIONS_PATHS = tuple(dict.fromkeys((*routes.OPTIONS_PATHS, *data_sharing_routes.OPTIONS_PATHS)))

    @property
    def app(self) -> Dict[str, Any]:
        return getattr(self.server, "app_state")  # type: ignore[attr-defined]

    def _request_path(self) -> str:
        return urlparse(self.path).path

    def _request_query(self) -> dict[str, list[str]]:
        return parse_qs(urlparse(self.path).query)

    def do_OPTIONS(self) -> None:  # noqa: N802
        request_path = self._request_path()
        if request_path not in self.OPTIONS_PATHS:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return
        origin = service.allowed_origin(self.headers.get("Origin", ""))
        if not origin:
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_get(self) -> None:
        payload = service.docs_management_get_payload(
            self.app["repo_root"],
            self._request_path(),
            self._request_query(),
            dry_run=bool(self.app["dry_run"]),
        )
        write_response(self, HTTPStatus.OK, payload)

    def do_GET(self) -> None:  # noqa: N802
        try:
            handler_name = self.GET_HANDLERS.get(self._request_path())
            if handler_name:
                getattr(self, handler_name)()
                return
            error_response(self, HTTPStatus.NOT_FOUND, "Not found")
        except FileNotFoundError as error:
            error_response(self, HTTPStatus.NOT_FOUND, str(error))
        except ValueError as error:
            error_response(self, HTTPStatus.BAD_REQUEST, str(error))
        except RuntimeError as error:
            error_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def _handle_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return service.docs_management_post_response(repo_root, self._request_path(), body, dry_run=dry_run)

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        if origin and not service.allowed_origin(origin):
            error_response(self, HTTPStatus.FORBIDDEN, "Origin not allowed")
            return

        try:
            body = parse_json_body(self)
            repo_root = self.app["repo_root"]
            dry_run = self.app["dry_run"]
            handler_name = self.POST_HANDLERS.get(self._request_path())
            if handler_name:
                status, payload = getattr(self, handler_name)(repo_root, body, dry_run)
                write_response(self, status, payload)
                return
            error_response(self, HTTPStatus.NOT_FOUND, "Not found")
        except FileNotFoundError as error:
            error_response(self, HTTPStatus.NOT_FOUND, str(error))
        except ValueError as error:
            error_response(self, HTTPStatus.BAD_REQUEST, str(error))
        except RuntimeError as error:
            error_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the localhost docs-management server.")
    parser.add_argument("--port", type=int, default=8789, help="Port to bind. Default: 8789")
    parser.add_argument("--repo-root", default="", help="Explicit repo root")
    parser.add_argument("--dry-run", action="store_true", help="Validate but do not write files")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = service.detect_repo_root(args.repo_root)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), DocsManagementHandler)
    server.app_state = {  # type: ignore[attr-defined]
        "repo_root": repo_root,
        "dry_run": bool(args.dry_run),
    }
    print(f"Docs Management Server listening on http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Docs Management Server")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
