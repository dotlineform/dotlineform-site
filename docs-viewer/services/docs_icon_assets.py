"""Resolve exact extensionless SVG names in the canonical Docs icon folder."""

from pathlib import Path
import re


ICON_NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")


def icon_asset_path(repo_root: Path, name: str) -> Path:
    """Validate a filename stem and return its existing confined SVG file.

    There are no aliases, alternate folders or extension-bearing forms. Both
    configured collection icons and authored tokens use this lookup boundary.
    """
    if not isinstance(name, str) or not ICON_NAME_PATTERN.fullmatch(name):
        raise ValueError(f"Icon requires an extensionless SVG filename stem: {name!r}")
    directory = repo_root.resolve() / "docs-viewer" / "static" / "icons"
    path = directory / f"{name}.svg"
    if path.is_symlink() or path.resolve().parent != directory:
        raise ValueError("Icon SVG must stay in the canonical icon folder")
    if not path.is_file():
        raise ValueError(f"Icon SVG not found: {name}.svg")
    return path
