#!/usr/bin/env python3
"""
Localhost-only read service for allowlisted Studio audits.

Run:
  ./scripts/studio/audit_service.py
  ./scripts/studio/audit_service.py --port 8790
  ./scripts/studio/audit_service.py --repo-root /path/to/dotlineform-site

Endpoints:
  GET /health
  GET /audits
  POST /audits/run

Security constraints:
  - Binds to 127.0.0.1 only.
  - CORS allows only http://localhost:* and http://127.0.0.1:*.
  - Runs only server-side allowlisted audit IDs.
  - Does not accept command text, paths, shell flags, environment, or cwd from the browser.
  - Writes minimal local logs under var/studio/audits/logs/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from script_logging import append_script_log  # noqa: E402


MAX_BODY_BYTES = 64 * 1024
LOGS_REL_DIR = Path("var/studio/audits/logs")
RUN_AUDIT_PATH = "/audits/run"


@dataclass(frozen=True)
class AuditDefinition:
    audit_id: str
    label: str
    description: str
    argv: tuple[str, ...]

    def public_payload(self) -> Dict[str, str]:
        return {
            "audit_id": self.audit_id,
            "label": self.label,
            "description": self.description,
        }


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_repo_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        found = find_repo_root(start)
        if found is not None:
            return found

    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def allowed_origin(origin: str) -> Optional[str]:
    if not origin:
        return None

    try:
        parsed = urlparse(origin)
    except Exception:
        return None

    if parsed.scheme != "http":
        return None
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        return None
    if parsed.path not in {"", "/"}:
        return None
    if parsed.params or parsed.query or parsed.fragment:
        return None
    if parsed.port is None:
        return f"{parsed.scheme}://{parsed.hostname}"
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"


def build_audit_registry(repo_root: Path) -> Dict[str, AuditDefinition]:
    return {
        "studio-ready-state": AuditDefinition(
            audit_id="studio-ready-state",
            label="Studio ready state",
            description="Checks Studio route-ready template contracts and static-route drift.",
            argv=(
                sys.executable,
                str(repo_root / "scripts" / "audit_studio_ready_state.py"),
                "--strict",
                "--json",
            ),
        )
    }


class AuditServiceServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_cls,
        repo_root: Path,
        audits: Dict[str, AuditDefinition],
    ):
        super().__init__(server_address, handler_cls)
        self.repo_root = repo_root.resolve()
        self.audits = audits

    def log_event(self, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        try:
            append_script_log(
                Path(__file__),
                event=event,
                details=details,
                repo_root=self.repo_root,
                log_dir_rel=LOGS_REL_DIR,
            )
        except Exception:
            pass


class Handler(BaseHTTPRequestHandler):
    server: AuditServiceServer  # type: ignore[assignment]

    def _request_path(self) -> str:
        return urlparse(self.path).path

    def do_OPTIONS(self) -> None:  # noqa: N802
        request_path = self._request_path()
        if request_path != RUN_AUDIT_PATH:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
            return

        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        self.send_response(HTTPStatus.NO_CONTENT)
        self._write_cors_headers(allowed)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        request_path = self._request_path()
        if request_path == "/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "service": "audit_service",
                    "audits": sorted(self.server.audits.keys()),
                    "time_utc": utc_now(),
                },
                allowed,
            )
            return

        if request_path == "/audits":
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "audits": [audit.public_payload() for audit in self.server.audits.values()],
                    "time_utc": utc_now(),
                },
                allowed,
            )
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        if self._request_path() != RUN_AUDIT_PATH:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
            return

        try:
            self._handle_run_audit(allowed)
        except ValueError as exc:
            self.server.log_event("request_error", {"path": RUN_AUDIT_PATH, "error": str(exc), "kind": "validation"})
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)}, allowed)
        except Exception as exc:  # noqa: BLE001
            self.server.log_event("request_error", {"path": RUN_AUDIT_PATH, "error": str(exc), "kind": "internal"})
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"internal error: {exc}"}, allowed)

    def _handle_run_audit(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        audit_id = str(body.get("audit_id") or "").strip()
        if not audit_id:
            raise ValueError("audit_id is required")
        audit = self.server.audits.get(audit_id)
        if audit is None:
            raise ValueError("audit_id is not allowlisted")

        started_at = utc_now()
        started = time.monotonic()
        result = subprocess.run(
            audit.argv,
            cwd=self.server.repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        finished_at = utc_now()
        duration = time.monotonic() - started

        audit_payload: Dict[str, Any]
        try:
            parsed = json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"audit returned invalid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("audit returned invalid JSON payload")
        audit_payload = parsed

        summary = audit_payload.get("summary") if isinstance(audit_payload.get("summary"), dict) else {}
        response_payload = {
            "ok": True,
            "audit_id": audit.audit_id,
            "label": audit.label,
            "status": str(audit_payload.get("status") or ("passed" if result.returncode == 0 else "failed")),
            "exit_code": result.returncode,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": round(duration, 3),
            "summary": {
                "errors": int(summary.get("errors") or 0),
                "warnings": int(summary.get("warnings") or 0),
            },
            "totals": audit_payload.get("totals") if isinstance(audit_payload.get("totals"), dict) else {},
            "findings": audit_payload.get("findings") if isinstance(audit_payload.get("findings"), list) else [],
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        self.server.log_event(
            "audit_run",
            {
                "audit_id": audit.audit_id,
                "status": response_payload["status"],
                "exit_code": result.returncode,
                "errors": response_payload["summary"]["errors"],
                "warnings": response_payload["summary"]["warnings"],
                "duration_seconds": response_payload["duration_seconds"],
            },
        )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _read_json_body(self) -> Dict[str, Any]:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid content length") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request body too large")
        data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _send_json(self, status: HTTPStatus, payload: Dict[str, Any], allowed: Optional[str] = None) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._write_cors_headers(allowed)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _write_cors_headers(self, allowed: Optional[str]) -> None:
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        print(f"[audit_service] {self.address_string()} - {fmt % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Localhost-only Studio audit service.")
    parser.add_argument("--port", type=int, default=8790, help="Server port (default: 8790)")
    parser.add_argument("--repo-root", default="", help="Repo root path (auto-detected if omitted)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = detect_repo_root(args.repo_root)
    audits = build_audit_registry(repo_root)
    server = AuditServiceServer(("127.0.0.1", args.port), Handler, repo_root=repo_root, audits=audits)
    print(
        f"audit_service listening on http://127.0.0.1:{args.port} "
        f"(audits={','.join(sorted(audits.keys()))})"
    )
    server.log_event("server_start", {"port": args.port, "audits": sorted(audits.keys())})
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down audit_service")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
