#!/usr/bin/env python3
"""Tag write-server backup and atomic JSON write helpers."""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Mapping


def backup_stamp_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")


def atomic_write(path: Path, payload: Mapping[str, Any], backups_dir: Path) -> Path | None:
    backups_dir.mkdir(parents=True, exist_ok=True)
    target_path = path.resolve()
    backup_path = backups_dir / f"{target_path.name}.bak-{backup_stamp_now()}"
    created_backup: Path | None = None
    if target_path.exists():
        shutil.copy2(target_path, backup_path)
        created_backup = backup_path

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

    return created_backup


def atomic_write_many(payloads_by_path: Mapping[Path, Mapping[str, Any]], backups_dir: Path) -> list[Path]:
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = backup_stamp_now()
    backups: Dict[Path, Path] = {}
    temp_paths: Dict[Path, Path] = {}
    replaced_paths: list[Path] = []

    try:
        for raw_path, payload in payloads_by_path.items():
            path = raw_path.resolve()
            if path.exists():
                backup_path = backups_dir / f"{path.name}.bak-{stamp}"
                shutil.copy2(path, backup_path)
                backups[path] = backup_path

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
            backup_path = backups.get(path)
            try:
                if backup_path and backup_path.exists():
                    shutil.copy2(backup_path, path)
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

    return list(backups.values())
