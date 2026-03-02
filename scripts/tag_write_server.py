#!/usr/bin/env python3
"""
README
======
Run:
  /Users/dlf/miniconda3/bin/python3 scripts/tag_write_server.py
  /Users/dlf/miniconda3/bin/python3 scripts/tag_write_server.py --port 8787
  /Users/dlf/miniconda3/bin/python3 scripts/tag_write_server.py --repo-root /path/to/dotlineform-site
  /Users/dlf/miniconda3/bin/python3 scripts/tag_write_server.py --dry-run

What it does:
  - Exposes a tiny localhost API for Tag Studio:
    - GET /health
    - POST /save-tags
    - POST /import-tag-registry
  - Updates:
    - assets/data/tag_assignments.json (series tag saves)
    - assets/data/tag_registry.json (registry import replace/merge)

Security constraints:
  - Binds to 127.0.0.1 only.
  - CORS allows only:
      http://localhost:*
      http://127.0.0.1:*
  - Hard allowlist permits writing only:
      <repo-root>/assets/data/tag_assignments.json
      <repo-root>/assets/data/tag_registry.json
  - No external dependencies (Python stdlib only).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TAG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$")
MAX_TAGS = 50
MAX_IMPORT_TAGS = 10000
TAG_STATUSES = {"active", "deprecated", "candidate"}
DEFAULT_ALLOWED_GROUPS = ["subject", "domain", "form", "theme"]

ALLOWED_ASSIGNMENTS_REL_PATH = Path("assets/data/tag_assignments.json")
ALLOWED_REGISTRY_REL_PATH = Path("assets/data/tag_registry.json")


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


def sanitize_tags(raw_tags: Any) -> list[str]:
    if not isinstance(raw_tags, list):
        raise ValueError("tags must be an array")
    if len(raw_tags) > MAX_TAGS:
        raise ValueError(f"tags may include at most {MAX_TAGS} entries")

    out: list[str] = []
    seen: set[str] = set()
    for idx, raw in enumerate(raw_tags):
        if not isinstance(raw, str):
            raise ValueError(f"tags[{idx}] must be a string")
        if raw == "":
            raise ValueError(f"tags[{idx}] must not be empty")
        if any((ch.isspace() or ord(ch) < 32 or ord(ch) == 127) for ch in raw):
            raise ValueError(f"tags[{idx}] contains whitespace or control characters")
        if raw in seen:
            continue
        seen.add(raw)
        out.append(raw)
    return out


def extract_allowed_groups(registry_payload: Dict[str, Any]) -> list[str]:
    policy = registry_payload.get("policy")
    if isinstance(policy, dict) and isinstance(policy.get("allowed_groups"), list):
        groups: list[str] = []
        for raw in policy.get("allowed_groups", []):
            value = str(raw or "").strip().lower()
            if not value or value in groups:
                continue
            groups.append(value)
        if groups:
            return groups
    return list(DEFAULT_ALLOWED_GROUPS)


def normalize_import_tag(raw_tag: Any, idx: int, allowed_groups: set[str]) -> Dict[str, str]:
    if not isinstance(raw_tag, dict):
        raise ValueError(f"import_registry.tags[{idx}] must be an object")

    tag_id = str(raw_tag.get("tag_id") or "").strip().lower()
    group = str(raw_tag.get("group") or "").strip().lower()
    label = str(raw_tag.get("label") or "").strip()
    status = str(raw_tag.get("status") or "active").strip().lower()
    description = str(raw_tag.get("description") or "").strip()

    if not TAG_ID_RE.fullmatch(tag_id):
        raise ValueError(f"import_registry.tags[{idx}].tag_id must match <group>:<slug>")
    if ":" not in tag_id:
        raise ValueError(f"import_registry.tags[{idx}].tag_id must include ':'")
    tag_group = tag_id.split(":", 1)[0]
    if group != tag_group:
        raise ValueError(f"import_registry.tags[{idx}] group must match tag_id prefix")
    if group not in allowed_groups:
        raise ValueError(f"import_registry.tags[{idx}].group is not allowed")
    if not label:
        raise ValueError(f"import_registry.tags[{idx}].label must not be empty")
    if status not in TAG_STATUSES:
        raise ValueError(f"import_registry.tags[{idx}].status must be one of {sorted(TAG_STATUSES)}")

    return {
        "tag_id": tag_id,
        "group": group,
        "label": label,
        "status": status,
        "description": description,
    }


def sanitize_import_registry(raw_registry: Any, allowed_groups: list[str]) -> list[Dict[str, str]]:
    if not isinstance(raw_registry, dict):
        raise ValueError("import_registry must be an object")

    raw_tags = raw_registry.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("import_registry.tags must be an array")
    if len(raw_tags) > MAX_IMPORT_TAGS:
        raise ValueError(f"import_registry.tags may include at most {MAX_IMPORT_TAGS} entries")

    out_order: list[str] = []
    out_by_id: dict[str, Dict[str, str]] = {}
    allowed_set = set(allowed_groups)
    for idx, raw_tag in enumerate(raw_tags):
        normalized = normalize_import_tag(raw_tag, idx, allowed_set)
        tag_id = normalized["tag_id"]
        if tag_id not in out_by_id:
            out_order.append(tag_id)
        out_by_id[tag_id] = normalized

    return [out_by_id[tag_id] for tag_id in out_order]


def load_json_object(path: Path, default_payload: Dict[str, Any], object_name: str) -> Dict[str, Any]:
    if not path.exists():
        return default_payload

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"failed to parse {object_name}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{object_name} must be a JSON object")
    return payload


def load_assignments(path: Path) -> Dict[str, Any]:
    return load_json_object(
        path,
        {
            "tag_assignments_version": "tag_assignments_v1",
            "updated_at_utc": utc_now(),
            "series": {},
        },
        "tag assignments",
    )


def load_registry(path: Path) -> Dict[str, Any]:
    return load_json_object(
        path,
        {
            "tag_registry_version": "tag_registry_v1",
            "updated_at_utc": utc_now(),
            "policy": {"allowed_groups": list(DEFAULT_ALLOWED_GROUPS)},
            "tags": [],
        },
        "tag registry",
    )


def apply_assignment_update(payload: Dict[str, Any], series_id: str, tags: list[str], now_utc: str) -> Dict[str, Any]:
    if not isinstance(payload.get("series"), dict):
        payload["series"] = {}
    if "tag_assignments_version" not in payload:
        payload["tag_assignments_version"] = "tag_assignments_v1"

    series_obj = payload["series"]
    row = series_obj.get(series_id)
    if not isinstance(row, dict):
        row = {}
        series_obj[series_id] = row

    row["tags"] = tags
    row["updated_at_utc"] = now_utc
    payload["updated_at_utc"] = now_utc
    return payload


def apply_registry_import(
    existing_payload: Dict[str, Any],
    import_registry: Any,
    mode: str,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if mode not in {"replace", "merge", "add"}:
        raise ValueError("mode must be one of: replace, merge, add")

    allowed_groups = extract_allowed_groups(existing_payload)
    imported_tags = sanitize_import_registry(import_registry, allowed_groups)

    raw_existing_tags = existing_payload.get("tags")
    existing_tags = raw_existing_tags if isinstance(raw_existing_tags, list) else []

    existing_order: list[str] = []
    existing_by_id: dict[str, Dict[str, Any]] = {}
    for raw in existing_tags:
        if not isinstance(raw, dict):
            continue
        tag_id = str(raw.get("tag_id") or "").strip().lower()
        if not tag_id:
            continue
        if tag_id not in existing_by_id:
            existing_order.append(tag_id)
        existing_by_id[tag_id] = raw

    import_order = [tag["tag_id"] for tag in imported_tags]
    import_by_id = {tag["tag_id"]: tag for tag in imported_tags}

    overwritten = 0
    added = 0
    unchanged = 0
    removed = 0

    if mode == "replace":
        existing_ids = set(existing_by_id.keys())
        imported_ids = set(import_by_id.keys())
        overwritten = len(existing_ids & imported_ids)
        added = len(imported_ids - existing_ids)
        removed = len(existing_ids - imported_ids)
        final_tags: list[Any] = []
        for tag_id in import_order:
            tag = dict(import_by_id[tag_id])
            tag["updated_at_utc"] = now_utc
            final_tags.append(tag)
    elif mode == "merge":
        final_tags = []
        remaining_import = dict(import_by_id)
        for existing_tag in existing_tags:
            if not isinstance(existing_tag, dict):
                unchanged += 1
                final_tags.append(existing_tag)
                continue

            existing_tag_id = str(existing_tag.get("tag_id") or "").strip().lower()
            if existing_tag_id and existing_tag_id in remaining_import:
                overwritten += 1
                incoming = dict(remaining_import.pop(existing_tag_id))
                incoming["updated_at_utc"] = now_utc
                final_tags.append(incoming)
            else:
                unchanged += 1
                final_tags.append(existing_tag)

        for tag_id in import_order:
            if tag_id not in remaining_import:
                continue
            added += 1
            incoming = dict(remaining_import.pop(tag_id))
            incoming["updated_at_utc"] = now_utc
            final_tags.append(incoming)
    else:  # mode == "add"
        final_tags = list(existing_tags)
        existing_ids = set(existing_by_id.keys())
        for tag_id in import_order:
            if tag_id in existing_ids:
                unchanged += 1
                continue
            incoming = dict(import_by_id[tag_id])
            incoming["updated_at_utc"] = now_utc
            final_tags.append(incoming)
            added += 1

    if "tag_registry_version" not in existing_payload:
        existing_payload["tag_registry_version"] = "tag_registry_v1"
    if not isinstance(existing_payload.get("policy"), dict):
        existing_payload["policy"] = {"allowed_groups": allowed_groups}

    existing_payload["tags"] = final_tags
    existing_payload["updated_at_utc"] = now_utc

    stats = {
        "mode": mode,
        "imported_total": len(imported_tags),
        "overwritten": overwritten,
        "added": added,
        "unchanged": unchanged,
        "removed": removed,
        "final_total": len(final_tags),
    }
    return existing_payload, stats


def atomic_write(path: Path, payload: Dict[str, Any]) -> None:
    backup_path = path.with_suffix(path.suffix + ".bak")
    if path.exists():
        shutil.copy2(path, backup_path)

    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=False)
            fh.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


class TagWriteServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_cls,
        assignments_path: Path,
        registry_path: Path,
        allowed_write_paths: set[Path],
        dry_run: bool,
    ):
        super().__init__(server_address, handler_cls)
        self.assignments_path = assignments_path
        self.registry_path = registry_path
        self.allowed_write_paths = {path.resolve() for path in allowed_write_paths}
        self.dry_run = dry_run


class Handler(BaseHTTPRequestHandler):
    server: TagWriteServer  # type: ignore[assignment]

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path not in {"/save-tags", "/import-tag-registry"}:
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

        if self.path != "/health":
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "service": "tag_write_server",
                "tag_assignments_path": str(self.server.assignments_path),
                "tag_registry_path": str(self.server.registry_path),
                "time_utc": utc_now(),
            },
            allowed,
        )

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        try:
            if self.path == "/save-tags":
                self._handle_save_tags(allowed)
                return
            if self.path == "/import-tag-registry":
                self._handle_import_tag_registry(allowed)
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)}, allowed)
        except Exception as exc:  # noqa: BLE001
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"internal error: {exc}"}, allowed)

    def _handle_save_tags(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        series_id = body.get("series_id")
        tags = body.get("tags")
        _ = body.get("client_time_utc")

        if not isinstance(series_id, str) or not series_id or not SLUG_RE.fullmatch(series_id):
            raise ValueError("series_id must be a non-empty slug-safe string")

        sanitized_tags = sanitize_tags(tags)
        now_utc = utc_now()

        payload = load_assignments(self.server.assignments_path)
        updated_payload = apply_assignment_update(payload, series_id, sanitized_tags, now_utc)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "series_id": series_id,
            "updated_at_utc": now_utc,
            "tag_count": len(sanitized_tags),
        }

        target_path = self.server.assignments_path.resolve()
        if not self.server.dry_run:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            atomic_write(target_path, updated_payload)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "series_id": series_id,
                "tags": sanitized_tags,
                "updated_at_utc": now_utc,
            }

        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_import_tag_registry(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        mode = str(body.get("mode") or "").strip().lower()
        import_registry = body.get("import_registry")
        _ = body.get("client_time_utc")

        now_utc = utc_now()
        existing_payload = load_registry(self.server.registry_path)
        updated_payload, stats = apply_registry_import(existing_payload, import_registry, mode, now_utc)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "updated_at_utc": now_utc,
            **stats,
        }

        target_path = self.server.registry_path.resolve()
        if not self.server.dry_run:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            atomic_write(target_path, updated_payload)
        else:
            response_payload["dry_run"] = True
            response_payload["would_write"] = {
                "updated_at_utc": now_utc,
                **stats,
            }

        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            raise ValueError("missing Content-Length")
        try:
            length = int(content_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 0 or length > 1024 * 1024:
            raise ValueError("request body too large")

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
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
        # Keep stdout concise but still provide basic request logs.
        print(f"[tag_write_server] {self.address_string()} - {fmt % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Localhost-only tag write service.")
    parser.add_argument("--port", type=int, default=8787, help="Server port (default: 8787)")
    parser.add_argument("--repo-root", default="", help="Repo root path (auto-detected if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Validate and respond without writing files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = detect_repo_root(args.repo_root)
    assignments_path = (repo_root / ALLOWED_ASSIGNMENTS_REL_PATH).resolve()
    registry_path = (repo_root / ALLOWED_REGISTRY_REL_PATH).resolve()
    allowed_paths = {assignments_path, registry_path}

    server = TagWriteServer(
        ("127.0.0.1", args.port),
        Handler,
        assignments_path=assignments_path,
        registry_path=registry_path,
        allowed_write_paths=allowed_paths,
        dry_run=args.dry_run,
    )
    mode = "dry-run" if args.dry_run else "write"
    print(
        f"tag_write_server listening on http://127.0.0.1:{args.port} "
        f"(mode={mode}, assignments={assignments_path}, registry={registry_path})"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("tag_write_server stopped")


if __name__ == "__main__":
    main()
