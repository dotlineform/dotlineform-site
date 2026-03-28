#!/usr/bin/env python3
"""Shared pipeline config loader and path helpers."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping


CONFIG_REL_PATH = Path("_data/pipeline.json")

DEFAULT_PIPELINE_CONFIG: Dict[str, Any] = {
    "env": {
        "projects_base_dir": "DOTLINEFORM_PROJECTS_BASE_DIR",
        "media_base_dir": "DOTLINEFORM_MEDIA_BASE_DIR",
        "srcset_jobs": "MAKE_SRCSET_JOBS",
        "srcset_selected_ids_file": "MAKE_SRCSET_WORK_IDS_FILE",
        "srcset_success_ids_file": "MAKE_SRCSET_SUCCESS_IDS_FILE",
    },
    "paths": {
        "source_roots": {
            "works": "projects",
            "moments": "moments",
        },
        "source_subdirs": {
            "moments_images": "images",
            "prose": "site text",
        },
        "media": {
            "work": {
                "input_subdir": "works/make_srcset_images",
                "output_subdir": "works/srcset_images",
            },
            "work_details": {
                "input_subdir": "work_details/make_srcset_images",
                "output_subdir": "work_details/srcset_images",
            },
            "moment": {
                "input_subdir": "moments/make_srcset_images",
                "output_subdir": "moments/srcset_images",
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
        if not (resolved / "_config.yml").exists():
            raise ValueError(f"repo root is missing _config.yml: {resolved}")
        return resolved

    start = Path(script_path if script_path is not None else __file__).expanduser().resolve()
    candidates = [start] if start.is_dir() else [start.parent, *start.parents]
    for candidate in candidates:
        if (candidate / "_config.yml").exists():
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
    source = environ if environ is not None else os.environ
    return str(source.get(env_var_name(config, key), "")).strip()


def media_mode_input_subdir(config: Mapping[str, Any], mode: str) -> Path:
    return Path(str(config["paths"]["media"][mode]["input_subdir"]))


def media_mode_output_subdir(config: Mapping[str, Any], mode: str) -> Path:
    return Path(str(config["paths"]["media"][mode]["output_subdir"]))


def media_work_files_subdir(config: Mapping[str, Any]) -> Path:
    return Path(str(config["paths"]["media"]["work_files_subdir"]))


def source_works_root_subdir(config: Mapping[str, Any]) -> Path:
    return Path(str(config["paths"]["source_roots"]["works"]))


def source_moments_root_subdir(config: Mapping[str, Any]) -> Path:
    return Path(str(config["paths"]["source_roots"]["moments"]))


def source_moments_images_subdir(config: Mapping[str, Any]) -> Path:
    return source_moments_root_subdir(config) / Path(str(config["paths"]["source_subdirs"]["moments_images"]))


def source_works_prose_subdir(config: Mapping[str, Any]) -> Path:
    return Path(str(config["paths"]["source_subdirs"]["prose"]))


def join_base_and_subdir(base_dir: str, subdir: str | Path) -> str:
    base = str(base_dir or "").strip()
    if not base:
        return ""
    return str(Path(base) / Path(subdir))
