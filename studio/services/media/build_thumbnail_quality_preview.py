#!/usr/bin/env python3
"""Build Studio thumbnail quality comparison previews from source images."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from scripts.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

from local_env import runtime_env  # noqa: E402
from pipeline_config import env_var_name, load_pipeline_config, resolve_repo_root  # noqa: E402


SOURCE_SUBDIR = "thumbnail-quality-preview"
OUTPUT_IMG_REL_DIR = Path("assets/studio/img/thumbnail-quality")
OUTPUT_DATA_REL_PATH = Path("studio/data/generated/thumbnail-quality/thumbnail-quality-preview.json")
SUPPORTED_EXTENSIONS = {".avif", ".heic", ".heif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}

LOWER_VARIANTS = [
    {"id": "q70-192", "label": "q70 192", "size": 192, "quality": 70},
    {"id": "q62-192", "label": "q62 192", "size": 192, "quality": 62},
    {"id": "q54-192", "label": "q54 192", "size": 192, "quality": 54},
    {"id": "q62-160", "label": "q62 160", "size": 160, "quality": 62},
    {"id": "q62-96", "label": "q62 96", "size": 96, "quality": 62},
    {"id": "q54-96", "label": "q54 96", "size": 96, "quality": 54},
]


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    return text or "source"


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    kib = size / 1024
    if kib < 1024:
        return f"{kib:.1f} KB"
    return f"{kib / 1024:.2f} MB"


def repo_url(path: Path) -> str:
    return "/" + path.as_posix().lstrip("/")


def source_dir_for_env(config: Mapping[str, Any], env: Mapping[str, str]) -> Path:
    env_name = env_var_name(config, "projects_base_dir")
    base = str(env.get(env_name) or "").strip()
    if not base:
        raise ValueError(f"{env_name} is not set")
    return Path(base).expanduser() / SOURCE_SUBDIR


def collect_sources(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        raise ValueError(f"source directory does not exist: {source_dir}")
    if not source_dir.is_dir():
        raise ValueError(f"source path is not a directory: {source_dir}")
    return [
        path
        for path in sorted(source_dir.iterdir(), key=lambda item: item.name.lower())
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def ffmpeg_thumb_command(src: Path, dest: Path, *, codec: str, preset: str, quality: int, compression_level: int, size: int) -> list[str]:
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(src),
        "-map_metadata",
        "-1",
        "-vf",
        f"scale='if(gt(iw,ih),-1,{size})':'if(gt(iw,ih),{size},-1)':flags=lanczos,crop={size}:{size}",
        "-c:v",
        codec,
        "-preset",
        preset,
        "-q:v",
        str(quality),
        "-compression_level",
        str(compression_level),
        str(dest),
    ]


def setting_summary(*, codec: str, preset: str, quality: int, compression_level: int, size: int) -> Dict[str, Any]:
    return {
        "size": size,
        "codec": codec,
        "preset": preset,
        "quality": quality,
        "compression_level": compression_level,
        "ffmpeg_args": [
            "-c:v",
            codec,
            "-preset",
            preset,
            "-q:v",
            str(quality),
            "-compression_level",
            str(compression_level),
        ],
        "scale_filter": f"scale/crop {size}x{size} lanczos",
    }


def run_ffmpeg(cmd: Iterable[str]) -> None:
    proc = subprocess.run(list(cmd), text=True, capture_output=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(detail or "ffmpeg failed")


def output_record(path: Path, rel_path: Path, *, variant_id: str, label: str, settings: Mapping[str, Any]) -> Dict[str, Any]:
    size_bytes = path.stat().st_size
    return {
        "variant_id": variant_id,
        "label": label,
        "url": repo_url(rel_path),
        "path": rel_path.as_posix(),
        "size_bytes": size_bytes,
        "size_label": format_bytes(size_bytes),
        "settings": dict(settings),
    }


def build_preview(
    repo_root: Path,
    *,
    env: Mapping[str, str] | None = None,
    write: bool = False,
    missing_only: bool = False,
) -> Dict[str, Any]:
    config = load_pipeline_config(repo_root=repo_root)
    runtime = dict(env if env is not None else runtime_env(repo_root=repo_root))
    source_dir = source_dir_for_env(config, runtime)
    sources = collect_sources(source_dir)
    encoding = config["encoding"]
    thumb_quality = int(encoding["thumb_quality"])
    codec = str(encoding["codec"])
    preset = str(encoding["preset"])
    compression_level = int(encoding["compression_level"])
    current_size = int(config["variants"]["thumb"]["sizes"][-1])
    image_format = str(encoding["format"])
    output_img_dir = repo_root / OUTPUT_IMG_REL_DIR

    if write and shutil.which("ffmpeg") is None:
        raise ValueError("ffmpeg not found on PATH")

    baseline_settings = setting_summary(
        codec=codec,
        preset=preset,
        quality=thumb_quality,
        compression_level=compression_level,
        size=current_size,
    )
    variant_settings = [
        {
            **variant,
            "settings": setting_summary(
                codec=codec,
                preset=preset,
                quality=int(variant["quality"]),
                compression_level=compression_level,
                size=int(variant["size"]),
            ),
        }
        for variant in LOWER_VARIANTS
    ]

    rows: list[Dict[str, Any]] = []
    planned_outputs: list[str] = []
    if write:
        output_img_dir.mkdir(parents=True, exist_ok=True)

    for index, source in enumerate(sources, start=1):
        source_slug = f"{index:02d}-{slugify(source.stem)}"
        baseline_rel = OUTPUT_IMG_REL_DIR / f"{source_slug}-current.{image_format}"
        baseline_abs = repo_root / baseline_rel
        planned_outputs.append(baseline_rel.as_posix())
        if write and not (missing_only and baseline_abs.exists()):
            run_ffmpeg(
                ffmpeg_thumb_command(
                    source,
                    baseline_abs,
                    codec=codec,
                    preset=preset,
                    quality=thumb_quality,
                    compression_level=compression_level,
                    size=current_size,
                )
            )
        variants: list[Dict[str, Any]] = []
        for variant in variant_settings:
            variant_rel = OUTPUT_IMG_REL_DIR / f"{source_slug}-{variant['id']}.{image_format}"
            variant_abs = repo_root / variant_rel
            planned_outputs.append(variant_rel.as_posix())
            if write:
                should_write_variant = not (missing_only and variant_abs.exists())
                if should_write_variant:
                    run_ffmpeg(
                        ffmpeg_thumb_command(
                            source,
                            variant_abs,
                            codec=codec,
                            preset=preset,
                            quality=int(variant["quality"]),
                            compression_level=compression_level,
                            size=int(variant["size"]),
                        )
                    )
                if not variant_abs.exists():
                    raise RuntimeError(f"missing preview output: {variant_rel.as_posix()}")
                variants.append(
                    output_record(
                        variant_abs,
                        variant_rel,
                        variant_id=str(variant["id"]),
                        label=str(variant["label"]),
                        settings=variant["settings"],
                    )
                )
            else:
                variants.append(
                    {
                        "variant_id": str(variant["id"]),
                        "label": str(variant["label"]),
                        "path": variant_rel.as_posix(),
                        "settings": variant["settings"],
                    }
                )
        if write and not baseline_abs.exists():
            raise RuntimeError(f"missing preview output: {baseline_rel.as_posix()}")
        baseline = (
            output_record(baseline_abs, baseline_rel, variant_id="current", label="current", settings=baseline_settings)
            if write
            else {
                "variant_id": "current",
                "label": "current",
                "path": baseline_rel.as_posix(),
                "settings": baseline_settings,
            }
        )
        rows.append(
            {
                "source_name": source.name,
                "source_display": f"$DOTLINEFORM_PROJECTS_BASE_DIR/{SOURCE_SUBDIR}/{source.name}",
                "baseline": baseline,
                "variants": variants,
            }
        )

    payload: Dict[str, Any] = {
        "ok": True,
        "schema": "thumbnail_quality_preview_v1",
        "generated_at_utc": utc_now_iso(),
        "source_dir": f"$DOTLINEFORM_PROJECTS_BASE_DIR/{SOURCE_SUBDIR}",
        "source_count": len(sources),
        "baseline": {
            "label": "current pipeline",
            "settings": baseline_settings,
        },
        "variants": [
            {
                "id": str(variant["id"]),
                "label": str(variant["label"]),
                "settings": variant["settings"],
            }
            for variant in variant_settings
        ],
        "rows": rows,
        "planned_outputs": planned_outputs,
        "data_path": OUTPUT_DATA_REL_PATH.as_posix(),
    }

    if write:
        data_path = repo_root / OUTPUT_DATA_REL_PATH
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Studio thumbnail quality comparison previews.")
    parser.add_argument("--repo-root", default="", help="Repo root. Auto-detected when omitted.")
    parser.add_argument("--write", action="store_true", help="Write preview images and metadata.")
    parser.add_argument("--missing-only", action="store_true", help="With --write, encode only preview image files that do not already exist.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = resolve_repo_root(__file__, args.repo_root or None)
    payload = build_preview(repo_root, write=bool(args.write), missing_only=bool(args.missing_only))
    mode = "wrote" if args.write else "preview"
    print(f"Thumbnail quality {mode}: {payload['source_count']} source images")
    print(f"Source: {payload['source_dir']}")
    print(f"Data: {payload['data_path']}")
    if not args.write:
        for output in payload["planned_outputs"]:
            print(f"DRY-RUN write: {output}")


if __name__ == "__main__":
    main()
