from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from .config import PublicSiteConfig


@dataclass(frozen=True)
class AuditResult:
    checked_count: int


def audit_artifact(destination: Path, config: PublicSiteConfig) -> AuditResult:
    if not destination.exists():
        raise FileNotFoundError(f"artifact destination does not exist: {destination}")

    missing = [
        required
        for required in config.required_files
        if not (destination / required).is_file()
    ]
    if missing:
        raise RuntimeError("artifact is missing required files: " + ", ".join(missing))

    missing_directories = [
        required
        for required in config.required_directories
        if not (destination / required).is_dir()
    ]
    if missing_directories:
        raise RuntimeError("artifact is missing required directories: " + ", ".join(missing_directories))

    checked_count = 0
    for path in destination.rglob("*"):
        if not path.is_file():
            continue
        checked_count += 1
        relative_path = path.relative_to(destination).as_posix()
        _check_denied_path(relative_path, config)
        _check_html_tokens(path, relative_path, config.denied_html_tokens)

    return AuditResult(checked_count=checked_count)


def _check_denied_path(relative_path: str, config: PublicSiteConfig) -> None:
    for prefix in config.denied_path_prefixes:
        if relative_path == prefix.rstrip("/") or relative_path.startswith(prefix):
            raise RuntimeError(f"artifact contains denied path: {relative_path}")

    name = Path(relative_path).name
    for pattern in config.denied_file_patterns:
        if fnmatch(name, pattern) or fnmatch(relative_path, pattern):
            raise RuntimeError(f"artifact contains denied file: {relative_path}")


def _check_html_tokens(path: Path, relative_path: str, denied_tokens: tuple[str, ...]) -> None:
    if path.suffix.lower() not in {".html", ".htm"}:
        return
    text = path.read_text(encoding="utf-8")
    for token in denied_tokens:
        if token in text:
            raise RuntimeError(f"artifact HTML contains denied token {token!r}: {relative_path}")
