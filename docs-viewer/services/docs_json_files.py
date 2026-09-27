"""Shared JSON file serialization for Docs Build and Links outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_text_atomic(path: Path, text: str) -> None:
    """Replace one output through a temporary sibling after creating its parent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(text, encoding="utf-8")
    temp_path.replace(path)


def render_json(payload: dict[str, Any]) -> str:
    """Serialize one JSON object with stable indentation and a final newline."""
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    """Read one JSON object, reporting malformed JSON with its caller-owned label."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload
