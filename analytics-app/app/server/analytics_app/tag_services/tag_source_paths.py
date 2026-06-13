"""Analytics-owned tag source path contract."""

from __future__ import annotations

from pathlib import Path


TAG_SOURCE_ROOT_REL_PATH = Path("analytics-app/data/canonical")
TAG_ASSIGNMENTS_REL_PATH = TAG_SOURCE_ROOT_REL_PATH / "tag-assignments.json"
TAG_REGISTRY_REL_PATH = TAG_SOURCE_ROOT_REL_PATH / "tag-registry.json"
TAG_ALIASES_REL_PATH = TAG_SOURCE_ROOT_REL_PATH / "tag-aliases.json"
TAG_GROUPS_REL_PATH = TAG_SOURCE_ROOT_REL_PATH / "tag-groups.json"
SERIES_INDEX_REL_PATH = Path("site/assets/data/series_index.json")


def resolve_repo_path(repo_root: Path, rel_path: Path) -> Path:
    return (repo_root / rel_path).resolve()


def tag_source_rel_paths() -> dict[str, Path]:
    return {
        "tag_assignments": TAG_ASSIGNMENTS_REL_PATH,
        "tag_registry": TAG_REGISTRY_REL_PATH,
        "tag_aliases": TAG_ALIASES_REL_PATH,
        "tag_groups": TAG_GROUPS_REL_PATH,
    }
