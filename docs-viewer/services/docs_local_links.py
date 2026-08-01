#!/usr/bin/env python3
"""Normalize and safely open Docs Viewer local-folder links."""

from __future__ import annotations

import re
import subprocess
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote_to_bytes, urlsplit

from studio.shared.python.local_env import runtime_env


PROJECTS_BASE_DIR_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"
INVALID_PERCENT_PATTERN = re.compile(r"%(?![0-9A-Fa-f]{2})")
SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class LocalLinkInputError(ValueError):
    pass


def _has_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _decode_percent_path(value: str) -> str:
    if INVALID_PERCENT_PATTERN.search(value):
        raise LocalLinkInputError("invalid percent escape")
    try:
        return unquote_to_bytes(value).decode("utf-8")
    except UnicodeDecodeError as error:
        raise LocalLinkInputError("invalid UTF-8 escape") from error


def _relative_parts(value: str) -> list[str]:
    if not value or value.startswith("/") or "\\" in value or _has_control(value):
        raise LocalLinkInputError("invalid relative target")
    if SCHEME_PATTERN.match(value):
        raise LocalLinkInputError("URL schemes are not allowed")
    parts = value.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise LocalLinkInputError("invalid relative target segment")
    return parts


def encode_relative_target(value: str) -> str:
    _relative_parts(value)
    return quote(value, safe="/-._~")


def decode_relative_target(value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise LocalLinkInputError("target must be one nonblank line")
    decoded = _decode_percent_path(value)
    _relative_parts(decoded)
    if encode_relative_target(decoded) != value:
        raise LocalLinkInputError("target is not canonically encoded")
    return decoded


def _shell_unescape(value: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] != "\\":
            output.append(value[index])
            index += 1
            continue
        if index + 1 == len(value):
            raise LocalLinkInputError("trailing shell escape")
        output.append(value[index + 1])
        index += 2
    return "".join(output)


def _absolute_parts(value: str) -> list[str]:
    if not value.startswith("/") or "\\" in value or _has_control(value):
        raise LocalLinkInputError("value must be an absolute POSIX path")
    parts = value[1:].split("/")
    if any(not part or part in {".", ".."} for part in parts):
        raise LocalLinkInputError("invalid absolute path segment")
    return parts


def normalize_local_path_input(value: Any, base_path: str | Path) -> dict[str, str]:
    if not isinstance(value, str) or not value or value != value.strip() or _has_control(value):
        raise LocalLinkInputError("value must be one exact nonblank line")
    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise LocalLinkInputError("invalid URL or path") from error
    if parsed.scheme.lower() == "file":
        if parsed.query or parsed.fragment or parsed.netloc.lower() not in {"", "localhost"}:
            raise LocalLinkInputError("invalid file URL")
        absolute = _decode_percent_path(parsed.path)
    else:
        if parsed.scheme or parsed.query or parsed.fragment:
            raise LocalLinkInputError("URL schemes, queries, and fragments are not allowed")
        absolute = _shell_unescape(value)
    candidate_parts = _absolute_parts(absolute)
    base_parts = _absolute_parts(str(base_path))
    if candidate_parts[: len(base_parts)] != base_parts or len(candidate_parts) == len(base_parts):
        raise LocalLinkInputError("path is outside the configured base")
    relative = "/".join(candidate_parts[len(base_parts) :])
    encoded = encode_relative_target(relative)
    label = candidate_parts[-1]
    escaped_label = label.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    return {
        "target": relative, "encoded_target": encoded, "label": label,
        "markdown": f"[{escaped_label}](dlf-local:{encoded})",
    }


def configured_base_dir(repo_root: Path) -> Path:
    raw_value = runtime_env(repo_root=repo_root).get(PROJECTS_BASE_DIR_ENV, "").strip()
    base = Path(raw_value)
    if not raw_value or not base.is_absolute() or not base.is_dir():
        raise ValueError("local-folder base is unavailable")
    _absolute_parts(str(base))
    return base


def local_folder_links_capability(repo_root: Path) -> dict[str, object]:
    try:
        base = configured_base_dir(repo_root)
    except (OSError, ValueError):
        return {"authoring": False, "activation": False, "base_path": ""}
    return {"authoring": True, "activation": sys.platform == "darwin", "base_path": str(base)}


def _response(status: HTTPStatus, state: str, *, target: str = "") -> tuple[HTTPStatus, dict[str, object]]:
    summaries = {
        "invalid_target": "The local-folder target is invalid.",
        "outside_root": "The local-folder target is outside the configured base.",
        "missing_target": "The local-folder target does not exist.",
        "unsupported_platform": "Local-folder links are unavailable on this platform.",
        "base_unavailable": "The local-folder base is unavailable.",
    }
    payload: dict[str, object] = {"ok": False, "state": state, "summary_text": summaries[state]}
    if target:
        payload["target"] = target
    return status, payload


def open_local_target_response(
    repo_root: Path, body: dict[str, Any], *, dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, object]]:
    if set(body) != {"target"}:
        return _response(HTTPStatus.BAD_REQUEST, "invalid_target")
    try:
        decoded = decode_relative_target(body["target"])
    except LocalLinkInputError:
        return _response(HTTPStatus.BAD_REQUEST, "invalid_target")
    target = encode_relative_target(decoded)
    try:
        base = configured_base_dir(repo_root).resolve(strict=True)
    except (OSError, ValueError):
        return _response(HTTPStatus.SERVICE_UNAVAILABLE, "base_unavailable", target=target)
    try:
        resolved = base.joinpath(*decoded.split("/")).resolve(strict=True)
    except (OSError, RuntimeError):
        return _response(HTTPStatus.NOT_FOUND, "missing_target", target=target)
    try:
        resolved.relative_to(base)
    except ValueError:
        return _response(HTTPStatus.FORBIDDEN, "outside_root", target=target)
    if sys.platform != "darwin":
        return _response(HTTPStatus.NOT_IMPLEMENTED, "unsupported_platform", target=target)
    command = ["open", str(resolved)] if resolved.is_dir() else ["open", "-R", str(resolved)]
    if not dry_run:
        completed = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError("Local target could not be opened.")
    return HTTPStatus.OK, {
        "ok": True, "state": "opened",
        "summary_text": "Local target opened." if not dry_run else "Local target validated.",
        "target": target, "dry_run": dry_run,
    }
