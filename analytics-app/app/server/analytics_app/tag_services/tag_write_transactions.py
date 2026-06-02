#!/usr/bin/env python3
"""Tag write-server atomic JSON write helpers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Mapping


def atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    target_path = path.resolve()

    fd, temp_name = tempfile.mkstemp(prefix=f"{target_path.name}.", suffix=".tmp", dir=str(target_path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
            handle.write("\n")
        os.replace(temp_path, target_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def atomic_write_many(payloads_by_path: Mapping[Path, Mapping[str, Any]]) -> None:
    temp_paths: Dict[Path, Path] = {}
    replaced_paths: list[Path] = []
    originals: Dict[Path, bytes | None] = {}

    try:
        for raw_path, payload in payloads_by_path.items():
            path = raw_path.resolve()
            originals[path] = path.read_bytes() if path.exists() else None

            fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
            temp_path = Path(temp_name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
                handle.write("\n")
            temp_paths[path] = temp_path

        for path, temp_path in temp_paths.items():
            os.replace(temp_path, path)
            replaced_paths.append(path)
    except Exception:
        for path in reversed(replaced_paths):
            try:
                original = originals.get(path)
                if original is not None:
                    path.write_bytes(original)
                elif path.exists():
                    path.unlink()
            except Exception:
                pass
        raise
    finally:
        for temp_path in temp_paths.values():
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
