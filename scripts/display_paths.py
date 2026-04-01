from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Sequence


def _try_relative(path: Path, base: Path | None) -> Path | None:
    if base is None:
        return None
    try:
        return path.resolve().relative_to(base.resolve())
    except Exception:
        return None


def format_display_path(
    value: str | os.PathLike[str],
    *,
    repo_root: Path | None = None,
    projects_base_dir: Path | None = None,
    media_base_dir: Path | None = None,
) -> str:
    raw = os.fspath(value)
    path = Path(raw).expanduser()

    repo_rel = _try_relative(path, repo_root)
    if repo_rel is not None:
        return repo_rel.as_posix() or "."

    media_rel = _try_relative(path, media_base_dir)
    if media_rel is not None:
        return f"[media]/{media_rel.as_posix()}"

    projects_rel = _try_relative(path, projects_base_dir)
    if projects_rel is not None:
        return f"[projects]/{projects_rel.as_posix()}"

    tmp_roots = [Path(tempfile.gettempdir())]
    tmpdir_env = os.environ.get("TMPDIR", "").strip()
    if tmpdir_env:
        tmp_roots.insert(0, Path(tmpdir_env).expanduser())
    tmp_roots.extend([Path("/tmp"), Path("/var/folders")])
    for tmp_root in tmp_roots:
        tmp_rel = _try_relative(path, tmp_root)
        if tmp_rel is not None:
            return f"[tmp]/{tmp_rel.as_posix()}"

    if path.is_absolute():
        return path.name or raw
    return path.as_posix()


def format_display_command(
    cmd: Sequence[str | os.PathLike[str]],
    *,
    repo_root: Path | None = None,
    projects_base_dir: Path | None = None,
    media_base_dir: Path | None = None,
) -> str:
    formatted: list[str] = []
    for part in cmd:
        raw = os.fspath(part)
        stripped = raw.strip()
        if not stripped:
            formatted.append(raw)
            continue
        if stripped.startswith("-"):
            formatted.append(raw)
            continue

        basename = Path(stripped).name
        if basename.startswith("python"):
            formatted.append("python3")
            continue
        if basename in {"ruby", "bash", "sh"}:
            formatted.append(basename)
            continue

        if stripped.startswith("/") or stripped.startswith("."):
            formatted.append(
                format_display_path(
                    stripped,
                    repo_root=repo_root,
                    projects_base_dir=projects_base_dir,
                    media_base_dir=media_base_dir,
                )
            )
            continue

        formatted.append(raw)
    return " ".join(formatted)
