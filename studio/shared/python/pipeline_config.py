#!/usr/bin/env python3
"""Shared pipeline config loader and path helpers."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Mapping

try:
    from .local_env import runtime_env
except ImportError:  # pragma: no cover - direct sys.path import fallback
    from local_env import runtime_env


CONFIG_REL_PATH = Path("_data/pipeline.json")

DEFAULT_PIPELINE_CONFIG: Dict[str, Any] = {
    "env": {
        "projects_base_dir": "DOTLINEFORM_PROJECTS_BASE_DIR",
        "srcset_jobs": "MAKE_SRCSET_JOBS",
        "srcset_selected_ids_file": "MAKE_SRCSET_WORK_IDS_FILE",
        "srcset_success_ids_file": "MAKE_SRCSET_SUCCESS_IDS_FILE",
    },
    "paths": {
        "workbooks": {
            "bulk_import": "data/works_bulk_import.xlsx",
        },
        "source_roots": {
            "work_media": {
                "default": "projects",
                "roots": {
                    "projects": "projects",
                    "processing": "processing",
                },
            },
        },
        "source_subdirs": {
            "prose": "site text",
        },
        "media": {
            "root_subdir": "catalogue/media",
            "work": {
                "input_subdir": "works/make_srcset_images",
                "output_subdir": "works/srcset_images",
            },
            "work_details": {
                "input_subdir": "work_details/make_srcset_images",
                "output_subdir": "work_details/srcset_images",
            },
            "work_files_subdir": "works/files",
        },
    },
    "variants": {
        "primary": {
            "widths": [800, 1200, 1600],
            "suffix": "primary",
            "output_subdir": "primary",
            "preferred_width": 1600,
        },
        "thumb": {
            "sizes": [96, 192],
            "suffix": "thumb",
            "output_subdir": "thumb",
        },
        "compatibility": {
            "generate_widths": [800, 1200, 1600],
            "render_widths": [800, 1200, 1600],
            "accepted_legacy_widths": [800, 1200, 1600, 2400],
        },
    },
    "encoding": {
        "format": "webp",
        "codec": "libwebp",
        "preset": "photo",
        "primary_quality": 82,
        "thumb_quality": 78,
        "compression_level": 6,
    },
}


def resolve_repo_root(script_path: str | Path | None = None, repo_root: str | Path | None = None) -> Path:
    if repo_root is not None:
        resolved = Path(repo_root).expanduser().resolve()
        if not (resolved / "site-tools" / "config" / "site-tools.json").exists():
            raise ValueError(f"repo root is missing site-tools/config/site-tools.json: {resolved}")
        return resolved

    start = Path(script_path if script_path is not None else __file__).expanduser().resolve()
    candidates = [start] if start.is_dir() else [start.parent, *start.parents]
    for candidate in candidates:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate
    raise ValueError("could not resolve repo root for pipeline config")


def _deep_merge(base: Dict[str, Any], overrides: Mapping[str, Any]) -> Dict[str, Any]:
    for key, value in overrides.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def load_pipeline_config(
    script_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> Dict[str, Any]:
    resolved_repo_root = resolve_repo_root(script_path=script_path, repo_root=repo_root)
    config = copy.deepcopy(DEFAULT_PIPELINE_CONFIG)
    config_path = resolved_repo_root / CONFIG_REL_PATH
    if config_path.exists():
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"pipeline config must be a JSON object: {config_path}")
        _deep_merge(config, loaded)
    return config


def env_var_name(config: Mapping[str, Any], key: str) -> str:
    value = str(config["env"][key]).strip()
    if not value:
        raise ValueError(f"pipeline env name is empty for key: {key}")
    return value


def env_var_value(
    config: Mapping[str, Any],
    key: str,
    environ: Mapping[str, str] | None = None,
) -> str:
    source = environ if environ is not None else runtime_env()
    return str(source.get(env_var_name(config, key), "")).strip()


def media_mode_input_subdir(config: Mapping[str, Any], mode: str) -> Path:
    return Path(str(config["paths"]["media"][mode]["input_subdir"]))


def media_root_subdir(config: Mapping[str, Any]) -> Path:
    return Path(str(config["paths"]["media"]["root_subdir"]))


def media_mode_output_subdir(config: Mapping[str, Any], mode: str) -> Path:
    return Path(str(config["paths"]["media"][mode]["output_subdir"]))


def media_work_files_subdir(config: Mapping[str, Any]) -> Path:
    return Path(str(config["paths"]["media"]["work_files_subdir"]))


def work_media_source_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the checked logical Work-media source map and configured default."""

    raw = config["paths"]["source_roots"]["work_media"]
    if not isinstance(raw, Mapping):
        raise ValueError("paths.source_roots.work_media must be an object")
    default_source_id = str(raw.get("default") or "").strip()
    raw_roots = raw.get("roots")
    if not isinstance(raw_roots, Mapping) or not raw_roots:
        raise ValueError("paths.source_roots.work_media.roots must be a non-empty object")

    roots: Dict[str, str] = {}
    for raw_source_id, raw_subdir in raw_roots.items():
        source_id = str(raw_source_id)
        if not source_id or source_id != source_id.strip() or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in source_id
        ):
            raise ValueError(f"invalid Work media source identity: {source_id!r}")
        subdir_text = str(raw_subdir or "")
        subdir = Path(subdir_text)
        if (
            not subdir_text
            or subdir_text != subdir_text.strip()
            or "\\" in subdir_text
            or not subdir.parts
            or subdir.is_absolute()
            or ".." in subdir.parts
        ):
            raise ValueError(f"invalid Work media source subdirectory for {source_id!r}")
        roots[source_id] = subdir.as_posix()

    if default_source_id not in roots:
        raise ValueError("default Work media source identity must exist in roots")
    return {
        "default": default_source_id,
        "roots": roots,
    }


def work_media_source_ids(config: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(work_media_source_config(config)["roots"].keys())


def default_work_media_source_id(config: Mapping[str, Any]) -> str:
    return str(work_media_source_config(config)["default"])


def work_media_source_root_subdir(config: Mapping[str, Any], source_id: str) -> Path:
    source_config = work_media_source_config(config)
    normalized_source_id = str(source_id or "").strip()
    if normalized_source_id not in source_config["roots"]:
        raise ValueError(f"unknown Work media source identity: {normalized_source_id or '(empty)'}")
    return Path(str(source_config["roots"][normalized_source_id]))


def source_works_prose_subdir(config: Mapping[str, Any]) -> Path:
    return Path(str(config["paths"]["source_subdirs"]["prose"]))


def bulk_import_workbook_path(config: Mapping[str, Any]) -> Path:
    return Path(str(config["paths"]["workbooks"]["bulk_import"]))
